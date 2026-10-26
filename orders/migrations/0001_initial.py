import uuid
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(name="Order", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("reference", models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
            ("status", models.CharField(choices=[("pending_payment", "Pending payment"), ("paid", "Paid")], default="pending_payment", max_length=24)),
            ("currency", models.CharField(default="EUR", max_length=3)), ("total_cents", models.PositiveIntegerField()),
            ("created_at", models.DateTimeField(auto_now_add=True)), ("updated_at", models.DateTimeField(auto_now=True)),
            ("customer", models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name="orders", to=settings.AUTH_USER_MODEL)),
        ], options={"ordering": ["-created_at"]}),
        migrations.CreateModel(name="OrderItem", fields=[
            ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ("product_name", models.CharField(max_length=120)), ("unit_price_cents", models.PositiveIntegerField()),
            ("quantity", models.PositiveIntegerField()), ("line_total_cents", models.PositiveIntegerField()),
            ("order", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="items", to="orders.order")),
        ]),
    ]
