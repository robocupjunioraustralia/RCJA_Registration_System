from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, PermissionDenied
from django.urls import reverse

import datetime

from .models import *
from events.models import Division, Event

@login_required
def summary(request):
    invoices = Invoice.objects.filter(Q(invoiceToUser=request.user) | Q(school__schooladministrator__user=request.user))

    context = {
        'user': request.user,
        'invoices': invoices,
    }

    return render(request, 'invoices/invoiceSummary.html', context)


@login_required
def detail(request, invoiceID):
    invoice = get_object_or_404(Invoice, pk=invoiceID)
    invoiceSettings = get_object_or_404(InvoiceGlobalSettings)
    enteredDivisions = Division.objects.filter(team__school__invoice=invoice)

    # Check permissions
    if not (request.user.schooladministrator_set.filter(school=invoice.school).exists() or invoice.invoiceToUser == request.user):
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

@login_required
def setInvoiceTo(request, invoiceID):
    invoice = get_object_or_404(Invoice, pk=invoiceID)

    # Check permissions
    if not (request.user.schooladministrator_set.filter(school=invoice.school).exists() or invoice.invoiceToUser == request.user):
        raise PermissionDenied("You do not have permission to view this invoice")
    
    invoice.invoiceToUser = request.user
    invoice.save(update_fields=['invoiceToUser'])

    return redirect(reverse('invoices:summary'))
