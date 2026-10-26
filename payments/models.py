import uuid
from django.db import models
from orders.models import Order

class Payment(models.Model):
    class Provider(models.TextChoices): STRIPE = "stripe", "Stripe"; SIMULATED = "simulated", "Simulated"
    class Status(models.TextChoices): CREATED = "created", "Created"; PROCESSING = "processing", "Processing"; PENDING = "pending", "Pending"; SUCCEEDED = "succeeded", "Succeeded"; FAILED = "failed", "Failed"; REFUNDED = "refunded", "Refunded"
    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name="payment")
    provider = models.CharField(max_length=16, choices=Provider.choices)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.CREATED)
    amount_cents = models.PositiveIntegerField()
    currency = models.CharField(max_length=3, default="EUR")
    provider_session_id = models.CharField(max_length=255, blank=True)
    provider_payment_id = models.CharField(max_length=255, blank=True)
    idempotency_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    failure_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True); updated_at = models.DateTimeField(auto_now=True)
    def __str__(self): return f"Payment {str(self.reference)[:8]} ({self.status})"

class ProviderEvent(models.Model):
    provider = models.CharField(max_length=16)
    external_event_id = models.CharField(max_length=255)
    event_type = models.CharField(max_length=120)
    payload = models.JSONField()
    received_at = models.DateTimeField(auto_now_add=True); processed_at = models.DateTimeField(null=True, blank=True)
    class Meta: constraints = [models.UniqueConstraint(fields=["provider", "external_event_id"], name="unique_provider_event")]

class PaymentEvent(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="events")
    event_type = models.CharField(max_length=80); detail = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta: ordering = ["created_at"]

class Refund(models.Model):
    class Status(models.TextChoices): PENDING = "pending", "Pending"; SUCCEEDED = "succeeded", "Succeeded"; FAILED = "failed", "Failed"
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, related_name="refunds")
    amount_cents = models.PositiveIntegerField(); provider_refund_id = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    reason = models.CharField(max_length=255, blank=True); created_at = models.DateTimeField(auto_now_add=True)
