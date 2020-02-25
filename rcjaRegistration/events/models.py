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
    eventTypeChoices = (('competition', 'Competition'), ('workshop', 'Workshop'))
    eventType = models.CharField('Event type', max_length=15, choices=eventTypeChoices, default='competition', help_text='Competition is standard event with teams and students. Workshop has no teams or students, just workshop attendees.')

    # Dates
    startDate = models.DateField('Event start date')
    endDate = models.DateField('Event end date')
    registrationsOpenDate = models.DateField('Registrations open date')
    registrationsCloseDate = models.DateField('Registration close date')

    # Team details
    event_maxMembersPerTeam = models.PositiveIntegerField('Max members per team')
    event_maxTeamsPerSchool = models.PositiveIntegerField('Max teams per school', null=True, blank=True, help_text='Leave blank for no limit. Only enforced on the mentor signup page, can be overridden in the admin portal.')
    event_maxTeamsForEvent = models.PositiveIntegerField('Max teams for event', null=True, blank=True, help_text='Leave blank for no limit. Only enforced on the mentor signup page, can be overridden in the admin portal.')

    # Billing details
    billingTypeChoices = (('team', 'By team'), ('student', 'By student'))
    event_billingType = models.CharField('Billing type', max_length=15, choices=billingTypeChoices, default='team')
    event_defaultEntryFee = models.PositiveIntegerField('Default entry fee')
    event_specialRateNumber = models.PositiveIntegerField('Special rate number', null=True, blank=True, help_text="The number of teams/ students specified will be billed at this rate. Subsequent teams/ students will be billed at the default rate. Leave blank for no special rate.")
    event_specialRateFee = models.PositiveIntegerField('Special rate fee', null=True, blank=True)

    # Event details
    directEnquiriesTo = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Direct enquiries to', on_delete=models.PROTECT, help_text="This person's name and email will appear on the event page")
    eventDetails = models.TextField('Event details', blank=True)
    location = models.TextField('Location', blank=True)
    additionalInvoiceMessage = models.TextField('Additional invoice message', blank=True, help_text='This appears below the state based invoice message on the invoice.')

    # Available divisions
    availableDivisions = models.ManyToManyField(Division, verbose_name='Available divisions', through='AvailableDivision')
  
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

class AvailableDivision(models.Model):
    # Foreign keys
    event = models.ForeignKey(Event, verbose_name='Event', on_delete=models.CASCADE)
    division = models.ForeignKey(Division, verbose_name='Division', on_delete=models.PROTECT)

    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)

    # Team details
    division_maxMembersPerTeam = models.PositiveIntegerField('Max members per team', null=True, blank=True, help_text='Leave blank for no limit. Will override limit on event.')
    division_maxTeamsPerSchool = models.PositiveIntegerField('Max teams per school', null=True, blank=True, help_text='Leave blank for no limit. Will override limit on event.')
    division_maxTeamsForDivision = models.PositiveIntegerField('Max teams for division', null=True, blank=True, help_text='Leave blank for no limit. Will override limit on event.')

    # Billing details
    billingTypeChoices = (('event', 'Event settings'), ('team', 'By team'), ('student', 'By student'))
    division_billingType = models.CharField('Billing type', max_length=15, choices=billingTypeChoices, default='event')
    division_entryFee = models.PositiveIntegerField('Default entry fee')

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Available Division'
        unique_together = ('event', 'division')
        ordering = ['event', 'division']

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
        return self.event.state

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return str(self.division)

    # *****CSV export methods*****

    # *****Email methods*****
