from django.db import models

# Create your models here.

class State(models.Model):
    # Foreign keys
    treasurer = models.ForeignKey('auth.user', verbose_name='Treasurer', on_delete=models.PROTECT)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=20)
    short_code = models.CharField('Short code', max_length=3)
    # Bank details
    bank_account_name = models.CharField('Bank Account Name', max_length=200, blank=True, null=True)
    bank_account_bsb = models.PositiveIntegerField('Bank Account BSB', blank=True, null=True)
    bank_account_number = models.PositiveIntegerField('Bank Account Number', blank=True, null=True)
    bank_paypal_email = models.EmailField('PayPal email')
    # Defaults
    default_comp_details = models.TextField('Default competition details', blank=True)
    default_invoice_message = models.TextField('Default invoice message', blank=True)


    # *****Meta and clean*****
    def __str__(self):
        return self.name

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    # *****CSV export methods*****

    # *****Email methods*****

class Division(models.Model):
    # Foreign keys
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=20)
    description = models.CharField('Description', max_length=200, blank=True, null=True)

    # *****Meta and clean*****
    def __str__(self):
        return self.name

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    # *****CSV export methods*****

    # *****Email methods*****

class Competition(models.Model):
    # Foreign keys
    division = models.ForeignKey(Division, verbose_name='Division', on_delete=models.PROTECT)
    state = models.ForeignKey(State, verbose_name = 'State', on_delete=models.PROTECT)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=50)
    max_team_members = models.PositiveIntegerField('Max team members')
    # Dates
    comp_start_date = models.DateField('Competition start date')
    comp_end_date = models.DateField('Competition end date')
    registrations_open_date = models.DateField('Registrations open date')
    registrations_close_date = models.DateField('Registration close date')
    # Competition details
    location = models.TextField('Location')
    comp_details = models.TextField('Competition details', blank=True)


    # *****Meta and clean*****
    def __str__(self):
        return self.name

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    # *****CSV export methods*****

    # *****Email methods*****
