from django.db import models
from common.models import *

# **********MODELS**********

class Division(models.Model):
    # Foreign keys
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    state = models.ForeignKey('regions.State', verbose_name='State', on_delete=models.CASCADE, blank=True, null=True, help_text='Blank for global, available to all states') # Do we want this, or just make it fully global?
    name = models.CharField('Name', max_length=20)
    description = models.CharField('Description', max_length=200, blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Division'
        ordering = ['state', 'name']

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        if level in ['full', 'viewall', 'eventmanager']:
            return [
                'view',
            ]
        
        return []

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return self.name if self.state is None else f'{self.state}: {self.name}'

    # *****CSV export methods*****

    # *****Email methods*****

class Year(models.Model):
    # Fields and primary key
    year = models.PositiveIntegerField('Year', primary_key=True)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields

    # *****Meta and clean*****
    class Meta:
        verbose_name = "Year"
        ordering = ['-year']

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        if level in ['full', 'viewall', 'eventmanager']:
            return [
                'view',
            ]
        
        return []

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return str(self.year)

    # *****CSV export methods*****

    # *****Email methods*****

class Event(models.Model):
    # Foreign keys
    year = models.ForeignKey(Year, verbose_name='Year', on_delete=models.PROTECT)
    state = models.ForeignKey('regions.State', verbose_name = 'State', on_delete=models.PROTECT)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=50)
    max_team_members = models.PositiveIntegerField('Max team members')
    # Dates
    startDate = models.DateField('Event start date')
    endDate = models.DateField('Event end date')
    registrationsOpenDate = models.DateField('Registrations open date')
    registrationsCloseDate = models.DateField('Registration close date')
    # Event details
    entryFee = models.PositiveIntegerField('Entry fee')
    availableDivisions = models.ManyToManyField(Division, verbose_name='Available divisions', blank=True)
    directEnquiriesTo = models.ForeignKey('auth.user', verbose_name='Direct enquiries to', on_delete=models.PROTECT)
    location = models.TextField('Location', blank=True)
    compDetails = models.TextField('Event details', blank=True)
    additionalInvoiceMessage = models.TextField('Additional invoice message', blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Event'
        unique_together = ('year', 'state', 'name')
        ordering = ['year', 'state', '-startDate']

    # Check close and end date after start dates


    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        if level in ['full', 'eventmanager']:
            return [
                'add',
                'view',
                'change',
                'delete'
            ]
        elif level in ['viewall', 'billingmanager']:
            return [
                'view',
            ]
        
        return []

    # Used in state coordinator permission checking
    def getState(self):
        return self.state

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return f'{self.name} {self.year} ({self.state.abbreviation})'

    # *****CSV export methods*****

    # *****Email methods*****

class Invoice(models.Model):
    # Foreign keys
    school = models.ForeignKey('schools.School', verbose_name='School', on_delete=models.PROTECT)
    event = models.ForeignKey(Event, verbose_name = 'Event', on_delete=models.PROTECT)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
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
