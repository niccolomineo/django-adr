"""HTML views for ADRs."""

from typing import Any

from django.db.models import QuerySet
from django.shortcuts import get_object_or_404
from django.views.generic import DetailView, ListView

from django_adr.models import ADR


class ADRListView(ListView):
    """Display a list of all ADRs."""

    model = ADR
    template_name = "django_adr/adr_list.html"
    context_object_name = "adrs"

    def get_queryset(self) -> QuerySet[ADR]:
        """Return ADRs optionally filtered by status."""
        qs = super().get_queryset()
        status = self.request.GET.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add available statuses and current filter to context."""
        context = super().get_context_data(**kwargs)
        context["statuses"] = ADR.Status.choices
        context["current_status"] = self.request.GET.get("status", "")
        return context


class ADRDetailView(DetailView):
    """Display a single ADR."""

    model = ADR
    template_name = "django_adr/adr_detail.html"
    context_object_name = "adr"

    def get_queryset(self) -> QuerySet[ADR]:
        """Return ADRs with superseded_by preloaded."""
        return super().get_queryset().select_related("superseded_by")

    def get_object(self, queryset: QuerySet[ADR] | None = None) -> ADR:
        """Return the ADR identified by the URL number."""
        queryset = queryset or self.get_queryset()
        return get_object_or_404(queryset, number=self.kwargs["number"])
