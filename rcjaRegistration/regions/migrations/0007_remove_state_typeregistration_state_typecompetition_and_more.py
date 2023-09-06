# Generated by Django 4.2.4 on 2023-09-02 08:54

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('regions', '0006_region_state'),
    ]

    operations = [
        migrations.RenameField(
            model_name='state',
            old_name='typeRegistration',
            new_name='typeCompetition',
        ),
        migrations.AlterField(
            model_name='state',
            name='typeCompetition',
            field=models.BooleanField(default=False, help_text='Allow events to be created for this state. Once enabled cannot be disabled.', verbose_name='Competition'),
        ),
        migrations.AddField(
            model_name='state',
            name='typeUserRegistration',
            field=models.BooleanField(default=False, help_text='Allow users to register to this state. Once enabled cannot be disabled.', verbose_name='User registration'),
        ),
        migrations.AlterField(
            model_name='region',
            name='state',
            field=models.ForeignKey(blank=True, help_text='Leave blank for a global region. Global regions are only editable by global administrators.', limit_choices_to={'typeUserRegistration': True}, null=True, on_delete=django.db.models.deletion.PROTECT, to='regions.state', verbose_name='State'),
        ),
    ]