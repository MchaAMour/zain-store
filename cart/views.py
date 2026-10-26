from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from catalog.models import Product
from .cart import Cart

def detail(request):
    cart = Cart(request)
    return render(request, "cart/detail.html", {"items": cart.items(), "total_cents": cart.total_cents()})

@require_POST
def add(request, product_id):
    product = get_object_or_404(Product, id=product_id, active=True)
    Cart(request).add(product)
    messages.success(request, f"{product.name} added to cart.")
    return redirect(request.POST.get("next") or "cart:detail")

@require_POST
def remove(request, product_id):
    Cart(request).remove(product_id)
    return redirect("cart:detail")
