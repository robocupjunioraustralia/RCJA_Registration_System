# Generated by Django 3.0.3 on 2020-03-10 10:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('regions', '0002_state_treasurer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='state',
            name='name',
            field=models.CharField(max_length=30, unique=True, verbose_name='Name'),
        ),
    ]