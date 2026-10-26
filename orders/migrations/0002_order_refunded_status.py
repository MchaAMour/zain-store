from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [("orders", "0001_initial")]
    operations = [migrations.AlterField(
        model_name="order",
        name="status",
        field=models.CharField(choices=[("pending_payment", "Pending payment"), ("paid", "Paid"), ("refunded", "Refunded")], default="pending_payment", max_length=24),
    )]
