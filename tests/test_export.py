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

    def test_export_uses_a_placeholder_when_the_title_has_no_slug(self) -> None:
        """Test that a title slugifying to nothing still produces a usable filename."""
        adr = ADR.objects.create(title="!!! ???", context="c", decision="d", consequences="c")
        call_command("export_adrs", f"--output-dir={self.output_dir}")
        name = next(Path(self.output_dir).iterdir()).name
        self.assertEqual(name, f"{adr.number:04d}-adr.md")

    def test_export_keeps_unicode_titles_in_the_filename(self) -> None:
        """Test that a non-ASCII title is not flattened away to an empty slug."""
        adr = ADR.objects.create(title="Città", context="c", decision="d", consequences="c")
        call_command("export_adrs", f"--output-dir={self.output_dir}")
        self.assertEqual(next(Path(self.output_dir).iterdir()).name, f"{adr.number:04d}-città.md")

    def test_export_distinguishes_adrs_sharing_a_title(self) -> None:
        """Test that identically titled ADRs do not overwrite one another."""
        ADR.objects.create(title="Same", context="c", decision="d", consequences="c")
        ADR.objects.create(title="Same", context="c", decision="d", consequences="c")
        call_command("export_adrs", f"--output-dir={self.output_dir}")
        self.assertEqual(len(list(Path(self.output_dir).iterdir())), 2)

    def test_export_handles_empty_text_fields(self) -> None:
        """Test that an ADR with no body still exports every section heading."""
        ADR.objects.create(title="Bare")
        call_command("export_adrs", f"--output-dir={self.output_dir}")
        content = next(Path(self.output_dir).iterdir()).read_text(encoding="utf-8")
        self.assertIn("## Context", content)
        self.assertIn("## Decision", content)
        self.assertIn("## Consequences", content)

    def test_export_reuses_an_existing_output_directory(self) -> None:
        """Test that exporting into a directory that already exists is not an error."""
        Path(self.output_dir, "stale.md").write_text("stale", encoding="utf-8")
        adr = ADR.objects.create(title="Fresh", context="c", decision="d", consequences="c")
        call_command("export_adrs", f"--output-dir={self.output_dir}")
        self.assertTrue(Path(self.output_dir, f"{adr.number:04d}-fresh.md").exists())

    def test_export_creates_a_missing_output_directory(self) -> None:
        """Test that a nested output directory is created on demand."""
        nested = Path(self.output_dir) / "docs" / "adr"
        adr = ADR.objects.create(title="Nested", context="c", decision="d", consequences="c")
        call_command("export_adrs", f"--output-dir={nested}")
        self.assertTrue((nested / f"{adr.number:04d}-nested.md").exists())

    def test_front_matter_is_omitted_by_default(self) -> None:
        """Test that no YAML block is written unless it is asked for."""
        ADR.objects.create(title="Plain", context="c", decision="d", consequences="c")
        call_command("export_adrs", f"--output-dir={self.output_dir}")
        content = next(Path(self.output_dir).iterdir()).read_text(encoding="utf-8")
        self.assertFalse(content.startswith("---"))

    def test_front_matter_flag_writes_a_yaml_block(self) -> None:
        """Test that --front-matter prefixes the file with the ADR metadata."""
        adr = ADR.objects.create(title="Meta", context="c", decision="d", consequences="c")
        call_command("export_adrs", f"--output-dir={self.output_dir}", "--front-matter")
        content = next(Path(self.output_dir).iterdir()).read_text(encoding="utf-8")
        self.assertTrue(content.startswith("---\n"))
        self.assertIn(f"adr: {adr.number:04d}", content)
        self.assertIn('title: "Meta"', content)
        self.assertIn("status: proposed", content)

    def test_front_matter_quotes_awkward_titles(self) -> None:
        """Test that a title containing quotes and a colon stays valid YAML."""
        ADR.objects.create(title='Use "X": now', context="c", decision="d", consequences="c")
        call_command("export_adrs", f"--output-dir={self.output_dir}", "--front-matter")
        content = next(Path(self.output_dir).iterdir()).read_text(encoding="utf-8")
        self.assertIn('title: "Use \\"X\\": now"', content)

    def test_front_matter_records_the_superseding_adr(self) -> None:
        """Test that the YAML block carries the superseding ADR number."""
        old = ADR.objects.create(title="Old", context="c", decision="d", consequences="c")
        new = ADR.objects.create(title="New", context="c", decision="d", consequences="c")
        old.supersede_with(new)
        call_command("export_adrs", f"--output-dir={self.output_dir}", "--front-matter")
        content = Path(self.output_dir, f"{old.number:04d}-old.md").read_text(encoding="utf-8")
        self.assertIn(f"superseded_by: {new.number:04d}", content)
