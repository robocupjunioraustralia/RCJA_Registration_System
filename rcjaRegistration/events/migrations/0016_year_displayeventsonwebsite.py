# Generated by Django 3.0.7 on 2021-01-06 11:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0015_auto_20201015_1254'),
    ]

    operations = [
        migrations.AddField(
            model_name='year',
            name='displayEventsOnWebsite',
            field=models.BooleanField(default=False, verbose_name='Display events on website'),
        ),
    ]
