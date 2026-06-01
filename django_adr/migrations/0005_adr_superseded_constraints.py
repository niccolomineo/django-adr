from django.db import migrations, models
from django.db.models import F, Q


def repair_inconsistent_rows(apps, schema_editor):
    """Bring rows that predate the constraints back into a valid state."""
    ADR = apps.get_model("django_adr", "ADR")
    ADR.objects.filter(superseded_by=F("number")).update(superseded_by=None, status="proposed")
    ADR.objects.filter(status="superseded", superseded_by__isnull=True).update(status="proposed")
    ADR.objects.exclude(status="superseded").filter(superseded_by__isnull=False).update(
        status="superseded"
    )


class Migration(migrations.Migration):
    dependencies = [("django_adr", "0004_restore_superseded_by")]
    operations = [
        migrations.RunPython(repair_inconsistent_rows, migrations.RunPython.noop),
        migrations.AddConstraint(
            model_name="adr",
            constraint=models.CheckConstraint(
                condition=(
                    Q(status="superseded", superseded_by__isnull=False)
                    | (~Q(status="superseded") & Q(superseded_by__isnull=True))
                ),
                name="adr_superseded_iff_superseded_by",
            ),
        ),
        migrations.AddConstraint(
            model_name="adr",
            constraint=models.CheckConstraint(
                condition=~Q(superseded_by=F("number")),
                name="adr_not_self_superseded",
            ),
        ),
    ]
