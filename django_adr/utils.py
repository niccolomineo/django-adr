"""Markdown rendering utilities."""

import mistune

_markdown = mistune.create_markdown(escape=False)


def render_markdown(text: str) -> str:
    """Return HTML rendered from the given Markdown text."""
    return _markdown(text)
