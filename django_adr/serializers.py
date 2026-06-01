"""DRF serializers for ADRs."""

from rest_framework import serializers

from django_adr.models import ADR


class ADRSerializer(serializers.ModelSerializer):
    """Serialize ADR instances."""

    context_html = serializers.ReadOnlyField()
    decision_html = serializers.ReadOnlyField()
    consequences_html = serializers.ReadOnlyField()
    superseded_by = serializers.SlugRelatedField(
        slug_field="number",
        read_only=True,
        allow_null=True,
    )

    class Meta:
        """Serializer metadata."""

        model = ADR
        fields = (
            "number",
            "title",
            "status",
            "date",
            "context",
            "context_html",
            "decision",
            "decision_html",
            "consequences",
            "consequences_html",
            "superseded_by",
        )
        read_only_fields = ("number", "date")
