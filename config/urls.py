from django.contrib import admin
from django.urls import include, path
from core import views as core_views

urlpatterns = [
    path("admin/", admin.site.urls), path("", include("catalog.urls")),
    path("health/", core_views.health, name="health"),
    path("accounts/", include("accounts.urls")), path("cart/", include("cart.urls")),
    path("orders/", include("orders.urls")), path("payments/", include("payments.urls")),
]
