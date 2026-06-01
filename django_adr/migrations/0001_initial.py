import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True
    dependencies = []
    operations = [
        migrations.CreateModel(
            name="ADR",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "number",
                    models.PositiveIntegerField(
                        editable=False,
                        unique=True,
                        verbose_name="number",
                    ),
                ),
                ("title", models.CharField(max_length=200, verbose_name="title")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("proposed", "Proposed"),
                            ("accepted", "Accepted"),
                            ("deprecated", "Deprecated"),
                            ("superseded", "Superseded"),
                            ("rejected", "Rejected"),
                        ],
                        default="proposed",
                        max_length=20,
                        verbose_name="status",
                    ),
                ),
                ("date", models.DateField(auto_now_add=True, verbose_name="date")),
                ("context", models.TextField(blank=True, verbose_name="context")),
                ("decision", models.TextField(blank=True, verbose_name="decision")),
                ("consequences", models.TextField(blank=True, verbose_name="consequences")),
                (
                    "superseded_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="supersedes",
                        to="django_adr.adr",
                        verbose_name="superseded by",
                    ),
                ),
            ],
            options={
                "verbose_name": "ADR",
                "verbose_name_plural": "ADRs",
                "ordering": ("number",),
            },
        ),
    ]
