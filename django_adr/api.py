"""DRF ViewSets for ADRs."""

from rest_framework.viewsets import ReadOnlyModelViewSet

from django_adr.models import ADR
from django_adr.serializers import ADRSerializer


class ADRViewSet(ReadOnlyModelViewSet):
    """Provide read-only API access to ADRs."""

    queryset = ADR.objects.select_related("superseded_by").all()
    serializer_class = ADRSerializer
    lookup_field = "number"
