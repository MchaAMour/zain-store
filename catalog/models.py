from django.db import models
from django.urls import reverse

class Product(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    description = models.TextField()
    price_cents = models.PositiveIntegerField()
    active = models.BooleanField(default=True)
    image_url = models.URLField(blank=True)

    class Meta:
        ordering = ["name"]

    @property
    def price_eur(self):
        return self.price_cents / 100

    def get_absolute_url(self):
        return reverse("catalog:product_detail", args=[self.slug])

    def __str__(self):
        return self.name
