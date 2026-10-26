from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from orders.models import Order, OrderItem
from .models import Payment, ProviderEvent
from .services import get_or_create_payment, ingest_provider_event, record_checkout_session, record_refund, transition

@override_settings(STRIPE_SECRET_KEY="")
class PaymentWorkflowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user("zain", password="safe-pass-123")
        self.order = Order.objects.create(customer=self.user, total_cents=12990)
        OrderItem.objects.create(order=self.order, product_name="Keyboard", unit_price_cents=12990, quantity=1, line_total_cents=12990)

    def test_payment_is_created_once_for_an_order(self):
        first = get_or_create_payment(self.order)
        second = get_or_create_payment(self.order)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(Payment.objects.count(), 1)

    def test_duplicate_provider_event_is_harmless(self):
        payment = get_or_create_payment(self.order)
        record_checkout_session(payment, "simulated-session")
        self.assertTrue(ingest_provider_event("simulated", "event-1", "simulated.success", {}, payment, Payment.Status.SUCCEEDED))
        self.assertFalse(ingest_provider_event("simulated", "event-1", "simulated.success", {}, payment, Payment.Status.SUCCEEDED))
        self.order.refresh_from_db(); payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.SUCCEEDED)
        self.assertEqual(self.order.status, Order.Status.PAID)
        self.assertEqual(ProviderEvent.objects.count(), 1)

    def test_late_failure_does_not_overwrite_success(self):
        payment = get_or_create_payment(self.order)
        record_checkout_session(payment, "simulated-session")
        ingest_provider_event("simulated", "event-success", "simulated.success", {}, payment, Payment.Status.SUCCEEDED)
        ingest_provider_event("simulated", "event-failure", "simulated.failure", {}, payment, Payment.Status.FAILED)
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.SUCCEEDED)

    def test_invalid_transition_is_ignored_and_audited(self):
        payment = get_or_create_payment(self.order)
        transition(payment, Payment.Status.SUCCEEDED, "Attempted before checkout")
        payment.refresh_from_db()
        self.assertEqual(payment.status, Payment.Status.CREATED)
        self.assertTrue(payment.events.filter(event_type="payment_transition_ignored").exists())

    def test_simulated_refund_marks_order_and_payment_refunded(self):
        payment = get_or_create_payment(self.order)
        record_checkout_session(payment, "simulated-session")
        ingest_provider_event("simulated", "event-success", "simulated.success", {}, payment, Payment.Status.SUCCEEDED)
        refund = record_refund(payment)
        payment.refresh_from_db(); self.order.refresh_from_db()
        self.assertEqual(refund.status, "succeeded")
        self.assertEqual(payment.status, Payment.Status.REFUNDED)
        self.assertEqual(self.order.status, Order.Status.REFUNDED)
