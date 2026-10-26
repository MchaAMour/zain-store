from django.urls import path
from . import views
app_name = "orders"
urlpatterns = [path("", views.history, name="history"), path("create/", views.create, name="create"), path("<uuid:reference>/", views.detail, name="detail")]
