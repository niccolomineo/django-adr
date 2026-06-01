"""DRF ViewSets for ADRs."""

from django.db.models import QuerySet
from rest_framework.decorators import action
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from django_adr.models import ADR
from django_adr.serializers import ADRSerializer


class ADRViewSet(ReadOnlyModelViewSet):
    """Provide read-only API access to ADRs."""

    queryset = ADR.objects.select_related("superseded_by").all()
    serializer_class = ADRSerializer
    lookup_field = "number"

    def get_queryset(self) -> QuerySet[ADR]:
        """Return ADRs optionally filtered by status."""
        queryset = super().get_queryset()
        status = self.request.query_params.get("status")
        if status:
            queryset = queryset.filter(status=status)
        return queryset

    @action(detail=True)
    def chain(self, request: Request, number: int | None = None) -> Response:
        """Return the supersession lineage of this ADR, oldest decision first."""
        chain = self.get_object().supersession_chain()
        return Response(self.get_serializer(chain, many=True).data)
