"""Django ADR models."""

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models import F, Q
from django.utils.translation import gettext_lazy as _

from django_adr.utils import render_markdown

_SUPERSEDED = "superseded"


class ADR(models.Model):
    """An Architectural Decision Record."""

    class Status(models.TextChoices):
        """ADR lifecycle statuses."""

        PROPOSED = "proposed", _("Proposed")
        ACCEPTED = "accepted", _("Accepted")
        DEPRECATED = "deprecated", _("Deprecated")
        SUPERSEDED = _SUPERSEDED, _("Superseded")
        REJECTED = "rejected", _("Rejected")

    number = models.BigAutoField(_("number"), primary_key=True)
    title = models.CharField(_("title"), max_length=200)
    status = models.CharField(
        _("status"),
        max_length=20,
        choices=Status.choices,
        default=Status.PROPOSED,
    )
    date = models.DateField(_("date"), auto_now_add=True)
    context = models.TextField(_("context"), blank=True)
    decision = models.TextField(_("decision"), blank=True)
    consequences = models.TextField(_("consequences"), blank=True)
    superseded_by = models.ForeignKey(
        "self",
        verbose_name=_("superseded by"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="supersedes",
    )

    class Meta:
        """Model options."""

        verbose_name = _("ADR")
        verbose_name_plural = _("ADRs")
        ordering = ("number",)
        constraints = (
            models.CheckConstraint(
                condition=(
                    Q(status=_SUPERSEDED, superseded_by__isnull=False)
                    | (~Q(status=_SUPERSEDED) & Q(superseded_by__isnull=True))
                ),
                name="adr_superseded_iff_superseded_by",
            ),
            models.CheckConstraint(
                condition=~Q(superseded_by=F("number")),
                name="adr_not_self_superseded",
            ),
        )

    def __str__(self) -> str:
        """Return string representation."""
        return f"ADR-{self.number:04d}: {self.title}"

    def clean(self) -> None:
        """Validate status and superseded_by consistency."""
        if self.status == self.Status.SUPERSEDED and not self.superseded_by_id:
            raise ValidationError(
                {"status": _("A superseded ADR must reference the superseding ADR.")}
            )
        if self.superseded_by_id and self.status != self.Status.SUPERSEDED:
            raise ValidationError(
                {"superseded_by": _("Setting a superseding ADR requires status 'Superseded'.")}
            )
        if self.superseded_by_id and self.superseded_by_id == self.pk:
            raise ValidationError({"superseded_by": _("An ADR cannot supersede itself.")})

    def supersede_with(self, replacement: "ADR") -> None:
        """
        Mark this ADR as superseded by ``replacement``.

        Both halves of the invariant are written in a single transaction, so the
        row is never visible in the state the check constraint forbids.
        """
        if self.pk is not None and self.pk == replacement.pk:
            raise ValidationError(_("An ADR cannot supersede itself."))
        if self.status == self.Status.SUPERSEDED:
            raise ValidationError(_("This ADR is already superseded."))
        with transaction.atomic():
            self.superseded_by = replacement
            self.status = self.Status.SUPERSEDED
            self.save(update_fields=("superseded_by", "status"))

    def supersession_chain(self) -> list["ADR"]:
        """
        Return the lineage this ADR belongs to, oldest decision first.

        Where several ADRs were superseded by the same record, the lowest-numbered
        one is followed. The walk is guarded against cycles, which the check
        constraints narrow but do not rule out beyond self-reference.
        """
        seen = {self.pk}
        earlier: list[ADR] = []
        current = self
        while (previous := current.supersedes.first()) is not None and previous.pk not in seen:
            seen.add(previous.pk)
            earlier.append(previous)
            current = previous
        later: list[ADR] = []
        current = self
        while (following := current.superseded_by) is not None and following.pk not in seen:
            seen.add(following.pk)
            later.append(following)
            current = following
        return [*reversed(earlier), self, *later]

    @property
    def context_html(self) -> str:
        """Return context rendered as HTML."""
        return render_markdown(self.context)

    @property
    def decision_html(self) -> str:
        """Return decision rendered as HTML."""
        return render_markdown(self.decision)

    @property
    def consequences_html(self) -> str:
        """Return consequences rendered as HTML."""
        return render_markdown(self.consequences)
