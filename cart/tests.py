from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from catalog.models import Product
from .cart import Cart

class CartTests(TestCase):
    def setUp(self):
        self.product = Product.objects.create(name="Keyboard", slug="keyboard", description="Demo", price_cents=12990)
        self.factory = RequestFactory()

    def test_total_is_calculated_from_database_price(self):
        request = self.factory.get("/")
        from django.contrib.sessions.middleware import SessionMiddleware
        middleware = SessionMiddleware(lambda request: None)
        middleware.process_request(request)
        request.session.save()
        cart = Cart(request)
        cart.add(self.product, quantity=2)
        self.assertEqual(cart.total_cents(), 25980)
