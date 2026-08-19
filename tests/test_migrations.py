"""Tests for the migration chain that moves the primary key onto number."""

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase

from django_adr.models import ADR

INITIAL = ("django_adr", "0001_initial")
LATEST = ("django_adr", "0005_adr_superseded_constraints")

SEED = (
    "INSERT INTO django_adr_adr (id, number, title, status, date, context, decision,"
    " consequences, superseded_by_id) VALUES"
    " (10, 3, 'Old decision', 'superseded', '2026-01-01', 'ctx', 'dec', 'con', 20),"
    " (20, 7, 'New decision', 'proposed',   '2026-02-01', 'ctx', 'dec', 'con', NULL),"
    " (30, 9, 'Unrelated',    'accepted',   '2026-03-01', 'ctx', 'dec', 'con', NULL),"
    " (40, 11,'Broken state', 'superseded', '2026-04-01', 'ctx', 'dec', 'con', NULL)"
)


class TestNumberPrimaryKeyMigration(TransactionTestCase):
    """Exercise 0001 to 0005 against data the pre-2.0 schema could hold."""

    reset_sequences = True

    def setUp(self) -> None:
        """Rewind to the original schema and seed rows where id differs from number."""
        self._migrate(INITIAL)
        with connection.cursor() as cursor:
            cursor.execute(SEED)

    def tearDown(self) -> None:
        """Leave the database on the latest migration."""
        self._migrate(LATEST)

    @staticmethod
    def _migrate(target: tuple[str, str]) -> None:
        """Move the django_adr app to the given migration."""
        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate([target])

    def test_supersession_link_survives_the_key_change(self) -> None:
        """Test that a foreign key stored as an id is remapped to the number."""
        self._migrate(LATEST)
        self.assertEqual(ADR.objects.get(number=3).superseded_by_id, 7)

    def test_identifiers_are_preserved(self) -> None:
        """Test that every ADR keeps the number it was published under."""
        self._migrate(LATEST)
        self.assertEqual(sorted(ADR.objects.values_list("number", flat=True)), [3, 7, 9, 11])

    def test_constraint_violating_rows_are_repaired(self) -> None:
        """Test that a superseded ADR with no target is reset before constraints apply."""
        self._migrate(LATEST)
        self.assertEqual(ADR.objects.get(number=11).status, ADR.Status.PROPOSED)

    def test_sequence_continues_past_the_migrated_rows(self) -> None:
        """Test that the number sequence is advanced past the data it inherited."""
        self._migrate(LATEST)
        created = ADR.objects.create(title="After", context="c", decision="d", consequences="c")
        self.assertGreater(created.number, 11)

    def test_chain_reverses_cleanly(self) -> None:
        """Test that unwinding to the original schema restores the id primary key."""
        self._migrate(LATEST)
        self._migrate(INITIAL)
        with connection.cursor() as cursor:
            columns = {
                column.name
                for column in connection.introspection.get_table_description(
                    cursor, "django_adr_adr"
                )
            }
            primary_key = connection.introspection.get_primary_key_column(cursor, "django_adr_adr")
        self.assertIn("id", columns)
        self.assertEqual(primary_key, "id")
