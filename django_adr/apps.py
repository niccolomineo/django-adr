"""Django ADR application configuration."""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class DjangoAdrConfig(AppConfig):
    """Django ADR application configuration."""

    name = "django_adr"
    verbose_name = _("Architectural Decision Records")
