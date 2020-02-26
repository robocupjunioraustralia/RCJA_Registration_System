# Generated by Django 2.2.10 on 2020-02-26 01:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creationDateTime', models.DateTimeField(auto_now_add=True, verbose_name='Creation date')),
                ('updatedDateTime', models.DateTimeField(auto_now=True, verbose_name='Last modified date')),
                ('invoiceNumber', models.PositiveIntegerField(editable=False, unique=True, verbose_name='Invoice number')),
                ('invoicedDate', models.DateField(blank=True, null=True, verbose_name='Invoiced date')),
                ('purchaseOrderNumber', models.CharField(blank=True, max_length=30, null=True, verbose_name='Purchase order number')),
                ('notes', models.TextField(blank=True, verbose_name='Notes')),
            ],
            options={
                'verbose_name': 'Invoice',
                'ordering': ['-invoiceNumber'],
            },
        ),
        migrations.CreateModel(
            name='InvoiceGlobalSettings',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creationDateTime', models.DateTimeField(auto_now_add=True, verbose_name='Creation date')),
                ('updatedDateTime', models.DateTimeField(auto_now=True, verbose_name='Last modified date')),
                ('invoiceFromName', models.CharField(max_length=50, verbose_name='Invoice from name')),
                ('invoiceFromDetails', models.TextField(verbose_name='Invoice from details')),
                ('invoiceFooterMessage', models.TextField(verbose_name='Invoice footer message')),
            ],
            options={
                'verbose_name': 'Invoice settings',
            },
        ),
        migrations.CreateModel(
            name='InvoicePayment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('creationDateTime', models.DateTimeField(auto_now_add=True, verbose_name='Creation date')),
                ('updatedDateTime', models.DateTimeField(auto_now=True, verbose_name='Last modified date')),
                ('amountPaid', models.PositiveIntegerField(verbose_name='Amount paid')),
                ('datePaid', models.DateField(verbose_name='Date paid')),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, to='invoices.Invoice', verbose_name='Invoice')),
            ],
            options={
                'verbose_name': 'Payment',
                'ordering': ['invoice', 'datePaid'],
            },
        ),
    ]