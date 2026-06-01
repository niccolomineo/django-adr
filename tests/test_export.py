"""Tests for the export_adrs management command."""

import io
import shutil
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.test import TestCase

from django_adr.models import ADR


class TestExportADRsCommand(TestCase):
    """Test the export_adrs management command."""

    def setUp(self) -> None:
        """Set up a temporary output directory for each test."""
        self.output_dir = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.output_dir)

    def test_export_creates_file_for_each_adr(self) -> None:
        """Test that the command creates one Markdown file per ADR."""
        ADR.objects.create(title="Use PostgreSQL", context="c", decision="d", consequences="c")
        ADR.objects.create(title="Use Redis", context="c", decision="d", consequences="c")
        call_command("export_adrs", f"--output-dir={self.output_dir}")
        files = list(Path(self.output_dir).iterdir())
        self.assertEqual(len(files), 2)

    def test_export_file_contains_adr_title(self) -> None:
        """Test that the exported file contains the ADR title."""
        ADR.objects.create(
            title="Use PostgreSQL", context="We need a DB.", decision="PG.", consequences="SQL."
        )
        call_command("export_adrs", f"--output-dir={self.output_dir}")
        content = next(Path(self.output_dir).iterdir()).read_text(encoding="utf-8")
        self.assertIn("Use PostgreSQL", content)

    def test_export_file_contains_superseded_by(self) -> None:
        """Test that the exported file includes the superseding ADR when set."""
        old = ADR.objects.create(title="Old", context="c", decision="d", consequences="c")
        new = ADR.objects.create(title="New", context="c", decision="d", consequences="c")
        old.superseded_by = new
        old.status = ADR.Status.SUPERSEDED
        old.save()
        call_command("export_adrs", f"--output-dir={self.output_dir}")
        files = {f.name: f.read_text(encoding="utf-8") for f in Path(self.output_dir).iterdir()}
        old_content = next(v for k, v in files.items() if "old" in k)
        self.assertIn("Superseded by", old_content)

    def test_export_with_no_adrs_writes_zero_count(self) -> None:
        """Test that the command reports zero exported files when no ADRs exist."""
        out = io.StringIO()
        call_command("export_adrs", f"--output-dir={self.output_dir}", stdout=out)
        self.assertIn("0 ADR(s)", out.getvalue())
