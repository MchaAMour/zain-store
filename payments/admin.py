from django.contrib import admin
from django.contrib import messages
from .models import Payment, PaymentEvent, ProviderEvent, Refund
from .services import record_refund
class PaymentEventInline(admin.TabularInline): model = PaymentEvent; extra = 0; readonly_fields = ("event_type", "detail", "created_at")
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("reference", "order", "provider", "status", "amount_cents", "currency", "updated_at")
    list_filter = ("provider", "status"); search_fields = ("reference", "order__reference", "provider_session_id"); readonly_fields = ("reference", "idempotency_key", "provider_session_id", "provider_payment_id", "created_at", "updated_at"); inlines = [PaymentEventInline]
    actions = ("issue_demo_refund",)
    @admin.action(description="Issue a test refund")
    def issue_demo_refund(self, request, queryset):
        issued = 0
        for payment in queryset:
            try:
                record_refund(payment); issued += 1
            except ValueError as error:
                self.message_user(request, f"{payment}: {error}", level=messages.WARNING)
        if issued: self.message_user(request, f"Issued {issued} demo refund(s).", level=messages.SUCCESS)
@admin.register(ProviderEvent)
class ProviderEventAdmin(admin.ModelAdmin): list_display = ("provider", "external_event_id", "event_type", "received_at", "processed_at"); readonly_fields = ("provider", "external_event_id", "event_type", "payload", "received_at", "processed_at")
@admin.register(Refund)
class RefundAdmin(admin.ModelAdmin): list_display = ("payment", "amount_cents", "status", "created_at")
