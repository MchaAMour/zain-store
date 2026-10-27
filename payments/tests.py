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

@override_settings(STRIPE_SECRET_KEY="sk_test_x", STRIPE_WEBHOOK_SECRET="whsec_test")
class StripeWebhookTests(TestCase):
    """Payloads are signed with Stripe's real scheme and go through the real construct_event."""
    def setUp(self):
        user = get_user_model().objects.create_user("zain", password="safe-pass-123")
        order = Order.objects.create(customer=user, total_cents=7990)
        self.payment = get_or_create_payment(order)
        record_checkout_session(self.payment, "cs_test_1")

    def post_event(self, event_type, obj, event_id="evt_1"):
        import hashlib, hmac, json, time
        body = json.dumps({"id": event_id, "object": "event", "type": event_type, "data": {"object": obj}})
        ts = int(time.time())
        sig = hmac.new(b"whsec_test", f"{ts}.{body}".encode(), hashlib.sha256).hexdigest()
        return self.client.post("/payments/stripe/webhook/", body, content_type="application/json", HTTP_STRIPE_SIGNATURE=f"t={ts},v1={sig}")

    def test_completed_session_marks_payment_succeeded(self):
        session = {"id": "cs_test_1", "object": "checkout.session", "metadata": {"payment_reference": str(self.payment.reference)}, "payment_intent": "pi_1"}
        self.assertEqual(self.post_event("checkout.session.completed", session).status_code, 200)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.SUCCEEDED)
        self.assertEqual(self.payment.provider_payment_id, "pi_1")
        self.assertEqual(self.post_event("checkout.session.completed", session).status_code, 200)  # replay is harmless
        self.assertEqual(ProviderEvent.objects.count(), 1)

    def test_null_metadata_falls_back_to_client_reference_id(self):
        session = {"id": "cs_test_1", "object": "checkout.session", "metadata": None, "client_reference_id": str(self.payment.reference)}
        self.assertEqual(self.post_event("checkout.session.completed", session).status_code, 200)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.status, Payment.Status.SUCCEEDED)

    def test_bad_signature_is_rejected(self):
        r = self.client.post("/payments/stripe/webhook/", "{}", content_type="application/json", HTTP_STRIPE_SIGNATURE="t=1,v1=bad")
        self.assertEqual(r.status_code, 400)
