# Generated by Django 4.2.5 on 2023-10-08 19:00

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("analyze_app", "0001_initial"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="chessgame",
            name="result",
        ),
        migrations.AddField(
            model_name="chessgame",
            name="end_reason",
            field=models.CharField(
                default=django.utils.timezone.now,
                help_text="Reason of the game end. e.g., 'checkmate'",
                max_length=50,
            ),
            preserve_default=False,
        ),
    ]
