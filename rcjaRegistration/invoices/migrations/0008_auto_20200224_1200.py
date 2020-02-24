# Generated by Django 2.2.10 on 2020-02-24 01:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0007_auto_20200224_0127'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='invoice',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='invoice',
            constraint=models.UniqueConstraint(condition=models.Q(campus=None), fields=('event', 'school'), name='event_school'),
        ),
        migrations.AddConstraint(
            model_name='invoice',
            constraint=models.UniqueConstraint(condition=models.Q(school=None), fields=('event', 'invoiceToUser'), name='event_user'),
        ),
        migrations.AddConstraint(
            model_name='invoice',
            constraint=models.UniqueConstraint(fields=('event', 'school', 'campus'), name='event_school_campus'),
        ),
    ]
