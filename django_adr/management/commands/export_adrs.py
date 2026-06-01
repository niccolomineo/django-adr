"""Management command to export ADRs as Markdown files."""

from pathlib import Path
from typing import Any

from django.core.management.base import BaseCommand, CommandParser
from django.utils.text import slugify

from django_adr.models import ADR


class Command(BaseCommand):
    """Export all ADRs as Markdown files."""

    help = "Export all ADRs as Markdown files."

    def add_arguments(self, parser: CommandParser) -> None:
        """Add command-line arguments."""
        parser.add_argument(
            "--output-dir",
            type=str,
            default="docs/adr",
            help="Directory to write Markdown files (default: docs/adr).",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Export each ADR to a Markdown file."""
        output_dir = Path(options["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        count = 0
        for adr in ADR.objects.select_related("superseded_by").all():
            path = output_dir / f"{adr.number:04d}-{slugify(adr.title)}.md"
            path.write_text(self._render(adr), encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Exported {adr} → {path}"))
            count += 1
        self.stdout.write(f"Exported {count} ADR(s) to {output_dir}.")

    def _render(self, adr: ADR) -> str:
        """Render an ADR as a Markdown string."""
        lines = [
            f"# {adr}",
            "",
            f"**Status:** {adr.get_status_display()}  ",
            f"**Date:** {adr.date}",
        ]
        if adr.superseded_by:
            lines.append(f"**Superseded by:** {adr.superseded_by}")
        lines += [
            "",
            "## Context",
            "",
            adr.context,
            "",
            "## Decision",
            "",
            adr.decision,
            "",
            "## Consequences",
            "",
            adr.consequences,
            "",
        ]
        return "\n".join(lines)
