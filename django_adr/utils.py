"""Markdown rendering utilities."""

from functools import cache
from typing import Any, cast

import mistune
from django.conf import settings
from django.core.signals import setting_changed
from django.dispatch import receiver

MARKDOWN_ESCAPE_SETTING = "DJANGO_ADR_MARKDOWN_ESCAPE"


@cache
def _markdown() -> mistune.Markdown:
    """
    Return the shared Markdown renderer.

    Built on first use rather than at import time, so Django settings are loaded
    by the time the setting is read.
    """
    escape = getattr(settings, MARKDOWN_ESCAPE_SETTING, True)
    return mistune.create_markdown(escape=escape)


@receiver(setting_changed)
def _reset_markdown(**kwargs: Any) -> None:
    """Discard the cached renderer so ``override_settings`` takes effect."""
    if kwargs["setting"] == MARKDOWN_ESCAPE_SETTING:
        _markdown.cache_clear()


def render_markdown(text: str) -> str:
    """Return HTML rendered from the given Markdown text."""
    return cast(str, _markdown()(text))
