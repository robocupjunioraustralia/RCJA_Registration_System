# Generated by Django 4.2.4 on 2023-09-30 05:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('coordination', '0007_auto_20201015_2127'),
    ]

    operations = [
        migrations.AlterField(
            model_name='coordinator',
            name='permissionLevel',
            field=models.CharField(choices=[('viewall', 'View all'), ('eventmanager', 'Event manager'), ('schoolmanager', 'School manager'), ('billingmanager', 'Billing manager'), ('associationmanager', 'Association manager'), ('webeditor', 'Web editor'), ('full', 'Full')], max_length=20, verbose_name='Permission level'),
        ),
    ]
