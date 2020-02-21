from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template import loader
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist

import datetime

from .models import *

@login_required
def invoice(request):
    return render(request,'events/invoiceTemplate.html')
