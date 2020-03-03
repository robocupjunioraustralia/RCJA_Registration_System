"""common URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.urls import path, include
from . import views
app_name = 'invoices'

urlpatterns = [
    path('invoices', views.summary, name='summary'),
    path('invoices/<int:invoiceID>', views.details, name='details'),
    path('invoices/<int:invoiceID>/paypal', views.paypal, name='paypal'),
    path('invoices/<int:invoiceID>/setInvoiceTo', views.setInvoiceTo, name='setInvoiceTo'),
    path('invoices/<int:invoiceID>/setCampusInvoice', views.setCampusInvoice, name='setCampusInvoice'),
    path('invoices/<int:invoiceID>/setPONumber', views.editInvoicePOAJAX, name='invoicePOAJAX'),
]