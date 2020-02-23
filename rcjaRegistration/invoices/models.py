from django.db import models
from common.models import *
from django.conf import settings

# **********MODELS**********

class InvoiceGlobalSettings(models.Model):
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    invoiceFromName = models.CharField('Invoice from name', max_length=50)
    invoiceFromDetails = models.TextField('Invoice from details')

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Invoice settings'

    # Allow only one instance of model
    def clean(self):
        if InvoiceGlobalSettings.objects.exclude(pk=self.pk).exists():
            raise(ValidationError('May only be one global settings object'))

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return 'Invoice settings'

class Invoice(models.Model):
    # Foreign keys
    school = models.ForeignKey('schools.School', verbose_name='School', on_delete=models.PROTECT)
    event = models.ForeignKey('events.Event', verbose_name = 'Event', on_delete=models.PROTECT)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    invoicedDate = models.DateField('Invoiced date', null=True, blank=True) # Set when invoice first viewed
    purchaseOrderNumber = models.CharField('Purchase order number', max_length=30, blank=True, null=True)
    notes = models.TextField('Notes', blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Invoice'
        unique_together = ('school', 'event')
        ordering = ['event', 'school']

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        if level == 'full':
            return [
                'add',
                'view',
                'change',
                'delete'
            ]
        elif level == 'billingmanager':
            return [
                'add',
                'view',
                'change',
                'delete'
            ]
        elif level in ['viewall']:
            return [
                'view',
            ]
        
        return []

    # Used in state coordinator permission checking
    def getState(self):
        return self.event.state

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def invoiceAmount(self):
        from teams.models import Team
        return self.event.entryFee * Team.objects.filter(event=self.event, school=self.school).count()
    invoiceAmount.short_description = 'Invoice amount'

    def amountPaid(self):
        return sum(self.invoicepayment_set.values_list('amountPaid', flat=True))
    amountPaid.short_description = 'Amount paid'

    def amountDue(self):
        return self.invoiceAmount() - self.amountPaid()
    amountDue.short_description = 'Amount due'

    def __str__(self):
        return f'{self.event}: {self.school}'

    # *****CSV export methods*****

    # *****Email methods*****

class InvoicePayment(models.Model):
    # Foreign keys
    invoice = models.ForeignKey(Invoice, verbose_name='Invoice', on_delete=models.PROTECT)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    amountPaid = models.PositiveIntegerField('Amount paid')
    datePaid = models.DateField('Date paid')

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Payment'
        ordering = ['invoice', 'datePaid']

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return f'{self.invoice}: {self.datePaid}'

    # *****CSV export methods*****

    # *****Email methods*****
