# Generated by Django 4.2.4 on 2023-10-03 12:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0020_baseeventattendance_copiedfrom'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='eventSurchargeAmount',
            field=models.FloatField(default=0, editable=False, verbose_name='Surcharge amount for event'),
        ),
    ]
