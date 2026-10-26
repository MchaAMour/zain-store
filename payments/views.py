import json
import uuid
import stripe
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from orders.models import Order
from .models import Payment
from .providers.simulated import SimulatedProvider
from .providers.stripe import StripeProvider
from .services import get_or_create_payment, ingest_provider_event, record_checkout_session, transition

@login_required
def start(request, reference):
    order = get_object_or_404(Order, reference=reference, customer=request.user)
    payment = get_or_create_payment(order)
    if payment.status == Payment.Status.SUCCEEDED: return redirect("orders:detail", reference=order.reference)
    if payment.provider == Payment.Provider.SIMULATED:
        if not payment.provider_session_id:
            payment = record_checkout_session(payment, SimulatedProvider().create_checkout(payment, "")["session_id"])
        return redirect("payments:simulated", reference=payment.reference)
    try:
        urls = (request.build_absolute_uri(reverse("payments:result", args=[payment.reference])), request.build_absolute_uri(reverse("orders:detail", args=[order.reference])))
        result = StripeProvider().create_checkout(payment, *urls)
        record_checkout_session(payment, result["session_id"])
        return redirect(result["url"])
    except Exception:
        messages.error(request, "Stripe Checkout could not be opened. Use the simulator or check your test key.")
        return redirect("orders:detail", reference=order.reference)

@login_required
def simulated(request, reference):
    payment = get_object_or_404(Payment.objects.select_related("order"), reference=reference, order__customer=request.user)
    return render(request, "payments/simulated.html", {"payment": payment})

@login_required
@require_POST
def simulated_outcome(request, reference, outcome):
    payment = get_object_or_404(Payment.objects.select_related("order"), reference=reference, order__customer=request.user)
    target = {"success": Payment.Status.SUCCEEDED, "fail": Payment.Status.FAILED, "pending": Payment.Status.PENDING}.get(outcome)
    if not target: return HttpResponseBadRequest("Unknown demo outcome")
    ingest_provider_event("simulated", f"{payment.provider_session_id}:{outcome}:{uuid.uuid4()}", f"simulated.{outcome}", {"payment": str(payment.reference), "outcome": outcome}, payment, target)
    return redirect("orders:detail", reference=payment.order.reference)

@login_required
@require_POST
def retry(request, reference):
    payment = get_object_or_404(Payment.objects.select_related("order"), reference=reference, order__customer=request.user)
    if payment.status not in [Payment.Status.FAILED, Payment.Status.PENDING]: return redirect("orders:detail", reference=payment.order.reference)
    payment.provider_session_id = ""; payment.save(update_fields=["provider_session_id", "updated_at"])
    transition(payment, Payment.Status.PROCESSING, "Customer initiated retry")
    return redirect("payments:start", reference=payment.order.reference)

@login_required
def result(request, reference):
    payment = get_object_or_404(Payment.objects.select_related("order"), reference=reference, order__customer=request.user)
    return render(request, "payments/result.html", {"payment": payment})

@csrf_exempt
@require_POST
def stripe_webhook(request):
    if not settings.STRIPE_WEBHOOK_SECRET: return HttpResponseBadRequest("Webhook secret is not configured")
    try:
        event = stripe.Webhook.construct_event(request.body, request.META.get("HTTP_STRIPE_SIGNATURE", ""), settings.STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError): return HttpResponseBadRequest("Invalid Stripe signature")
    data = event.data.object
    reference = data.get("metadata", {}).get("payment_reference") or data.get("client_reference_id")
    if not reference: return HttpResponse(status=200)
    try: payment = Payment.objects.get(reference=reference, provider=Payment.Provider.STRIPE)
    except Payment.DoesNotExist: return HttpResponse(status=200)
    payment_intent = data.get("payment_intent")
    if payment_intent and payment.provider_payment_id != payment_intent:
        payment.provider_payment_id = payment_intent
        payment.save(update_fields=["provider_payment_id", "updated_at"])
    outcomes = {"checkout.session.completed": Payment.Status.SUCCEEDED, "checkout.session.async_payment_succeeded": Payment.Status.SUCCEEDED, "checkout.session.async_payment_failed": Payment.Status.FAILED, "checkout.session.expired": Payment.Status.FAILED}
    if event.type in outcomes: ingest_provider_event("stripe", event.id, event.type, event.to_dict_recursive(), payment, outcomes[event.type])
    return HttpResponse(status=200)
