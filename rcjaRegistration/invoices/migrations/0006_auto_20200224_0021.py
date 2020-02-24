# Generated by Django 2.2.10 on 2020-02-23 13:21

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('schools', '0004_auto_20200224_0021'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('invoices', '0005_auto_20200223_2323'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='campus',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.CASCADE, to='schools.Campus', verbose_name='Campus'),
        ),
        migrations.AddField(
            model_name='invoice',
            name='invoiceToUser',
            field=models.ForeignKey(default=2, editable=False, on_delete=django.db.models.deletion.PROTECT, to=settings.AUTH_USER_MODEL, verbose_name='Mentor'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='invoice',
            name='event',
            field=models.ForeignKey(editable=False, on_delete=django.db.models.deletion.PROTECT, to='events.Event', verbose_name='Event'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='school',
            field=models.ForeignKey(blank=True, editable=False, null=True, on_delete=django.db.models.deletion.PROTECT, to='schools.School', verbose_name='School'),
        ),
    ]
