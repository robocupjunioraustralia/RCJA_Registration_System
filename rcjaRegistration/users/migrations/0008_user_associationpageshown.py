# Generated by Django 5.1.5 on 2025-02-02 12:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_alter_user_mobilenumber'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='associationPageShown',
            field=models.BooleanField(default=False, editable=False, verbose_name='Association page shown'),
        ),
    ]
