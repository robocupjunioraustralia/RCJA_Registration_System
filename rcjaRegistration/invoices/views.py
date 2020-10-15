from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError, PermissionDenied
from django.urls import reverse

from django.http import JsonResponse
from django.http import HttpResponseForbidden, HttpResponseBadRequest
import datetime

from .models import InvoiceGlobalSettings, Invoice
from events.models import Division, Event
from schools.models import Campus

@login_required
def summary(request):
    invoices = Invoice.invoicesForUser(request.user)

    context = {
        'user': request.user,
        'invoices': invoices,
        'showCampusColumn': Campus.objects.filter(school__schooladministrator__user=request.user).exists(),
    }

    return render(request, 'invoices/summary.html', context)

def mentorInvoicePermissions(request, invoice):
    return request.user.schooladministrator_set.filter(school=invoice.school).exists() or invoice.invoiceToUser == request.user

def coordinatorInvoiceDetailsPermissions(request, invoice):
    from coordination.adminPermissions import checkStatePermissions
    return checkStatePermissions(request, invoice, 'view')

@login_required
def details(request, invoiceID):
    # Get invoice
    invoice = get_object_or_404(Invoice, pk=invoiceID)
    invoiceSettings = get_object_or_404(InvoiceGlobalSettings)

    # Check permissions
    mentor = mentorInvoicePermissions(request, invoice)
    coordinator = coordinatorInvoiceDetailsPermissions(request, invoice)
    if not (mentor or coordinator):
        raise PermissionDenied("You do not have permission to view this invoice")

    # Set invoiced date
    if mentor and invoice.invoicedDate is None:
        invoice.invoicedDate = datetime.datetime.today().date()
        invoice.save(update_fields=['invoicedDate'])

    context = {
        'invoice': invoice,
        'invoiceSettings': invoiceSettings,
        'currentDate': datetime.datetime.today().date,
    }

    return render(request, 'invoices/details.html', context)

@login_required
def paypal(request, invoiceID):
    # Get invoice
    invoice = get_object_or_404(Invoice, pk=invoiceID)

    # Check permissions
    mentor = mentorInvoicePermissions(request, invoice)
    if not mentor:
        raise PermissionDenied("You do not have permission to view this invoice")

    # Check paypal email is set for this state
    if not invoice.paypalAvailable():
        return HttpResponseForbidden('PayPal not enabled for this invoice')

    # Set invoiced date
    if mentor and invoice.invoicedDate is None:
        invoice.invoicedDate = datetime.datetime.today()
        invoice.save(update_fields=['invoicedDate'])

    if invoice.campus:
        schoolCampusString = f'{invoice.school}, {invoice.campus}'
    elif invoice.school:
        schoolCampusString = f'{invoice.school}'
    else:
        schoolCampusString = 'Independent'

    context = {
        'invoice': invoice,
        'paypalDescription': f"{invoice.invoiceNumber} - {invoice.event} - {schoolCampusString} - {invoice.invoiceToUser}",
    }

    return render(request, 'invoices/paypal.html', context)

@login_required
def setInvoiceTo(request, invoiceID):
    if request.method == 'POST':
        invoice = get_object_or_404(Invoice, pk=invoiceID)

        # Check permissions
        if not mentorInvoicePermissions(request, invoice):
            raise PermissionDenied("You do not have permission to view this invoice")
        
        invoice.invoiceToUser = request.user
        invoice.save(update_fields=['invoiceToUser'])

        return JsonResponse({'id':invoiceID, 'invoiceTo':request.user.fullname_or_email(), 'success':True})
    else:
        return HttpResponseForbidden()

@login_required
def setCampusInvoice(request, invoiceID):
    if request.method == 'POST':
        invoice = get_object_or_404(Invoice, pk=invoiceID)

        # Check permissions
        if not mentorInvoicePermissions(request, invoice):
            raise PermissionDenied("You do not have permission to view this invoice")

        # Check campus invoicing available
        if not invoice.campusInvoicingAvailable():
            return HttpResponseForbidden("Campus invoicing is not available for this event")

        # Create campus invoices for campuses that have teams entered in this event
        # This invoice object remains for teams without a campus
        from schools.models import Campus
        for campus in Campus.objects.filter(school=invoice.school, baseeventattendance__event=invoice.event).distinct():
            Invoice.objects.create(
                event=invoice.event,
                invoiceToUser=invoice.invoiceToUser,
                school=invoice.school,
                campus=campus,
            )

        return JsonResponse({'id':invoiceID, 'success':True})
    else:
        return HttpResponseForbidden()

@login_required
def editInvoicePOAJAX(request, invoiceID):
    if request.method == 'POST':
        invoice = get_object_or_404(Invoice, pk=invoiceID)

        # Check permissions
        if not mentorInvoicePermissions(request, invoice):
            raise PermissionDenied("You do not have permission to view this invoice")

        # Update invoice
        try:
            invoice.purchaseOrderNumber = request.POST["PONumber"]
            invoice.save(update_fields=['purchaseOrderNumber'])
        except KeyError:
            return HttpResponseBadRequest()

        return JsonResponse({'id':invoiceID,'number':request.POST["PONumber"], 'success':True})
        #IF PO NUMBERS NEED AN ERROR RESPONSE
        """
            return JsonResponse({
                'success': False,
                'errors': dict(form.errors.items())
            },status=400)
        """
    else:
        return HttpResponseForbidden()
