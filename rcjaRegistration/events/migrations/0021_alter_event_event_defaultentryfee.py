# Generated by Django 4.2.10 on 2024-03-12 12:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0020_baseeventattendance_copiedfrom'),
    ]

    operations = [
        migrations.AlterField(
            model_name='event',
            name='event_defaultEntryFee',
            field=models.PositiveIntegerField(default=0, verbose_name='Default entry fee'),
        ),
    ]
