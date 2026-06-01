"""URL configuration for the test suite."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("adrs/", include("django_adr.urls", namespace="django_adr")),
]
