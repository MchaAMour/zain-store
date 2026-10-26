import stripe
from django.conf import settings
class StripeProvider:
    name = "stripe"
    def create_checkout(self, payment, success_url, cancel_url):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        session = stripe.checkout.Session.create(
            mode="payment",
            success_url=f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=cancel_url,
            client_reference_id=str(payment.reference),
            metadata={"payment_reference": str(payment.reference)},
            payment_intent_data={"metadata": {"payment_reference": str(payment.reference)}},
            line_items=[{"price_data": {"currency": payment.currency.lower(), "product_data": {"name": f"Zain Store order {payment.order.reference}"}, "unit_amount": payment.amount_cents}, "quantity": 1}],
            idempotency_key=str(payment.idempotency_key),
        )
        return {"session_id": session.id, "url": session.url}
