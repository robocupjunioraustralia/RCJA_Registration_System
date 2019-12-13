from django.db import models

# Create your models here.

class State(models.Model):
    # Foreign keys
    treasurer = models.ForeignKey('auth.user', verbose_name='Treasurer', on_delete=models.PROTECT)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=20, unique=True)
    abbreviation = models.CharField('Short code', max_length=3, unique=True)
    # Bank details
    bankAccountName = models.CharField('Bank Account Name', max_length=200, blank=True, null=True)
    bankAccountBSB = models.PositiveIntegerField('Bank Account BSB', blank=True, null=True)
    bankAccountNumber = models.PositiveIntegerField('Bank Account Number', blank=True, null=True)
    paypalEmail = models.EmailField('PayPal email', blank=True)
    # Defaults
    defaultCompDetails = models.TextField('Default competition details', blank=True)
    invoiceMessage = models.TextField('Invoice message', blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'State'
        ordering = ['name']

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return self.name

    # *****CSV export methods*****

    # *****Email methods*****

class Division(models.Model):
    # Foreign keys
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    state = models.ForeignKey(State, verbose_name='State', on_delete=models.CASCADE, blank=True, null=True, help_text='Blank for global, available to all states')
    name = models.CharField('Name', max_length=20)
    description = models.CharField('Description', max_length=200, blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Division'
        ordering = ['state', 'name']

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

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return str(self.year)

    # *****CSV export methods*****

    # *****Email methods*****

class Competition(models.Model):
    # Foreign keys
    year = models.ForeignKey(Year, verbose_name='Year', on_delete=models.PROTECT)
    state = models.ForeignKey(State, verbose_name = 'State', on_delete=models.PROTECT)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=50)
    max_team_members = models.PositiveIntegerField('Max team members')
    # Dates
    startDate = models.DateField('Competition start date')
    endDate = models.DateField('Competition end date')
    registrationsOpenDate = models.DateField('Registrations open date')
    registrationsCloseDate = models.DateField('Registration close date')
    # Competition details
    entryFee = models.PositiveIntegerField('Entry fee')
    availableCompetitions = models.ManyToManyField(Division, verbose_name='Available division')
    directEnquiriesTo = models.ForeignKey('auth.user', verbose_name='Direct enquiries to', on_delete=models.PROTECT)
    location = models.TextField('Location', blank=True)
    compDetails = models.TextField('Competition details', blank=True)
    additionalInvoiceMessage = models.TextField('Additional invoice message', blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Competition'
        unique_together = ('year', 'state', 'name')
        ordering = ['year', 'state', '-startDate']

    # Check close and end date after start dates

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return f'{self.name} {self.year}'

    # *****CSV export methods*****

    # *****Email methods*****

class Invoice(models.Model):
    # Foreign keys
    school = models.ForeignKey('schools.School', verbose_name='School', on_delete=models.PROTECT)
    competition = models.ForeignKey(Competition, verbose_name = 'Competition', on_delete=models.PROTECT)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    purchaseOrderNumber = models.PositiveIntegerField('Purchase order number', blank=True, null=True)
    notes = models.TextField('Notes', blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Invoice'
        unique_together = ('school', 'competition')
        ordering = ['competition', 'school']

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def invoiceAmount(self):
        from teams.models import Team
        return self.competition.entryFee * Team.objects.filter(competition=self.competition, school=self.school).count()
    invoiceAmount.short_description = 'Invoice amount'

    def amountPaid(self):
        return sum(self.invoicepayment_set.values_list('amountPaid', flat=True))
    amountPaid.short_description = 'Amount paid'

    def amountDue(self):
        return self.invoiceAmount() - self.amountPaid()
    amountDue.short_description = 'Amount due'

    def __str__(self):
        return f'{self.competition}: {self.school}'

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
