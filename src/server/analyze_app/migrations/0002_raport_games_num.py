# Generated by Django 4.1.1 on 2022-09-27 16:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("analyze_app", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="raport",
            name="games_num",
            field=models.IntegerField(default=0),
        ),
    ]