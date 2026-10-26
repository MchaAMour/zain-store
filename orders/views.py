from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from cart.cart import Cart
from .models import Order
from .services import create_order_from_cart

@login_required
def history(request):
    return render(request, "orders/history.html", {"orders": request.user.orders.prefetch_related("items", "payment").all()})

@login_required
@require_POST
def create(request):
    cart = Cart(request)
    pending_reference = request.session.get("pending_checkout_order")
    if pending_reference:
        existing = Order.objects.filter(reference=pending_reference, customer=request.user, status=Order.Status.PENDING_PAYMENT).first()
        if existing:
            return redirect("payments:start", reference=existing.reference)
        request.session.pop("pending_checkout_order", None)
    try: order = create_order_from_cart(request.user, cart)
    except ValueError as error:
        messages.error(request, str(error)); return redirect("cart:detail")
    request.session["pending_checkout_order"] = str(order.reference)
    request.session.modified = True
    cart.clear()
    return redirect("payments:start", reference=order.reference)

@login_required
def detail(request, reference):
    order = get_object_or_404(Order.objects.prefetch_related("items", "payment__events"), reference=reference, customer=request.user)
    return render(request, "orders/detail.html", {"order": order})
