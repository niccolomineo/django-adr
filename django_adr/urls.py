"""URL configuration for django_adr."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from django_adr.api import ADRViewSet
from django_adr.views import ADRDetailView, ADRListView

_router = DefaultRouter()
_router.register("api/adrs", ADRViewSet, basename="adr-api")

app_name = "django_adr"

urlpatterns = [
    path("", ADRListView.as_view(), name="adr-list"),
    path("<int:number>/", ADRDetailView.as_view(), name="adr-detail"),
    *_router.urls,
]
