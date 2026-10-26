import uuid
import django.db.models.deletion
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = [("orders", "0001_initial")]
    operations = [
        migrations.CreateModel(name="Payment", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("reference", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
            ("provider", models.CharField(choices=[("stripe", "Stripe"), ("simulated", "Simulated")], max_length=16)),
            ("status", models.CharField(choices=[("created", "Created"), ("processing", "Processing"), ("pending", "Pending"), ("succeeded", "Succeeded"), ("failed", "Failed"), ("refunded", "Refunded")], default="created", max_length=16)),
            ("amount_cents", models.PositiveIntegerField()), ("currency", models.CharField(default="EUR", max_length=3)), ("provider_session_id", models.CharField(blank=True, max_length=255)), ("provider_payment_id", models.CharField(blank=True, max_length=255)),
            ("idempotency_key", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)), ("failure_reason", models.CharField(blank=True, max_length=255)), ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("order", models.OneToOneField(on_delete=django.db.models.deletion.PROTECT, related_name="payment", to="orders.order")),
        ]),
        migrations.CreateModel(name="ProviderEvent", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("provider", models.CharField(max_length=16)), ("external_event_id", models.CharField(max_length=255)), ("event_type", models.CharField(max_length=120)), ("payload", models.JSONField()), ("received_at", models.DateTimeField(auto_now_add=True)), ("processed_at", models.DateTimeField(blank=True, null=True))]),
        migrations.CreateModel(name="PaymentEvent", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("event_type", models.CharField(max_length=80)), ("detail", models.CharField(blank=True, max_length=255)), ("created_at", models.DateTimeField(auto_now_add=True)), ("payment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="events", to="payments.payment"))], options={"ordering": ["created_at"]}),
        migrations.CreateModel(name="Refund", fields=[("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")), ("amount_cents", models.PositiveIntegerField()), ("provider_refund_id", models.CharField(blank=True, max_length=255)), ("status", models.CharField(choices=[("pending", "Pending"), ("succeeded", "Succeeded"), ("failed", "Failed")], default="pending", max_length=16)), ("reason", models.CharField(blank=True, max_length=255)), ("created_at", models.DateTimeField(auto_now_add=True)), ("payment", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="refunds", to="payments.payment"))]),
        migrations.AddConstraint(model_name="providerevent", constraint=models.UniqueConstraint(fields=("provider", "external_event_id"), name="unique_provider_event")),
    ]
