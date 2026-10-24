import uuid

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_analysis_dashboard_job_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductInterest",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=120)),
                ("email", models.EmailField()),
                ("interests", models.JSONField(default=list)),
                ("comment", models.TextField(blank=True)),
                ("analysis_id", models.UUIDField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
        ),
    ]
