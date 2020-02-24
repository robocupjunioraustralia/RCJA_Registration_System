# Generated by Django 2.2.10 on 2020-02-23 14:27

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0002_auto_20200224_0021'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='campus',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='schools.Campus', verbose_name='Campus'),
        ),
    ]
