# Generated by Django 5.1.5 on 2025-01-25 11:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0028_baseeventattendance_invoiceoverride'),
    ]

    operations = [
        migrations.RenameField(
            model_name='availabledivision',
            old_name='division_maxTeamsForDivision',
            new_name='division_maxRegistrationsForDivision',
        ),
        migrations.RenameField(
            model_name='availabledivision',
            old_name='division_maxTeamsPerSchool',
            new_name='division_maxRegistrationsPerSchool',
        ),
        migrations.RenameField(
            model_name='event',
            old_name='event_maxTeamsForEvent',
            new_name='event_maxRegistrationsForEvent',
        ),
        migrations.RenameField(
            model_name='event',
            old_name='event_maxTeamsPerSchool',
            new_name='event_maxRegistrationsPerSchool',
        ),
        migrations.AlterField(
            model_name='availabledivision',
            name='division',
            field=models.ForeignKey(limit_choices_to={'active': True}, on_delete=django.db.models.deletion.CASCADE, to='events.division', verbose_name='Division'),
        ),
        migrations.AlterField(
            model_name='availabledivision',
            name='division_maxRegistrationsForDivision',
            field=models.PositiveIntegerField(blank=True, help_text='Leave blank for no limit. Will override limit on event.', null=True, verbose_name='Max registrations for division'),
        ),
        migrations.AlterField(
            model_name='availabledivision',
            name='division_maxRegistrationsPerSchool',
            field=models.PositiveIntegerField(blank=True, help_text='Leave blank for no limit. Will override limit on event.', null=True, verbose_name='Max registrations per school'),
        ),
        migrations.AlterField(
            model_name='event',
            name='event_maxRegistrationsForEvent',
            field=models.PositiveIntegerField(blank=True, help_text='Leave blank for no limit. Only enforced on the mentor signup page, can be overridden in the admin portal.', null=True, verbose_name='Max registrations for event'),
        ),
        migrations.AlterField(
            model_name='event',
            name='event_maxRegistrationsPerSchool',
            field=models.PositiveIntegerField(blank=True, help_text='Leave blank for no limit. Only enforced on the mentor signup page, can be overridden in the admin portal.', null=True, verbose_name='Max registrations per school'),
        ),
    ]
