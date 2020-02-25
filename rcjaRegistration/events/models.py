from django.db import models
from common.models import *
from django.conf import settings

# **********MODELS**********

class Division(models.Model):
    # Foreign keys
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=20, unique=True)
    description = models.CharField('Description', max_length=200, blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Division'
        ordering = ['name']

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
        return self.name

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
    maxMembersPerTeam = models.PositiveIntegerField('Max members per team')
    # Dates
    startDate = models.DateField('Event start date')
    endDate = models.DateField('Event end date')
    registrationsOpenDate = models.DateField('Registrations open date')
    registrationsCloseDate = models.DateField('Registration close date')
    # Event details
    entryFee = models.PositiveIntegerField('Entry fee')
    availableDivisions = models.ManyToManyField(Division, verbose_name='Available divisions', blank=True)
    directEnquiriesTo = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Direct enquiries to', on_delete=models.PROTECT)
    location = models.TextField('Location', blank=True)
    eventDetails = models.TextField('Event details', blank=True)
    additionalInvoiceMessage = models.TextField('Additional invoice message', blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Event'
        unique_together = ('year', 'state', 'name')
        ordering = ['-startDate']

    def clean(self):
        errors = []
        # Check required fields are not None
        checkRequiredFieldsNotNone(self, ['startDate', 'endDate', 'registrationsOpenDate', 'registrationsCloseDate'])

        # Check close and end date after start dates
        if self.startDate > self.endDate:
            errors.append(ValidationError('Start date must not be after end date'))

        if self.registrationsOpenDate > self.registrationsCloseDate:
            errors.append(ValidationError('Registration open date must not be after registration close date'))

        if self.registrationsCloseDate >= self.startDate:
            errors.append(ValidationError('Registration close date must be before event start date'))
    
        # Raise any errors
        if errors:
            raise ValidationError(errors)

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


