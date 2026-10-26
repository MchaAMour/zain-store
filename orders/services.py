from django.db import transaction
from .models import Order, OrderItem

@transaction.atomic
def create_order_from_cart(user, cart):
    items = cart.items()
    if not items: raise ValueError("Your cart is empty.")
    total_cents = sum(item["line_total_cents"] for item in items)
    order = Order.objects.create(customer=user, total_cents=total_cents)
    OrderItem.objects.bulk_create([OrderItem(order=order, product_name=i["product"].name, unit_price_cents=i["product"].price_cents, quantity=i["quantity"], line_total_cents=i["line_total_cents"]) for i in items])
    return order
