from django.db import migrations, models


def store_numbers(apps, schema_editor):
    """Park each supersession target's number in the temporary column."""
    ADR = apps.get_model("django_adr", "ADR")
    for pk, number in ADR.objects.exclude(superseded_by=None).values_list(
        "pk", "superseded_by__number"
    ):
        ADR.objects.filter(pk=pk).update(superseded_by_number=number)


def restore_links(apps, schema_editor):
    """Rebuild the foreign key from the parked numbers."""
    ADR = apps.get_model("django_adr", "ADR")
    pks_by_number = dict(ADR.objects.values_list("number", "pk"))
    for pk, number in ADR.objects.exclude(superseded_by_number=None).values_list(
        "pk", "superseded_by_number"
    ):
        ADR.objects.filter(pk=pk).update(superseded_by=pks_by_number[number])


class Migration(migrations.Migration):
    dependencies = [("django_adr", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="adr",
            name="superseded_by_number",
            field=models.PositiveIntegerField(editable=False, null=True),
        ),
        migrations.RunPython(store_numbers, restore_links),
        migrations.RemoveField(model_name="adr", name="superseded_by"),
    ]
