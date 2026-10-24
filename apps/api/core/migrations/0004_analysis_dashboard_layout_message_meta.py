from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_ratelimitevent"),
    ]

    operations = [
        migrations.AddField(
            model_name="analysis",
            name="dashboard_layout",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="message",
            name="meta",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
