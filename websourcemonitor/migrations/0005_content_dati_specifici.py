# Generated by Django 4.2.13 on 2024-07-19 12:23

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("websourcemonitor", "0004_content_scraping_class"),
    ]

    operations = [
        migrations.AddField(
            model_name="content",
            name="dati_specifici",
            field=models.JSONField(blank=True, default=dict, null=True),
        ),
    ]
