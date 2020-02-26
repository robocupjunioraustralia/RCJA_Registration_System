from django.db import models
from common.models import *
from django.conf import settings

# **********MODELS**********

class State(CustomSaveDeleteModel):
    # Foreign keys
    treasurer = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Treasurer', on_delete=models.PROTECT, related_name='+')
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=20, unique=True)
    abbreviation = models.CharField('Abbreviation', max_length=3, unique=True)
    # Bank details
    bankAccountName = models.CharField('Bank Account Name', max_length=200, blank=True, null=True)
    bankAccountBSB = models.CharField('Bank Account BSB', max_length=7, blank=True, null=True)
    bankAccountNumber = models.CharField('Bank Account Number', max_length=10, blank=True, null=True)
    paypalEmail = models.EmailField('PayPal email', blank=True)
    # Defaults
    defaultEventDetails = models.TextField('Default event details', blank=True)
    invoiceMessage = models.TextField('Invoice message', blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'State'
        ordering = ['name']

    def clean(self):
        errors = []

        # Case insenstive abbreviation and name unique check
        if State.objects.filter(name__iexact=self.name).exclude(pk=self.pk).exists():
            errors.append(ValidationError('State with this name exists.'))

        if State.objects.filter(abbreviation__iexact=self.abbreviation).exclude(pk=self.pk).exists():
            errors.append(ValidationError('State with this abbreviation exists.'))

        # Raise any errors
        if errors:
            raise ValidationError(errors)

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        if level == 'full':
            return [
                'view',
                'change'
            ]
        elif level in ['viewall', 'eventmanager', 'billingmanager']:
            return [
                'view',
            ]
        
        return []

    # Used in state coordinator permission checking
    def getState(self):
        return self

    # *****Save & Delete Methods*****

    def preSave(self):
        self.abbreviation = self.abbreviation.upper()

    # *****Methods*****

    # *****Get Methods*****

    def treasurerName(self):
        return self.treasurer.fullname_or_email()
    treasurerName.short_description = 'Treasurer'

    def __str__(self):
        return self.name

    # *****CSV export methods*****

    # *****Email methods*****

class Region(models.Model):
    # Foreign keys
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=30, unique=True)
    description = models.CharField('Description', max_length=200, blank=True, null=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Region'
        ordering = ['name']

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return self.name

    # *****CSV export methods*****

    # *****Email methods***** 
