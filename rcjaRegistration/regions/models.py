from django.db import models
from common.models import *
from django.conf import settings

# **********MODELS**********

class State(CustomSaveDeleteModel):
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=30, unique=True)
    abbreviation = models.CharField('Abbreviation', max_length=3, unique=True)
    # Type fields
    typeRegistration = models.BooleanField('Registration', default=False, help_text='Use this state in the registration portal. Once enabled cannot be disabled.')
    typeGlobal = models.BooleanField('Global', default=False, help_text='Associate this state with global events.')
    typeWebsite = models.BooleanField('Website', default=False, help_text='Display this state on the public website.')
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
        elif level in ['viewall', 'eventmanager', 'billingmanager', 'schoolmanager', 'webeditor']:
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

        # Registration type incompatible with global type
        if self.typeRegistration:
            self.typeGlobal = False
        
        # Can only be one global state
        if self.typeGlobal:
            State.objects.exclude(pk=self.pk).update(typeGlobal=False)

    # *****Methods*****

    # *****Get Methods*****

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

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        if level in ['full', 'viewall', 'eventmanager', 'billingmanager']:
            return [
                'view',
            ]
        
        return []

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return self.name

    # *****CSV export methods*****

    # *****Email methods***** 
