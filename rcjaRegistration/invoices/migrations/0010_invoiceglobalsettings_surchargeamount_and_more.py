# Generated by Django 4.2.4 on 2023-10-03 13:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('invoices', '0009_invoice_cache_amountgst_unrounded_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoiceglobalsettings',
            name='surchargeAmount',
            field=models.FloatField(default=0, help_text='Amount excludes GST, GST will be added automatically.', verbose_name='Surcharge amount'),
        ),
        migrations.AddField(
            model_name='invoiceglobalsettings',
            name='surchargeEventDescription',
            field=models.CharField(blank=True, help_text='Appears on the event page below the surcharge amount.', max_length=200, verbose_name='Surcharge event page description'),
        ),
        migrations.AddField(
            model_name='invoiceglobalsettings',
            name='surchargeInvoiceDescription',
            field=models.CharField(blank=True, help_text='Appears in small text below the surcharge name on the invoice.', max_length=70, verbose_name='Surcharge invoice description'),
        ),
        migrations.AddField(
            model_name='invoiceglobalsettings',
            name='surchargeName',
            field=models.CharField(default='Surcharge', help_text='Name of the surcharge on the invoice.', max_length=30, verbose_name='Surcharge name'),
        ),
    ]
