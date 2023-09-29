# Generated by Django 4.2.4 on 2023-09-29 04:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0019_alter_division_state_alter_event_state_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='baseeventattendance',
            name='copiedFrom',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='copiedTo', to='events.baseeventattendance', verbose_name='Copied from'),
        ),
    ]