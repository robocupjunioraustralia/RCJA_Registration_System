# Generated by Django 4.2.18 on 2025-01-21 12:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0026_remove_event_event_type_check_event_eventtype_check'),
    ]

    operations = [
        migrations.AddField(
            model_name='event',
            name='cmsEventId',
            field=models.CharField(editable=False, help_text='The ID of this event in the RCJ CMS', max_length=15, null=True, verbose_name='CMS Event ID'),
        ),
    ]
