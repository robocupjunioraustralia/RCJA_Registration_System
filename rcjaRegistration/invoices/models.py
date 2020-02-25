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

        # Check if at least one invoice has campus field set
        return Invoice.objects.filter(school=self.school, event=self.event, campus__isnull=False).exists()

    # Returns true if teams with campus for this school and event exists and campus invoicing not already enabled
    def campusInvoicingAvailable(self):
        from teams.models import Team
        if not self.school:
            return False

        if self.campusInvoicingEnabled():
            return False

        # Check no payments made
        if self.invoicepayment_set.exists():
            return False

        return Team.objects.filter(school=self.school, event=self.event, campus__isnull=False).exists()

    # Teams

    # Queryset of teams covered by this invoice
    def includedTeams(self):
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

    # Invoice items

    def includedDivisions(self):
        from events.models import Division
        return Division.objects.filter(team__in=self.includedTeams()).distinct()

    def invoiceItems(self):
        from events.models import AvailableDivision
        from teams.models import Student
        invoiceItems = []

        for division in self.includedDivisions():
            # Get available division
            try:
                availableDivision = self.event.availabledivision_set.get(division=division)
            except AvailableDivision.DoesNotExist:
                availableDivision = None

            teams = self.includedTeams().filter(division=division)

            # Get unit cost, use availableDivision value if present, otherwise use value from event
            unitCost = self.event.event_defaultEntryFee
            useDivision = False
            if availableDivision and availableDivision.division_entryFee is not None:
                unitCost = availableDivision.division_entryFee
                useDivision = True

            # Get quantity calculation method
            if useDivision:
                quantityMethod = availableDivision.division_billingType

            else:
                quantityMethod = self.event.event_billingType

            # Get quantity
            quantity = 0
            if quantityMethod == 'team':
                quantity = teams.count()

            elif quantityMethod == 'student':
                quantity = Student.objects.filter(team__in=teams).count()

            # Calculate values
            totalExclGST = quantity * unitCost
            gst = 0.1 * totalExclGST
            totalInclGST = totalExclGST + gst

            # Quantity string
            quantityString = f"{quantity} {quantityMethod if quantity <= 1 else quantityMethod + 's'}"

            invoiceItems.append({
                'name': division.name,
                'quantity': quantity,
                'quantityString': quantityString,
                'unitCost': unitCost,
                'totalExclGST': totalExclGST,
                'gst': gst,
                'totalInclGST': totalInclGST,
            })
        
        return invoiceItems

    # Totals

    def amountPaid(self):
        return sum(self.invoicepayment_set.values_list('amountPaid', flat=True))
    amountPaid.short_description = 'Amount paid'

    def amountGST(self):
        return sum([item['gst'] for item in self.invoiceItems()])
    amountGST.short_description = 'GST'

    # Invoice amount

    def invoiceAmountExclGST(self):
        return sum([item['totalExclGST'] for item in self.invoiceItems()])
    invoiceAmountExclGST.short_description = 'Invoice amount (ex GST)'

    def invoiceAmountInclGST(self):
        return sum([item['totalInclGST'] for item in self.invoiceItems()])
    invoiceAmountInclGST.short_description = 'Invoice amount (incl GST)'

    # Amount due

    def amountDueExclGST(self):
        return self.invoiceAmountExclGST() - self.amountPaid()
    amountDueExclGST.short_description = 'Amount due (ex GST)'

    def amountDueInclGST(self):
        return self.invoiceAmountInclGST() - self.amountPaid()
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
