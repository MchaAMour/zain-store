from django.urls import path
from . import views
app_name = "payments"
urlpatterns = [
    path("start/<uuid:reference>/", views.start, name="start"), path("simulated/<uuid:reference>/", views.simulated, name="simulated"),
    path("simulated/<uuid:reference>/<str:outcome>/", views.simulated_outcome, name="simulated_outcome"), path("retry/<uuid:reference>/", views.retry, name="retry"),
    path("result/<uuid:reference>/", views.result, name="result"), path("stripe/webhook/", views.stripe_webhook, name="stripe_webhook"),
]
