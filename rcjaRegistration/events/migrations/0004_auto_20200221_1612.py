# Generated by Django 2.2.8 on 2020-02-21 05:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0003_auto_20200217_2257'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='event',
            options={'ordering': ['-startDate'], 'verbose_name': 'Event'},
        ),
    ]
