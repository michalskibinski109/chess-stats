# Generated by Django 4.1.8 on 2023-10-24 09:30

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("analyze_app", "0002_report_professional"),
    ]

    operations = [
        migrations.AlterField(
            model_name="report",
            name="professional",
            field=models.BooleanField(default=False),
        ),
    ]