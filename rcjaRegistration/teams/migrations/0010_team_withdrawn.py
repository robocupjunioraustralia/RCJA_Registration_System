# Generated by Django 4.2.16 on 2024-11-02 10:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0009_platformcategory_hardwareplatform_category_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='team',
            name='withdrawn',
            field=models.BooleanField(default=False, help_text='Selecting this box will remove the team from the scoring system but leave it on the invoice.', verbose_name='Withdrawn'),
        ),
    ]