"""Management command tests for create_adr."""

import io

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase

from django_adr.models import ADR


class TestCreateADRCommand(TestCase):
    """Test the create_adr management command."""

    def test_command_creates_adr_with_given_title(self) -> None:
        """Test that the command creates an ADR with the given title."""
        call_command("create_adr", "My New Decision")
        self.assertTrue(ADR.objects.filter(title="My New Decision").exists())

    def test_created_adr_defaults_to_proposed_status(self) -> None:
        """Test that an ADR created via command defaults to PROPOSED status."""
        call_command("create_adr", "Status Test")
        adr = ADR.objects.get(title="Status Test")
        self.assertEqual(adr.status, ADR.Status.PROPOSED)

    def test_command_accepts_custom_status(self) -> None:
        """Test that the command creates an ADR with the specified status."""
        call_command("create_adr", "Accepted Decision", "--status=accepted")
        adr = ADR.objects.get(title="Accepted Decision")
        self.assertEqual(adr.status, ADR.Status.ACCEPTED)

    def test_command_stores_context_decision_and_consequences(self) -> None:
        """Test that the command stores the provided context, decision, and consequences."""
        call_command(
            "create_adr",
            "Full ADR",
            "--context=Some context",
            "--decision=The decision",
            "--consequences=Some consequences",
        )
        adr = ADR.objects.get(title="Full ADR")
        self.assertEqual(adr.context, "Some context")
        self.assertEqual(adr.decision, "The decision")
        self.assertEqual(adr.consequences, "Some consequences")

    def test_command_writes_success_message_to_stdout(self) -> None:
        """Test that the command writes a success message to stdout after creation."""
        out = io.StringIO()
        call_command("create_adr", "Output Test", stdout=out)
        self.assertIn("ADR-", out.getvalue())

    def test_command_assigns_sequential_numbers(self) -> None:
        """Test that successive command invocations assign sequential numbers."""
        call_command("create_adr", "First")
        call_command("create_adr", "Second")
        first, second = ADR.objects.order_by("number").values_list("number", flat=True)
        self.assertEqual(second, first + 1)

    def test_command_creates_adr_with_empty_text_fields_by_default(self) -> None:
        """Test that the command creates an ADR with empty text fields when not provided."""
        call_command("create_adr", "Minimal ADR")
        adr = ADR.objects.get(title="Minimal ADR")
        self.assertEqual(adr.context, "")
        self.assertEqual(adr.decision, "")
        self.assertEqual(adr.consequences, "")

    def test_supersedes_marks_old_adr_as_superseded(self) -> None:
        """Test that --supersedes sets the old ADR status to SUPERSEDED."""
        call_command("create_adr", "Old Decision")
        old = ADR.objects.get(title="Old Decision")
        call_command("create_adr", "New Decision", f"--supersedes={old.number}")
        old.refresh_from_db()
        self.assertEqual(old.status, ADR.Status.SUPERSEDED)

    def test_supersedes_sets_superseded_by_to_new_adr(self) -> None:
        """Test that --supersedes sets superseded_by on the old ADR to the new ADR."""
        call_command("create_adr", "Old")
        old = ADR.objects.get(title="Old")
        call_command("create_adr", "New", f"--supersedes={old.number}")
        new = ADR.objects.get(title="New")
        old.refresh_from_db()
        self.assertEqual(old.superseded_by, new)

    def test_supersedes_raises_error_for_unknown_number(self) -> None:
        """Test that --supersedes raises CommandError when the referenced ADR does not exist."""
        with self.assertRaises(CommandError):
            call_command("create_adr", "New", "--supersedes=999")
        self.assertFalse(ADR.objects.filter(title="New").exists())


class TestCreateADRSupersessionGuards(TestCase):
    """Test that create_adr refuses to produce inconsistent supersession states."""

    def test_superseded_status_is_rejected(self) -> None:
        """Test that a new ADR cannot be created already marked as superseded."""
        with self.assertRaises(CommandError):
            call_command("create_adr", "Impossible", "--status=superseded")
        self.assertFalse(ADR.objects.filter(title="Impossible").exists())

    def test_superseded_status_is_rejected_even_with_supersedes(self) -> None:
        """Test that --supersedes does not licence creating a superseded ADR."""
        call_command("create_adr", "Existing")
        existing = ADR.objects.get(title="Existing")
        with self.assertRaises(CommandError):
            call_command(
                "create_adr", "Impossible", "--status=superseded", f"--supersedes={existing.number}"
            )
        self.assertFalse(ADR.objects.filter(title="Impossible").exists())

    def test_superseding_an_already_superseded_adr_is_rejected(self) -> None:
        """Test that an ADR already superseded cannot be superseded a second time."""
        call_command("create_adr", "Old")
        old = ADR.objects.get(title="Old")
        call_command("create_adr", "New", f"--supersedes={old.number}")
        with self.assertRaises(CommandError):
            call_command("create_adr", "Newer", f"--supersedes={old.number}")
        self.assertFalse(ADR.objects.filter(title="Newer").exists())

    def test_supersession_leaves_the_new_adr_proposed(self) -> None:
        """Test that superseding marks only the old ADR, leaving the new one proposed."""
        call_command("create_adr", "Old")
        old = ADR.objects.get(title="Old")
        call_command("create_adr", "New", f"--supersedes={old.number}")
        self.assertEqual(ADR.objects.get(title="New").status, ADR.Status.PROPOSED)
