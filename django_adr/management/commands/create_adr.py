"""Management command to create a new ADR."""

from typing import Any

from django.core.management.base import BaseCommand, CommandError, CommandParser
from django.db import transaction

from django_adr.models import ADR


class Command(BaseCommand):
    """Create a new Architectural Decision Record."""

    help = "Create a new Architectural Decision Record."

    def add_arguments(self, parser: CommandParser) -> None:
        """Add command-line arguments."""
        parser.add_argument("title", type=str, help="The ADR title.")
        parser.add_argument(
            "--status",
            type=str,
            default=ADR.Status.PROPOSED,
            choices=[s.value for s in ADR.Status],
            help="The initial status (default: proposed).",
        )
        parser.add_argument(
            "--context",
            type=str,
            default="",
            help="The architectural context (Markdown).",
        )
        parser.add_argument(
            "--decision",
            type=str,
            default="",
            help="The decision made (Markdown).",
        )
        parser.add_argument(
            "--consequences",
            type=str,
            default="",
            help="The consequences of the decision (Markdown).",
        )
        parser.add_argument(
            "--supersedes",
            type=int,
            default=None,
            help="Number of the ADR this new ADR supersedes.",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        """Create and save the ADR."""
        if options["supersedes"] is not None:
            try:
                old = ADR.objects.get(number=options["supersedes"])
            except ADR.DoesNotExist as exc:
                raise CommandError(f"ADR-{options['supersedes']:04d} does not exist.") from exc
        else:
            old = None
        with transaction.atomic():
            adr = ADR.objects.create(
                title=options["title"],
                status=options["status"],
                context=options["context"],
                decision=options["decision"],
                consequences=options["consequences"],
            )
            self.stdout.write(self.style.SUCCESS(f"Created {adr}"))
            if old is not None:
                old.superseded_by = adr
                old.status = ADR.Status.SUPERSEDED
                old.save()
                self.stdout.write(self.style.WARNING(f"Marked {old} as superseded."))
