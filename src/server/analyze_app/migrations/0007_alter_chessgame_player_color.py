# Generated by Django 4.1.1 on 2022-09-29 14:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("analyze_app", "0006_alter_chessgame_player_color_alter_chessgame_result"),
    ]

    operations = [
        migrations.AlterField(
            model_name="chessgame",
            name="player_color",
            field=models.IntegerField(help_text="Player's color 0-Black, 1-White"),
        ),
    ]