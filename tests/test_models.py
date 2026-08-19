"""ADR model tests."""

from django.core.exceptions import ValidationError
from django.db import IntegrityError, models, transaction
from django.test import TestCase, TransactionTestCase

from django_adr.models import ADR


class TestADRStr(TestCase):
    """Test ADR string representation."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        super().setUpTestData()
        cls.adr = ADR.objects.create(
            number=42,
            title="Use PostgreSQL",
            context="We need a relational database.",
            decision="Use PostgreSQL.",
            consequences="Team must know SQL.",
        )

    def test_str_includes_zero_padded_number_and_title(self) -> None:
        """Test that __str__ includes a zero-padded number and title."""
        self.assertEqual(str(self.adr), "ADR-0042: Use PostgreSQL")


class TestADRAutoNumber(TestCase):
    """Test ADR auto-number assignment."""

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


class TestADRNumberAllocation(TestCase):
    """Test that ADR numbers come from the database, not a read-then-write."""

    def test_save_is_not_overridden(self) -> None:
        """Test that the model no longer hand-rolls number allocation on save."""
        self.assertIs(ADR.save, models.Model.save)

    def test_number_is_not_reused_after_a_delete(self) -> None:
        """Test that a freed number is not handed out again."""
        ADR.objects.create(title="A", context="c", decision="d", consequences="c")
        second = ADR.objects.create(title="B", context="c", decision="d", consequences="c")
        freed = second.number
        second.delete()
        third = ADR.objects.create(title="C", context="c", decision="d", consequences="c")
        self.assertEqual(third.number, freed + 1)


class TestADRConstraints(TestCase):
    """Test the database-level supersession invariants."""

    @classmethod
    def setUpTestData(cls) -> None:
        """Set up test data."""
        super().setUpTestData()
        cls.other = ADR.objects.create(title="Other", context="c", decision="d", consequences="c")

    def test_superseded_status_without_target_is_rejected_by_the_database(self) -> None:
        """Test that the constraint catches what clean() alone would let through."""
        with self.assertRaises(IntegrityError), transaction.atomic():
            ADR.objects.create(
                title="T", status=ADR.Status.SUPERSEDED, context="c", decision="d", consequences="c"
            )

    def test_target_without_superseded_status_is_rejected_by_the_database(self) -> None:
        """Test that a supersession target requires the SUPERSEDED status."""
        with self.assertRaises(IntegrityError), transaction.atomic():
            ADR.objects.create(
                title="T",
                status=ADR.Status.ACCEPTED,
                context="c",
                decision="d",
                consequences="c",
                superseded_by=self.other,
            )

    def test_self_supersession_is_rejected_by_the_database(self) -> None:
        """Test that an ADR cannot be recorded as superseding itself."""
        adr = ADR.objects.create(title="Loop", context="c", decision="d", consequences="c")
        with self.assertRaises(IntegrityError), transaction.atomic():
            ADR.objects.filter(pk=adr.pk).update(superseded_by=adr.pk, status=ADR.Status.SUPERSEDED)

    def test_self_supersession_fails_validation(self) -> None:
        """Test that clean() reports self-supersession before the database does."""
        adr = ADR.objects.create(title="Loop", context="c", decision="d", consequences="c")
        adr.superseded_by = adr
        adr.status = ADR.Status.SUPERSEDED
        with self.assertRaises(ValidationError):
            adr.full_clean()


class TestADRSupersedeWith(TestCase):
    """Test the supersede_with domain operation."""

    def setUp(self) -> None:
        """Create an old and a new ADR."""
        self.old = ADR.objects.create(title="Old", context="c", decision="d", consequences="c")
        self.new = ADR.objects.create(title="New", context="c", decision="d", consequences="c")

    def test_supersede_with_sets_both_halves_of_the_invariant(self) -> None:
        """Test that supersede_with writes status and superseded_by together."""
        self.old.supersede_with(self.new)
        self.old.refresh_from_db()
        self.assertEqual(self.old.status, ADR.Status.SUPERSEDED)
        self.assertEqual(self.old.superseded_by, self.new)

    def test_supersede_with_refuses_self(self) -> None:
        """Test that an ADR cannot supersede itself."""
        with self.assertRaises(ValidationError):
            self.old.supersede_with(self.old)

    def test_supersede_with_refuses_an_already_superseded_adr(self) -> None:
        """Test that an already superseded ADR cannot be superseded again."""
        self.old.supersede_with(self.new)
        newer = ADR.objects.create(title="Newer", context="c", decision="d", consequences="c")
        with self.assertRaises(ValidationError):
            self.old.supersede_with(newer)


class TestADRSupersessionChain(TestCase):
    """Test supersession lineage traversal."""

    def test_chain_of_a_lone_adr_is_just_itself(self) -> None:
        """Test that an ADR with no supersession links returns only itself."""
        adr = ADR.objects.create(title="Alone", context="c", decision="d", consequences="c")
        self.assertEqual(adr.supersession_chain(), [adr])

    def test_chain_spans_multiple_hops_in_both_directions(self) -> None:
        """Test that the lineage is returned oldest first from any member."""
        first = ADR.objects.create(title="First", context="c", decision="d", consequences="c")
        second = ADR.objects.create(title="Second", context="c", decision="d", consequences="c")
        third = ADR.objects.create(title="Third", context="c", decision="d", consequences="c")
        first.supersede_with(second)
        second.supersede_with(third)
        self.assertEqual(second.supersession_chain(), [first, second, third])

    def test_chain_terminates_on_a_cycle(self) -> None:
        """Test that a two-ADR supersession loop does not hang the walk."""
        one = ADR.objects.create(title="One", context="c", decision="d", consequences="c")
        two = ADR.objects.create(title="Two", context="c", decision="d", consequences="c")
        one.supersede_with(two)
        ADR.objects.filter(pk=two.pk).update(superseded_by=one.pk, status=ADR.Status.SUPERSEDED)
        two.refresh_from_db()
        self.assertEqual(two.supersession_chain(), [one, two])


class TestADRFirstNumber(TransactionTestCase):
    """Test numbering in a log that has never held an ADR."""

    reset_sequences = True

    def test_first_adr_gets_number_one(self) -> None:
        """Test that the first ADR created receives number 1."""
        adr = ADR.objects.create(title="First", context="c", decision="d", consequences="c")
        self.assertEqual(adr.number, 1)
