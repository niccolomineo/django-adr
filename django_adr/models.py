"""Django ADR models."""

from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.utils.translation import gettext_lazy as _

from django_adr.utils import render_markdown


class ADR(models.Model):
    """An Architectural Decision Record."""

    class Status(models.TextChoices):
        """ADR lifecycle statuses."""

        PROPOSED = "proposed", _("Proposed")
        ACCEPTED = "accepted", _("Accepted")
        DEPRECATED = "deprecated", _("Deprecated")
        SUPERSEDED = "superseded", _("Superseded")
        REJECTED = "rejected", _("Rejected")

    number = models.PositiveIntegerField(_("number"), unique=True, editable=False)
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

    def __str__(self) -> str:
        """Return string representation."""
        return f"ADR-{self.number:04d}: {self.title}"

    def save(self, *args, **kwargs) -> None:
        """Save the ADR, auto-assigning number if not set."""
        if not self.number:
            with transaction.atomic():
                last = ADR.objects.select_for_update().order_by("-number").first()
                self.number = (last.number + 1) if last else 1
                super().save(*args, **kwargs)
        else:
            super().save(*args, **kwargs)

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
