"""ADR model tests."""

from django.core.exceptions import ValidationError
from django.test import TestCase

from django_adr.models import ADR


class TestADRStr(TestCase):
    """Test ADR string representation."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        super().setUpTestData()
        cls.adr = ADR.objects.create(
            title="Use PostgreSQL",
            context="We need a relational database.",
            decision="Use PostgreSQL.",
            consequences="Team must know SQL.",
        )

    def test_str_includes_zero_padded_number_and_title(self) -> None:
        """Test that __str__ includes a zero-padded number and title."""
        self.assertEqual(str(self.adr), "ADR-0001: Use PostgreSQL")


class TestADRAutoNumber(TestCase):
    """Test ADR auto-number assignment."""

    def test_first_adr_gets_number_one(self) -> None:
        """Test that the first ADR created receives number 1."""
        adr = ADR.objects.create(title="First", context="c", decision="d", consequences="c")
        self.assertEqual(adr.number, 1)

    def test_second_adr_gets_sequential_number(self) -> None:
        """Test that each subsequent ADR receives the next sequential number."""
        first = ADR.objects.create(title="A", context="c", decision="d", consequences="c")
        second = ADR.objects.create(title="B", context="c", decision="d", consequences="c")
        self.assertEqual(second.number, first.number + 1)

    def test_explicit_number_is_preserved(self) -> None:
        """Test that an explicitly provided number is not overwritten on save."""
        adr = ADR.objects.create(
            number=99, title="Explicit", context="c", decision="d", consequences="c"
        )
        self.assertEqual(adr.number, 99)


class TestADRMarkdownProperties(TestCase):
    """Test ADR Markdown rendering properties."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        super().setUpTestData()
        cls.adr = ADR.objects.create(
            title="Markdown ADR",
            context="## Context\n\nSome **bold** text.",
            decision="Use *italics*.",
            consequences="- item one\n- item two",
        )

    def test_context_html_renders_markdown(self) -> None:
        """Test that context_html returns rendered HTML from Markdown source."""
        self.assertIn("<h2>", self.adr.context_html)
        self.assertIn("<strong>bold</strong>", self.adr.context_html)

    def test_decision_html_renders_markdown(self) -> None:
        """Test that decision_html returns HTML with emphasis tags."""
        self.assertIn("<em>italics</em>", self.adr.decision_html)

    def test_consequences_html_renders_markdown(self) -> None:
        """Test that consequences_html returns HTML list from Markdown list source."""
        self.assertIn("<li>", self.adr.consequences_html)


class TestADRBlankTextFields(TestCase):
    """Test that text fields accept blank values."""

    def test_text_fields_allow_blank(self) -> None:
        """Test that context, decision, and consequences accept empty strings via full_clean."""
        adr = ADR(title="Draft", context="", decision="", consequences="")
        adr.full_clean()


class TestADRClean(TestCase):
    """Test ADR status/superseded_by validation."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        super().setUpTestData()
        cls.other = ADR.objects.create(title="Other", context="c", decision="d", consequences="c")

    def test_superseded_status_without_superseded_by_raises(self) -> None:
        """Test that SUPERSEDED status without a superseding ADR fails validation."""
        adr = ADR(
            title="T", status=ADR.Status.SUPERSEDED, context="c", decision="d", consequences="c"
        )
        with self.assertRaises(ValidationError):
            adr.full_clean()

    def test_superseded_by_without_superseded_status_raises(self) -> None:
        """Test that setting superseded_by without SUPERSEDED status fails validation."""
        adr = ADR(
            title="T",
            status=ADR.Status.ACCEPTED,
            context="c",
            decision="d",
            consequences="c",
            superseded_by=self.other,
        )
        with self.assertRaises(ValidationError):
            adr.full_clean()

    def test_superseded_status_with_superseded_by_passes(self) -> None:
        """Test that SUPERSEDED status with a superseding ADR passes validation."""
        adr = ADR(
            title="T",
            status=ADR.Status.SUPERSEDED,
            context="c",
            decision="d",
            consequences="c",
            superseded_by=self.other,
        )
        adr.full_clean()


class TestADRStatusDefault(TestCase):
    """Test ADR default status."""

    def test_default_status_is_proposed(self) -> None:
        """Test that a new ADR defaults to PROPOSED status."""
        adr = ADR.objects.create(title="T", context="c", decision="d", consequences="c")
        self.assertEqual(adr.status, ADR.Status.PROPOSED)


class TestADRSupersededBy(TestCase):
    """Test ADR supersession relationship."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        super().setUpTestData()
        cls.old = ADR.objects.create(title="Old", context="c", decision="d", consequences="c")
        cls.new = ADR.objects.create(title="New", context="c", decision="d", consequences="c")
        cls.old.superseded_by = cls.new
        cls.old.status = ADR.Status.SUPERSEDED
        cls.old.save()

    def test_superseded_by_links_to_new_adr(self) -> None:
        """Test that superseded_by foreign key points to the replacing ADR."""
        self.old.refresh_from_db()
        self.assertEqual(self.old.superseded_by, self.new)

    def test_supersedes_reverse_relation_lists_superseded_adr(self) -> None:
        """Test that the reverse relation supersedes lists the superseded ADR."""
        self.assertIn(self.old, self.new.supersedes.all())
