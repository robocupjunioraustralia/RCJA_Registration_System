# Generated by Django 3.1.14 on 2023-08-31 14:35

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0006_auto_20201024_1418'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='student',
            name='birthday',
        ),
    ]