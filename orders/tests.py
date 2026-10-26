from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.contrib.sessions.middleware import SessionMiddleware
from catalog.models import Product
from cart.cart import Cart
from .services import create_order_from_cart
from .models import Order

class OrderCreationTests(TestCase):
    def test_order_keeps_a_price_snapshot(self):
        user = get_user_model().objects.create_user("customer", password="safe-pass-123")
        product = Product.objects.create(name="Keyboard", slug="keyboard", description="Demo", price_cents=12990)
        request = RequestFactory().get("/")
        middleware = SessionMiddleware(lambda request: None)
        middleware.process_request(request); request.session.save()
        cart = Cart(request); cart.add(product)
        order = create_order_from_cart(user, cart)
        product.price_cents = 999; product.save()
        self.assertEqual(order.total_cents, 12990)
        self.assertEqual(order.items.get().unit_price_cents, 12990)

    def test_a_pending_order_can_be_reused_for_a_duplicate_checkout_submit(self):
        user = get_user_model().objects.create_user("customer", password="safe-pass-123")
        product = Product.objects.create(name="Keyboard", slug="keyboard", description="Demo", price_cents=12990)
        self.client.force_login(user)
        session = self.client.session
        session["zain_store_cart"] = {str(product.id): 1}
        session.save()
        first = self.client.post("/orders/create/")
        second = self.client.post("/orders/create/")
        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 302)
        self.assertEqual(Order.objects.filter(customer=user).count(), 1)
