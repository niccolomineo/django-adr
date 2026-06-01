"""Django admin configuration for ADRs."""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from django_adr.models import ADR


@admin.register(ADR)
class ADRAdmin(admin.ModelAdmin):
    """Admin interface for ADR."""

    list_display = ("number", "title", "status", "date")
    list_filter = ("status",)
    search_fields = ("title", "context", "decision", "consequences")
    readonly_fields = ("number", "date")
    fieldsets = (
        (None, {"fields": ("number", "title", "status", "date", "superseded_by")}),
        (_("Context"), {"fields": ("context",)}),
        (_("Decision"), {"fields": ("decision",)}),
        (_("Consequences"), {"fields": ("consequences",)}),
    )
