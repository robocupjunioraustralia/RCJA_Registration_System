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
    invoiceFooterMessage = models.TextField('Invoice footer message')

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

class Invoice(CustomSaveDeleteModel):
    # Foreign keys
    event = models.ForeignKey('events.Event', verbose_name = 'Event', on_delete=models.PROTECT, editable=False)

    # User and school foreign keys
    invoiceToUser = models.ForeignKey('users.User', verbose_name='Invoice to', on_delete=models.PROTECT, editable=False)
    school = models.ForeignKey('schools.School', verbose_name='School', on_delete=models.PROTECT, null=True, blank=True, editable=False)
    campus = models.ForeignKey('schools.Campus', verbose_name='Campus', on_delete=models.PROTECT, null=True, blank=True, editable=False)

    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)

    # Fields
    invoiceNumber = models.PositiveIntegerField('Invoice number', unique=True, editable=False)
    invoicedDate = models.DateField('Invoiced date', null=True, blank=True) # Set when invoice first viewed
    purchaseOrderNumber = models.CharField('Purchase order number', max_length=30, blank=True, null=True)
    notes = models.TextField('Notes', blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Invoice'
        constraints = [
            models.UniqueConstraint(fields=['event', 'school'], condition=Q(campus=None), name='event_school'),
            models.UniqueConstraint(fields=['event', 'invoiceToUser'], condition=Q(school=None), name='event_user'),
            models.UniqueConstraint(fields=['event', 'school', 'campus'], name='event_school_campus'),
        ]
        ordering = ['-invoiceNumber']

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

    def preSave(self):
        if self.invoiceNumber is None:
            try:
                self.invoiceNumber = Invoice.objects.latest('invoiceNumber').invoiceNumber + 1
            except Invoice.DoesNotExist:
                self.invoiceNumber = 1

    # *****Methods*****

    # *****Get Methods*****

    # Campus

    # Returns true if campus based invoicing enabled for this school for this event
    def campusInvoicingEnabled(self):
        if not self.school:
            return False

        # Check no payments made
        if self.invoicepayment_set.exists():
            return False

        # Check if at least one invoice has campus field set
        return Invoice.objects.filter(school=self.school, event=self.event, campus__isnull=False).exists()

    # Returns true if teams with campus for this school and event exists and campus invoicing not already enabled
    def campusInvoicingAvailable(self):
        from teams.models import Team
        if not self.school:
            return False

        if self.campusInvoicingEnabled():
            return False

        return Team.objects.filter(school=self.school, event=self.event, campus__isnull=False).exists()

    # Teams

    # Queryset of teams covered by this invoice
    def teamsQueryset(self):
        from teams.models import Team
        if self.campusInvoicingEnabled():
            # Filter by school and campus
            return Team.objects.filter(event=self.event, school=self.school, campus=self.campus)

        elif self.school:
            # If school but campuses not enableed filter by school
            return Team.objects.filter(event=self.event, school=self.school)

        else:
            # If no school filter by user
            return Team.objects.filter(event=self.event, mentorUser=self.invoiceToUser, school=None)

    # Totals

    def invoiceAmount(self):
        return self.event.entryFee * self.teamsQueryset().count()
    invoiceAmount.short_description = 'Invoice amount'

    def amountPaid(self):
        return sum(self.invoicepayment_set.values_list('amountPaid', flat=True))
    amountPaid.short_description = 'Amount paid'

    def amountDueExclGST(self):
        return self.invoiceAmount() - self.amountPaid()
    amountDueExclGST.short_description = 'Amount due (ex GST)'

    def amountDueInclGST(self):
        return self.amountDueExclGST() * 1.1
    amountDueInclGST.short_description = 'Amount due (incl GST)'

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
