from django.db import models
from common.models import *
from django.conf import settings

# **********MODELS**********

def eventCoordinatorEditPermisisons(level):
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

def eventCoordinatorViewPermissions(level):
    if level in ['full', 'viewall', 'eventmanager']:
        return [
            'view',
        ]

    return []

class DivisionCategory(models.Model):
    # Foreign keys
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=60, unique=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Division Category'
        verbose_name_plural = 'Division Categories'
        ordering = ['name']

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        return eventCoordinatorViewPermissions(level)

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
    name = models.CharField('Name', max_length=60, unique=True)
    description = models.CharField('Description', max_length=200, blank=True)
    category = models.ForeignKey(DivisionCategory, verbose_name='Category', on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey('regions.State', verbose_name='State', on_delete=models.PROTECT, null=True, blank=True, help_text='Leave blank for a global division. Global divisions are only editable by global administrators.')

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Division'
        ordering = ['name']

    def clean(self):
        errors = []

        # Check changing state won't cause conflict
        if self.state:
            if self.team_set.exclude(event__state=self.state).exists():
                errors.append(ValidationError('State not compatible with existing teams in this division'))

            if self.availabledivision_set.exclude(event__state=self.state).exists():
                errors.append(ValidationError('State not compatible with existing available division for this division'))

        # Raise any errors
        if errors:
            raise ValidationError(errors)

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        return eventCoordinatorEditPermisisons(level)

    # Used in state coordinator permission checking
    def getState(self):
        return self.state

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        if self.state:
            return f'{self.name} ({self.state})'
        return self.name

    # *****CSV export methods*****

    # *****Email methods*****

class Venue(models.Model):
    # Foreign keys
    state = models.ForeignKey('regions.State', verbose_name='State', on_delete=models.PROTECT)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=60)
    address = models.TextField('Address', blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Venue'
        ordering = ['name']
        unique_together = ('name', 'state')

    def clean(self):
        errors = []

        # Check changing state won't cause conflict
        if self.event_set.exclude(state=self.state).exists():
            errors.append(ValidationError('State not compatible with existing events with this venue'))

        # Raise any errors
        if errors:
            raise ValidationError(errors)

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        return eventCoordinatorEditPermisisons(level)

    # Used in state coordinator permission checking
    def getState(self):
        return self.state

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
        return eventCoordinatorViewPermissions(level)

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return str(self.year)

    # *****CSV export methods*****

    # *****Email methods*****

class Event(CustomSaveDeleteModel):
    # Foreign keys
    year = models.ForeignKey(Year, verbose_name='Year', on_delete=models.PROTECT)
    state = models.ForeignKey('regions.State', verbose_name = 'State', on_delete=models.PROTECT)
    globalEvent = models.BooleanField('Global event', default=False, help_text='Global events appear to users as not belonging to a state. Recommeneded for national events. Billing still uses state based settings.')

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
    maxMembersPerTeam = models.PositiveIntegerField('Max members per team', help_text="Resets to 0 for workshops")
    event_maxTeamsPerSchool = models.PositiveIntegerField('Max teams per school', null=True, blank=True, help_text='Leave blank for no limit. Only enforced on the mentor signup page, can be overridden in the admin portal.')
    event_maxTeamsForEvent = models.PositiveIntegerField('Max teams for event', null=True, blank=True, help_text='Leave blank for no limit. Only enforced on the mentor signup page, can be overridden in the admin portal.')

    # Billing details
    entryFeeIncludesGST = models.BooleanField('Includes GST', default=True, help_text='Whether the prices specified on this page are GST inclusive or exclusive.')
    billingTypeChoices = (('team', 'By team'), ('student', 'By student'))
    event_billingType = models.CharField('Billing type', max_length=15, choices=billingTypeChoices, default='team')
    event_defaultEntryFee = models.PositiveIntegerField('Default entry fee')
    event_specialRateNumber = models.PositiveIntegerField('Special rate number', null=True, blank=True, help_text="The number of teams/ students specified will be billed at this rate. Subsequent teams/ students will be billed at the default rate. Leave blank for no special rate.")
    event_specialRateFee = models.PositiveIntegerField('Special rate fee', null=True, blank=True)
    paymentDueDate = models.DateField('Payment due date', null=True, blank=True)

    # Event details
    directEnquiriesTo = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Direct enquiries to', on_delete=models.PROTECT, help_text="This person's name and email will appear on the event page")
    venue = models.ForeignKey(Venue, verbose_name='Venue', on_delete=models.PROTECT, null=True, blank=True)
    eventDetails = models.TextField('Event details', blank=True)
    additionalInvoiceMessage = models.TextField('Additional invoice message', blank=True, help_text='This appears below the state based invoice message on the invoice.')

    # Available divisions
    divisions = models.ManyToManyField(Division, verbose_name='Available divisions', through='AvailableDivision')

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Event'
        unique_together = ('year', 'state', 'name')
        ordering = ['-startDate']

    def clean(self):
        errors = []
        # Check required fields are not None
        checkRequiredFieldsNotNone(self, ['state', 'startDate', 'endDate', 'registrationsOpenDate', 'registrationsCloseDate'])

        # Check close and end date after start dates
        if self.startDate > self.endDate:
            errors.append(ValidationError('Start date must not be after end date'))

        if self.registrationsOpenDate > self.registrationsCloseDate:
            errors.append(ValidationError('Registration open date must not be after registration close date'))

        if self.registrationsCloseDate >= self.startDate:
            errors.append(ValidationError('Registration close date must be before event start date'))

        # Validate billing settings
        if (self.event_specialRateNumber is None) != (self.event_specialRateFee is None):
            errors.append(ValidationError('Both special rate number and fee must either be blank or not blank'))

        if (self.event_specialRateNumber is not None or self.event_specialRateFee is not None) and self.availabledivision_set.exclude(division_billingType='event').exists():
            errors.append(ValidationError('Special rate billing on event is incompatible with division based billing settings'))

        if (self.event_specialRateNumber is not None or self.event_specialRateFee is not None) and self.event_billingType != 'team':
            errors.append(ValidationError('Special billing rate only available for team billing'))

        # Validate division states
        if self.pk:
            if self.divisions.exclude(Q(state=None) | Q(state=self.state)).exists():
                errors.append(ValidationError('All division states must match event state'))

        # Validate venue state
        if self.venue and self.venue.state != self.state:
            errors.append(ValidationError('Venue must be from same state as event'))

        # Raise any errors
        if errors:
            raise ValidationError(errors)

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        return eventCoordinatorEditPermisisons(level)

    # Used in state coordinator permission checking
    def getState(self):
        return self.state

    # *****Save & Delete Methods*****

    def preSave(self):
        if self.eventType == 'workshop':
            # Set maxMembersPerTeam to 0 if eventType is workshop
            self.maxMembersPerTeam = 0

            # Set billing type to team or event if eventType is workshop
            self.event_billingType = 'team'
            self.availabledivision_set.filter(division_billingType='student').update(division_entryFee=None)
            self.availabledivision_set.filter(division_billingType='student').update(division_billingType='event')

    # *****Methods*****

    # *****Get Methods*****

    def directEnquiriesToName(self):
        return self.directEnquiriesTo.fullname_or_email()
    directEnquiriesToName.short_description = 'Direct enquiries to'
    directEnquiriesToName.admin_order_field = 'directEnquiriesTo'   

    def directEnquiriesToEmail(self):
        return self.directEnquiriesTo.email
    directEnquiriesToEmail.short_description = 'Direct enquiries to email'
    directEnquiriesToEmail.admin_order_field = 'directEnquiriesTo__email'

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('events:details', kwargs = {"eventID": self.id})

    def boolWorkshop(self):
        return self.eventType == 'workshop'

    def __str__(self):
        if not self.globalEvent:
            return f'{self.name} {self.year} ({self.state.abbreviation})'
        else:
            return f'{self.name} {self.year}'

    # *****CSV export methods*****

    # *****Email methods*****

class AvailableDivision(CustomSaveDeleteModel):
    # Foreign keys
    event = models.ForeignKey(Event, verbose_name='Event', on_delete=models.CASCADE)
    division = models.ForeignKey(Division, verbose_name='Division', on_delete=models.PROTECT)

    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)

    # Team details
    division_maxTeamsPerSchool = models.PositiveIntegerField('Max teams per school', null=True, blank=True, help_text='Leave blank for no limit. Will override limit on event.')
    division_maxTeamsForDivision = models.PositiveIntegerField('Max teams for division', null=True, blank=True, help_text='Leave blank for no limit. Will override limit on event.')

    # Billing details
    billingTypeChoices = (('event', 'Event settings'), ('team', 'By team'), ('student', 'By student'))
    division_billingType = models.CharField('Billing type', max_length=15, choices=billingTypeChoices, default='event')
    division_entryFee = models.PositiveIntegerField('Division entry fee', null=True, blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Available Division'
        unique_together = ('event', 'division')
        ordering = ['event', 'division']

    def clean(self):
        errors = []
        # Check required fields are not None
        checkRequiredFieldsNotNone(self, ['event', 'division'])

        # Validate division_entryFee and division_billingType
        if self.division_billingType == 'event' and self.division_entryFee is not None:
            errors.append(ValidationError('Division entry fee must be blank if event billing settings selected'))

        if self.division_billingType != 'event' and self.division_entryFee is None:
            errors.append(ValidationError('Division entry fee must not be blank if event billing settings not selected'))

        # Validate division_billingType
        if self.division_billingType != 'event' and (self.event.event_specialRateNumber is not None or self.event.event_specialRateFee is not None):
            errors.append(ValidationError('Special rate billing on event is incompatible with division based billing settings'))

        if self.division_billingType == 'student' and self.event.eventType == 'workshop':
            errors.append(ValidationError('Student billing not available on workshops, use team billing which bills per attendee'))

        # Validate division state
        if self.division.state is not None and self.division.state != self.event.state:
            errors.append(ValidationError('Division state must match event state'))

        # Raise any errors
        if errors:
            raise ValidationError(errors)

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        return eventCoordinatorEditPermisisons(level)

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
