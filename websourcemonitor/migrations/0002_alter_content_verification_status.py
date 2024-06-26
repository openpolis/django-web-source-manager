# Generated by Django 4.2.13 on 2024-06-13 10:34

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("websourcemonitor", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="content",
            name="verification_status",
            field=models.IntegerField(
                choices=[
                    (0, "Immutato"),
                    (1, "Cambiato"),
                    (2, "Errore rilevato"),
                    (3, "Aggiornato alla destinazione"),
                    (4, "Errore segnalato"),
                ],
                null=True,
                verbose_name="Stato",
            ),
        ),
    ]
