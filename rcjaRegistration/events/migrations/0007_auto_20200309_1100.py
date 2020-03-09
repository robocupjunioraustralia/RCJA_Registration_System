# Generated by Django 3.0.3 on 2020-03-09 00:00

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('regions', '0002_state_treasurer'),
        ('events', '0006_division_state'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='location',
        ),
        migrations.CreateModel(
            name='Venue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creationDateTime', models.DateTimeField(auto_now_add=True, verbose_name='Creation date')),
                ('updatedDateTime', models.DateTimeField(auto_now=True, verbose_name='Last modified date')),
                ('name', models.CharField(max_length=40, verbose_name='Name')),
                ('address', models.TextField(blank=True, verbose_name='Address')),
                ('state', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='regions.State', verbose_name='State')),
            ],
            options={
                'verbose_name': 'Venue',
                'ordering': ['name'],
                'unique_together': {('name', 'state')},
            },
        ),
        migrations.AddField(
            model_name='event',
            name='venue',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, to='events.Venue', verbose_name='Venue'),
        ),
    ]