from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0004_analysis_dashboard_layout_message_meta"),
    ]

    operations = [
        migrations.AddField(
            model_name="analysis",
            name="dashboard_job_id",
            field=models.UUIDField(blank=True, null=True),
        ),
    ]
