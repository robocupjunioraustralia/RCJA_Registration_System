from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, PermissionDenied

import datetime

from .models import *
from events.models import Division, Event

@login_required
def summary(request):

    context = {
        'invoices': request.user.invoice_set.all()
    }

    return render(request, 'invoices/invoiceSummary.html', context)


@login_required
def detail(request, invoiceID):
    invoice = get_object_or_404(Invoice, pk=invoiceID)
    invoiceSettings = get_object_or_404(InvoiceGlobalSettings)
    enteredDivisions = Division.objects.filter(team__school__invoice=invoice)

    # Check permissions
    if not request.user.schooladministrator_set.filter(school=invoice.school).exists():
        raise PermissionDenied("You do not have permission to view this invoice")

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
