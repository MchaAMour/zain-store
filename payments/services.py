import uuid
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from orders.models import Order
from .models import Payment, PaymentEvent, ProviderEvent, Refund

ALLOWED_TRANSITIONS = {
    Payment.Status.CREATED: {Payment.Status.PROCESSING},
    Payment.Status.PROCESSING: {Payment.Status.PENDING, Payment.Status.SUCCEEDED, Payment.Status.FAILED},
    Payment.Status.PENDING: {Payment.Status.PROCESSING, Payment.Status.SUCCEEDED, Payment.Status.FAILED},
    Payment.Status.FAILED: {Payment.Status.PROCESSING},
    Payment.Status.SUCCEEDED: {Payment.Status.REFUNDED},
    Payment.Status.REFUNDED: set(),
}

def payment_provider():
    from django.conf import settings
    return Payment.Provider.STRIPE if settings.STRIPE_SECRET_KEY else Payment.Provider.SIMULATED

@transaction.atomic
def get_or_create_payment(order):
    payment, created = Payment.objects.select_for_update().get_or_create(order=order, defaults={"provider": payment_provider(), "amount_cents": order.total_cents, "currency": order.currency})
    if created: PaymentEvent.objects.create(payment=payment, event_type="payment_created", detail="Durable payment record created")
    return payment

@transaction.atomic
def transition(payment, status, detail=""):
    payment = Payment.objects.select_for_update().select_related("order").get(pk=payment.pk)
    if payment.status in [Payment.Status.SUCCEEDED, Payment.Status.REFUNDED] and status != Payment.Status.REFUNDED:
        PaymentEvent.objects.create(payment=payment, event_type="payment_transition_ignored", detail=f"Ignored {status}: terminal state is {payment.status}")
        return payment
    if payment.status == status: return payment
    if status not in ALLOWED_TRANSITIONS[payment.status]:
        PaymentEvent.objects.create(payment=payment, event_type="payment_transition_ignored", detail=f"Ignored invalid transition {payment.status} → {status}")
        return payment
    payment.status = status
    if status == Payment.Status.FAILED: payment.failure_reason = detail
    payment.save(update_fields=["status", "failure_reason", "updated_at"])
    PaymentEvent.objects.create(payment=payment, event_type=f"payment_{status}", detail=detail)
    if status == Payment.Status.SUCCEEDED and payment.order.status != Order.Status.PAID:
        payment.order.status = Order.Status.PAID; payment.order.save(update_fields=["status", "updated_at"])
    elif status == Payment.Status.REFUNDED and payment.order.status != Order.Status.REFUNDED:
        payment.order.status = Order.Status.REFUNDED; payment.order.save(update_fields=["status", "updated_at"])
    return payment

@transaction.atomic
def record_checkout_session(payment, provider_session_id):
    """Persist a hosted/simulated checkout session before exposing its URL."""
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    payment.provider_session_id = provider_session_id
    payment.save(update_fields=["provider_session_id", "updated_at"])
    PaymentEvent.objects.create(payment=payment, event_type="checkout_session_created", detail=f"{payment.provider} checkout session created")
    return transition(payment, Payment.Status.PROCESSING, "Awaiting provider outcome")

@transaction.atomic
def ingest_provider_event(provider, external_id, event_type, payload, payment, outcome):
    event, created = ProviderEvent.objects.get_or_create(provider=provider, external_event_id=external_id, defaults={"event_type": event_type, "payload": payload})
    if not created: return False
    transition(payment, outcome, f"Provider event: {event_type}")
    event.processed_at = timezone.now(); event.save(update_fields=["processed_at"])
    return True

@transaction.atomic
def record_refund(payment, reason="Admin test/demo refund"):
    payment = Payment.objects.select_for_update().get(pk=payment.pk)
    if payment.status != Payment.Status.SUCCEEDED:
        raise ValueError("Only successful payments can be refunded.")
    refund, created = Refund.objects.get_or_create(payment=payment, defaults={"amount_cents": payment.amount_cents, "reason": reason})
    if not created:
        return refund
    if payment.provider == Payment.Provider.SIMULATED:
        refund.provider_refund_id = f"demo-refund-{payment.reference}"
        refund.status = Refund.Status.SUCCEEDED
        refund.save(update_fields=["provider_refund_id", "status"])
        transition(payment, Payment.Status.REFUNDED, reason)
        return refund
    try:
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
        provider_refund = stripe.Refund.create(
            payment_intent=payment.provider_payment_id,
            amount=payment.amount_cents,
            reason="requested_by_customer",
            idempotency_key=f"refund-{payment.idempotency_key}",
        )
        refund.provider_refund_id = provider_refund.id
        refund.status = Refund.Status.SUCCEEDED if provider_refund.status == "succeeded" else Refund.Status.PENDING
        refund.save(update_fields=["provider_refund_id", "status"])
        if refund.status == Refund.Status.SUCCEEDED:
            transition(payment, Payment.Status.REFUNDED, reason)
    except stripe.StripeError as error:
        refund.status = Refund.Status.FAILED
        refund.reason = str(error.user_message or "Stripe refund failed")
        refund.save(update_fields=["status", "reason"])
        PaymentEvent.objects.create(payment=payment, event_type="refund_failed", detail=refund.reason)
    return refund
