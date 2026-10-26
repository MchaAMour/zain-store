from django.contrib import admin
from .models import Order, OrderItem
class ItemInline(admin.TabularInline): model = OrderItem; extra = 0; readonly_fields = ("product_name", "unit_price_cents", "quantity", "line_total_cents")
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("reference", "customer", "status", "total_cents", "currency", "created_at")
    list_filter = ("status",); search_fields = ("reference", "customer__username"); inlines = [ItemInline]
