# Generated by Django 4.2.16 on 2024-11-02 06:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0021_alter_event_event_defaultentryfee'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='eventSurchargeAmount',
            field=models.FloatField(default=0, editable=False, verbose_name='Surcharge amount for event'),
        ),
    ]
