# Generated by Django 2.2.10 on 2020-02-25 08:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('events', '0006_auto_20200225_1920'),
    ]

    operations = [
        migrations.AlterField(
            model_name='availabledivision',
            name='division_maxMembersPerTeam',
            field=models.PositiveIntegerField(blank=True, help_text='Leave blank for no limit. Will override limit on event.', null=True, verbose_name='Max members per team'),
        ),
        migrations.AlterField(
            model_name='availabledivision',
            name='division_maxTeamsForDivision',
            field=models.PositiveIntegerField(blank=True, help_text='Leave blank for no limit. Will override limit on event.', null=True, verbose_name='Max teams for division'),
        ),
        migrations.AlterField(
            model_name='availabledivision',
            name='division_maxTeamsPerSchool',
            field=models.PositiveIntegerField(blank=True, help_text='Leave blank for no limit. Will override limit on event.', null=True, verbose_name='Max teams per school'),
        ),
        migrations.AlterField(
            model_name='event',
            name='event_maxTeamsForEvent',
            field=models.PositiveIntegerField(blank=True, help_text='Leave blank for no limit. Only enforced on the mentor signup page, can be overridden in the admin portal.', null=True, verbose_name='Max teams for event'),
        ),
        migrations.AlterField(
            model_name='event',
            name='event_maxTeamsPerSchool',
            field=models.PositiveIntegerField(blank=True, help_text='Leave blank for no limit. Only enforced on the mentor signup page, can be overridden in the admin portal.', null=True, verbose_name='Max teams per school'),
        ),
    ]
