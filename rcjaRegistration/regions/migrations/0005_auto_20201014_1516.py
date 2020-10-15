# Generated by Django 3.0.7 on 2020-10-14 04:16

import common.fields
from django.db import migrations, models
import rcjaRegistration.storageBackends


class Migration(migrations.Migration):

    dependencies = [
        ('regions', '0004_auto_20200505_1353'),
    ]

    operations = [
        migrations.AddField(
            model_name='state',
            name='defaultEventImage',
            field=common.fields.UUIDImageField(blank=True, null=True, original_filename_field='defaultEventImageOriginalFilename', storage=rcjaRegistration.storageBackends.PublicMediaStorage(), upload_prefix='DefaultEventImage', verbose_name='Default event image'),
        ),
        migrations.AddField(
            model_name='state',
            name='defaultEventImageOriginalFilename',
            field=models.CharField(blank=True, editable=False, max_length=300, null=True, verbose_name='Original filename'),
        ),
    ]