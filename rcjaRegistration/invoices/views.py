from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

import datetime

from .models import *
from events.models import Division, Event

@login_required
def invoice(request, invoiceID):
    invoice = get_object_or_404(Invoice, pk=invoiceID)
    invoiceSettings = get_object_or_404(InvoiceGlobalSettings)
    enteredDivisions = Division.objects.filter(team__school__invoice=invoice)

    # Set invoiced date
    if invoice.invoicedDate is None:
        invoice.invoicedDate = datetime.datetime.today()
        invoice.save()

    context = {
        'invoice': invoice,
        'invoiceSettings': invoiceSettings,
        'enteredDivisions': enteredDivisions
    }

    return render(request, 'invoices/invoiceDetail.html', context)
