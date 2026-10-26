from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "price_cents", "active")
    list_filter = ("active",)
    prepopulated_fields = {"slug": ("name",)}
