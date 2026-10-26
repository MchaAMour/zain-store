from django.db import migrations, models

class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [migrations.CreateModel(name="Product", fields=[
        ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
        ("name", models.CharField(max_length=120)), ("slug", models.SlugField(unique=True)),
        ("description", models.TextField()), ("price_cents", models.PositiveIntegerField()),
        ("active", models.BooleanField(default=True)), ("image_url", models.URLField(blank=True)),
    ], options={"ordering": ["name"]})]
