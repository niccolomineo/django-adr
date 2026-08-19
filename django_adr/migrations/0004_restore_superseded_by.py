import django.db.models.deletion
from django.db import migrations, models


def relink(apps, schema_editor):
    """Point the restored foreign key at the parked numbers."""
    ADR = apps.get_model("django_adr", "ADR")
    for pk, number in ADR.objects.exclude(superseded_by_number=None).values_list(
        "pk", "superseded_by_number"
    ):
        ADR.objects.filter(pk=pk).update(superseded_by=number)


def park_numbers(apps, schema_editor):
    """Copy the foreign key back into the temporary column."""
    ADR = apps.get_model("django_adr", "ADR")
    for pk, number in ADR.objects.exclude(superseded_by=None).values_list("pk", "superseded_by_id"):
        ADR.objects.filter(pk=pk).update(superseded_by_number=number)


class Migration(migrations.Migration):
    dependencies = [("django_adr", "0003_number_primary_key")]
    operations = [
        migrations.AddField(
            model_name="adr",
            name="superseded_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="supersedes",
                to="django_adr.adr",
                verbose_name="superseded by",
            ),
        ),
        migrations.RunPython(relink, park_numbers),
        migrations.RemoveField(model_name="adr", name="superseded_by_number"),
    ]
