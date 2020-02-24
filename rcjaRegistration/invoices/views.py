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
    # Get invoice
    invoice = get_object_or_404(Invoice, pk=invoiceID)
    invoiceSettings = get_object_or_404(InvoiceGlobalSettings)

    # Check permissions
    if not (request.user.schooladministrator_set.filter(school=invoice.school).exists() or invoice.invoiceToUser == request.user):
        raise PermissionDenied("You do not have permission to view this invoice")

    # Set invoiced date
    if invoice.invoicedDate is None:
        invoice.invoicedDate = datetime.datetime.today()
        invoice.save()

    # Division details
    teams = invoice.teamsQueryset()
    enteredDivisions = Division.objects.filter(team__in=teams)

    divisionDetails = []
    overallTotalExclGST = 0
    overallTotalGST = 0
    overallTotalInclGST = 0

    for division in enteredDivisions:
        # Calculate values
        numberTeams = teams.filter(division=division).count()
        unitCost = invoice.event.entryFee
        totalExclGST = numberTeams * unitCost
        gst = 0.1 * totalExclGST
        totalInclGST = totalExclGST + gst

        # Update totals
        overallTotalExclGST += totalExclGST
        overallTotalGST += gst
        overallTotalInclGST += totalInclGST

        divisionDetails.append({
            'division': division,
            'numberTeams': numberTeams,
            'unitCost': unitCost,
            'totalExclGST': totalExclGST,
            'gst': gst,
            'totalInclGST': totalInclGST,
        })

    context = {
        'invoice': invoice,
        'invoiceSettings': invoiceSettings,
        'divisionDetails': divisionDetails,
        'overallTotalExclGST': overallTotalExclGST,
        'overallTotalGST': overallTotalGST,
        'overallTotalInclGST': overallTotalInclGST,
        'currentDate': datetime.datetime.today().date,
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
