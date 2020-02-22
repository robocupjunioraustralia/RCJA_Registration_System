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
    enteredDivisions = Division.objects.filter(team__school__invoice=invoice)

    context = {
        'invoice': invoice,
        'enteredDivisions': enteredDivisions
    }

    return render(request, 'invoices/invoiceDetail.html', context)
