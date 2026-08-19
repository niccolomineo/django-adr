from django.core.management.color import no_style
from django.db import migrations, models


def reset_number_sequence(apps, schema_editor):
    """Advance the number sequence past the rows that already exist."""
    ADR = apps.get_model("django_adr", "ADR")
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        for statement in connection.ops.sequence_reset_sql(no_style(), [ADR]):
            cursor.execute(statement)


class Migration(migrations.Migration):
    dependencies = [("django_adr", "0002_superseded_by_number")]
    operations = [
        migrations.RemoveField(model_name="adr", name="id"),
        migrations.AlterField(
            model_name="adr",
            name="number",
            field=models.BigAutoField(
                primary_key=True,
                serialize=False,
                verbose_name="number",
            ),
        ),
        migrations.RunPython(reset_number_sequence, migrations.RunPython.noop),
    ]
