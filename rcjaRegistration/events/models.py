from django.db import models
from django.db.models import F, Q
from common.models import SaveDeleteMixin, checkRequiredFieldsNotNone
from django.conf import settings
from django.core.exceptions import ValidationError
from django.urls import reverse

import bleach
import datetime

from django.utils.html import format_html, mark_safe
from django.template.defaultfilters import filesizeformat
from common.fields import UUIDImageField

from rcjaRegistration.storageBackends import PublicMediaStorage
from django.templatetags.static import static

from invoices.models import Invoice, InvoiceGlobalSettings
from schools.models import SchoolAdministrator

# **********MODELS**********

def eventCoordinatorEditPermissions(level):
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
    def stateCoordinatorPermissions(cls, level):
        return eventCoordinatorViewPermissions(level)

    stateCoordinatorViewGlobal = True

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return self.name

    # *****CSV export methods*****

    # *****Email methods*****

class Division(models.Model):
    # Foreign keys
    state = models.ForeignKey('regions.State', verbose_name='State', on_delete=models.PROTECT, null=True, blank=True, limit_choices_to={'typeCompetition': True}, help_text='Leave blank for a global division. Global divisions are only editable by global administrators.')
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=60, unique=True)
    description = models.CharField('Description', max_length=200, blank=True)
    category = models.ForeignKey(DivisionCategory, verbose_name='Category', on_delete=models.SET_NULL, null=True, blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Division'
        ordering = ['category', 'name']

    def clean(self):
        errors = []

        # Check changing state won't cause conflict
        if self.pk and self.state:
            if self.baseeventattendance_set.exclude(event__state=self.state).exists():
                errors.append(ValidationError('State not compatible with existing event attendances in this division'))

            if self.availabledivision_set.exclude(event__state=self.state).exists():
                errors.append(ValidationError('State not compatible with existing available division for this division'))

        # Raise any errors
        if errors:
            raise ValidationError(errors)

    # *****Permissions*****
    @classmethod
    def stateCoordinatorPermissions(cls, level):
        return eventCoordinatorEditPermissions(level)

    stateCoordinatorViewGlobal = True

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
    state = models.ForeignKey('regions.State', verbose_name='State', on_delete=models.PROTECT, limit_choices_to={'typeCompetition': True})
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=60)
    address = models.TextField('Address', blank=True)
    # Venue image
    venueImage = UUIDImageField('Venue image', storage=PublicMediaStorage(), upload_prefix="VenueImage", original_filename_field="venueImageOriginalFilename", null=True, blank=True)
    venueImageOriginalFilename = models.CharField('Original filename', max_length=300, null=True, blank=True, editable=False)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Venue'
        ordering = ['name']
        unique_together = ('name', 'state')

    def clean(self):
        errors = []

        # Check required fields are not None
        checkRequiredFieldsNotNone(self, ['state'])

        # Check changing state won't cause conflict
        if self.pk and self.event_set.exclude(state=self.state).exists():
            errors.append(ValidationError('State not compatible with existing events with this venue'))

        # Raise any errors
        if errors:
            raise ValidationError(errors)

    # *****Permissions*****
    @classmethod
    def stateCoordinatorPermissions(cls, level):
        return eventCoordinatorEditPermissions(level)

    # Used in state coordinator permission checking
    def getState(self):
        return self.state

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    # Image methods

    def venueImageFilesize(self):
        return filesizeformat(self.venueImage.size)
    venueImageFilesize.short_description = 'Size'

    def venueImageTag(self):
        return format_html('<img src="{}" height="200" />', self.venueImage.url)
    venueImageTag.short_description = 'Preview'

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
    displayEventsOnWebsite = models.BooleanField('Display events on website', default=False)

    # *****Meta and clean*****
    class Meta:
        verbose_name = "Year"
        ordering = ['-year']

    # *****Permissions*****
    @classmethod
    def stateCoordinatorPermissions(cls, level):
        return eventCoordinatorViewPermissions(level)

    stateCoordinatorViewGlobal = True

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return str(self.year)

    # *****CSV export methods*****

    # *****Email methods*****

class Event(SaveDeleteMixin, models.Model):
    # Foreign keys
    year = models.ForeignKey(Year, verbose_name='Year', on_delete=models.PROTECT)
    state = models.ForeignKey('regions.State', verbose_name = 'State', on_delete=models.PROTECT, limit_choices_to={'typeCompetition': True})
    globalEvent = models.BooleanField('Global event', default=False, help_text='Global events appear to users as not belonging to a state. Recommeneded for national events. Billing still uses state based settings.')

    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)

    # Fields
    name = models.CharField('Name', max_length=50)
    eventTypeChoices = (('competition', 'Competition'), ('workshop', 'Workshop'))
    eventType = models.CharField('Event type', max_length=15, choices=eventTypeChoices, help_text='Competition is standard event with teams and students. Workshop has no teams or students, just workshop attendees.')
    statusChoices = (('draft', 'Draft'), ('published', 'Published'))
    status = models.CharField('Status', max_length=15, choices=statusChoices, default='draft', help_text="Event must be published to be visible and for people to register. Can't unpublish once people have registered.")

    # Banner image
    eventBannerImage = UUIDImageField('Banner image', storage=PublicMediaStorage(), upload_prefix='EventBannerImage', original_filename_field='eventBannerImageOriginalFilename', null=True, blank=True)
    eventBannerImageOriginalFilename = models.CharField('Original filename', max_length=300, null=True, blank=True, editable=False)

    # Dates
    startDate = models.DateField('Event start date')
    endDate = models.DateField('Event end date')
    registrationsOpenDate = models.DateField('Registrations open date')
    registrationsCloseDate = models.DateField('Registration close date')

    # Team details
    maxMembersPerTeam = models.PositiveIntegerField('Max members per team', default=4)
    event_maxTeamsPerSchool = models.PositiveIntegerField('Max teams per school', null=True, blank=True, help_text='Leave blank for no limit. Only enforced on the mentor signup page, can be overridden in the admin portal.')
    event_maxTeamsForEvent = models.PositiveIntegerField('Max teams for event', null=True, blank=True, help_text='Leave blank for no limit. Only enforced on the mentor signup page, can be overridden in the admin portal.')

    # Billing details
    entryFeeIncludesGST = models.BooleanField('Includes GST', default=True, help_text='Whether the prices specified on this page are GST inclusive or exclusive.')
    event_defaultEntryFee = models.PositiveIntegerField('Default entry fee', default=0)
    paymentDueDate = models.DateField('Payment due date', null=True, blank=True)

    # Competition billing settings
    billingTypeChoices = (('team', 'By team'), ('student', 'By student'))
    event_billingType = models.CharField('Billing type', max_length=15, choices=billingTypeChoices, default='team')
    event_specialRateNumber = models.PositiveIntegerField('Special rate number', null=True, blank=True, help_text="The number of teams specified will be billed at this rate. Subsequent teams will be billed at the default rate. Leave blank for no special rate.")
    event_specialRateFee = models.PositiveIntegerField('Special rate fee', null=True, blank=True)

    # Workshop billing settings
    workshopTeacherEntryFee = models.PositiveIntegerField('Teacher entry fee', null=True)
    workshopStudentEntryFee = models.PositiveIntegerField('Student entry fee', null=True)

    # Surcharge
    eventSurchargeAmount = models.FloatField('Surcharge amount for event', default=0, editable=False) # Store the surcharge amount at the time of event creation so later changes don't affect past events

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

        # Validate status
        if self.pk and self.status != 'published' and (self.baseeventattendance_set.exists() or self.invoice_set.exists()):
            errors.append(ValidationError("Can't unpublish once teams or invoices created"))

        # Check close and end date after start dates
        if self.startDate > self.endDate:
            errors.append(ValidationError('Start date must not be after end date'))

        if self.registrationsOpenDate > self.registrationsCloseDate:
            errors.append(ValidationError('Registration open date must not be after registration close date'))

        if self.registrationsCloseDate > self.startDate:
            errors.append(ValidationError('Registration close date must be before or on event start date'))

        # Validate billing settings
        if (self.event_specialRateNumber is None) != (self.event_specialRateFee is None):
            errors.append(ValidationError('Both special rate number and fee must either be blank or not blank'))

        if self.pk and (self.event_specialRateNumber is not None or self.event_specialRateFee is not None) and self.availabledivision_set.exclude(division_billingType='event').exists():
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

        # Validate file upload deadline if start date or registrations clsoe date changed
        if self.pk and self.eventavailablefiletype_set.filter(uploadDeadline__gt=self.startDate).exists():
            errors.append(ValidationError("Event start date must on or after file upload deadlines"))

        if self.pk and self.eventavailablefiletype_set.filter(uploadDeadline__lt=self.registrationsCloseDate).exists():
            errors.append(ValidationError("Registration close date must on or before file upload deadlines"))

        # Raise any errors
        if errors:
            raise ValidationError(errors)

    # *****Permissions*****
    @classmethod
    def stateCoordinatorPermissions(cls, level):
        return eventCoordinatorEditPermissions(level)

    # Used in state coordinator permission checking
    def getState(self):
        return self.state

    # *****Save & Delete Methods*****

    def preSave(self):
        # Set workshop prices
        if self.workshopTeacherEntryFee is None:
            self.workshopTeacherEntryFee = self.event_defaultEntryFee

        if self.workshopStudentEntryFee is None:
            self.workshopStudentEntryFee = self.event_defaultEntryFee

        if self.eventType == 'workshop':
            # Set maxMembersPerTeam to 0 if eventType is workshop
            self.maxMembersPerTeam = 0

            # Set billing type to team or event if eventType is workshop
            self.event_billingType = 'team'
            if self.pk:
                self.availabledivision_set.filter(division_billingType='student').update(division_entryFee=None)
                self.availabledivision_set.filter(division_billingType='student').update(division_billingType='event')

        # Set surcharge amount to global settings value
        if self.pk is None:
            try:
                self.eventSurchargeAmount = InvoiceGlobalSettings.objects.get().surchargeAmount
            except InvoiceGlobalSettings.DoesNotExist:
                pass # Already set to 0 by default

        self.billingDetailsChanged = self.checkBillingDetailsChanged()

    def checkBillingDetailsChanged(self):
        try:
            previousEvent = Event.objects.get(pk=self.pk)
        except Event.DoesNotExist:
            # Return false on new event because no invoices can exist yet
            return False

        return (
            self.entryFeeIncludesGST != previousEvent.entryFeeIncludesGST or
            self.event_defaultEntryFee != previousEvent.event_defaultEntryFee or
            self.event_billingType != previousEvent.event_billingType or
            self.event_specialRateNumber != previousEvent.event_specialRateNumber or
            self.event_specialRateFee != previousEvent.event_specialRateFee or
            self.workshopTeacherEntryFee != previousEvent.workshopTeacherEntryFee or
            self.workshopStudentEntryFee != previousEvent.workshopStudentEntryFee
        )

    def postSave(self):
        if self.billingDetailsChanged: # Set in presave so can see the previous value before database operation
            for invoice in self.invoice_set.all():
                invoice.calculateAndSaveAllTotals()

    # *****Methods*****

    # *****Get Methods*****

    def surchargeName(self):
        # For serializer
        try:
            return InvoiceGlobalSettings.objects.get().surchargeName
        except InvoiceGlobalSettings.DoesNotExist:
            return ''

    def surchargeEventDescription(self):
        # For serializer
        try:
            return InvoiceGlobalSettings.objects.get().surchargeEventDescription
        except InvoiceGlobalSettings.DoesNotExist:
            return ''

    def registrationsOpen(self):
        return self.registrationsCloseDate >= datetime.datetime.today().date() and self.registrationsOpenDate <= datetime.datetime.today().date()

    def registrationNotOpenYet(self):
        return self.registrationsOpenDate > datetime.datetime.today().date()

    def published(self):
        return self.status == 'published'

    def paidEvent(self):
        if self.event_defaultEntryFee > 0 or (self.event_specialRateFee and self.event_specialRateFee > 0):
            return True
        # Workshops don't rely on the default entry fee
        if self.eventType == 'workshop':
            if self.workshopTeacherEntryFee and self.workshopTeacherEntryFee > 0:
                return True
            if self.workshopStudentEntryFee and self.workshopStudentEntryFee > 0:
                return True

        return self.availabledivision_set.filter(division_entryFee__gt=0).exists()

    def getBaseEventAttendanceFilterDict(self, user):
        # Create dict of attributes to filter teams/ workshop attendees by
        if user.currentlySelectedSchool is not None:
            return {
                'event': self,
                'school': user.currentlySelectedSchool
            }
        else:
            # Independent, filter by mentor
            return {
                'event': self,
                'school': None,
                'mentorUser': user
            }

    def maxEventTeamsForSchoolReached(self, user):
        return self.event_maxTeamsPerSchool is not None and self.baseeventattendance_set.filter(**self.getBaseEventAttendanceFilterDict(user)).count() >= self.event_maxTeamsPerSchool

    def maxEventTeamsTotalReached(self):
        return self.event_maxTeamsForEvent is not None and self.baseeventattendance_set.count() >= self.event_maxTeamsForEvent

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

    def bleachedEventDetails(self):
        return mark_safe(bleach.clean(self.eventDetails))

    def registrationsAdminURL(self):
        if self.boolWorkshop():
            return f"{reverse('admin:workshops_workshopattendee_changelist')}?event__id__exact={self.id}"
        return f"{reverse('admin:teams_team_changelist')}?event__id__exact={self.id}"

    # Image methods

    def effectiveBannerImageURL(self):
        if self.eventBannerImage:
            return self.eventBannerImage.url
        elif self.venue and self.venue.venueImage:
            return self.venue.venueImage.url
        elif self.state and self.state.defaultEventImage:
            return self.state.defaultEventImage.url
        else:
            return static("homeimage2.jpg")

    def effectiveBannerImageTag(self):
        return format_html('<img src="{}" height="200" />', self.effectiveBannerImageURL())
    effectiveBannerImageTag.short_description = 'Preview'

    def bannerImageFilesize(self):
        return filesizeformat(self.eventBannerImage.size)
    bannerImageFilesize.short_description = 'Size'

    def __str__(self):
        if not (self.globalEvent or self.state.typeGlobal):
            return f'{self.name} {self.year} ({self.state.abbreviation})'
        else:
            return f'{self.name} {self.year}'

    # *****CSV export methods*****

    # *****Email methods*****

class AvailableDivision(SaveDeleteMixin, models.Model):
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
    def stateCoordinatorPermissions(cls, level):
        return eventCoordinatorEditPermissions(level)

    # Used in state coordinator permission checking
    def getState(self):
        return self.event.state

    # *****Save & Delete Methods*****

    def postSave(self):
        for invoice in self.event.invoice_set.all():
            invoice.calculateAndSaveAllTotals()

    def postDelete(self):
        for invoice in self.event.invoice_set.all():
            invoice.calculateAndSaveAllTotals()

    # *****Methods*****

    # *****Get Methods*****

    def maxDivisionTeamsForSchoolReached(self, user):
        return self.division_maxTeamsPerSchool is not None and self.division.baseeventattendance_set.filter(**self.event.getBaseEventAttendanceFilterDict(user)).count() >= self.division_maxTeamsPerSchool

    def maxDivisionTeamsTotalReached(self):
        return self.division_maxTeamsForDivision is not None and self.division.baseeventattendance_set.filter(event=self.event).count() >= self.division_maxTeamsForDivision

    def __str__(self):
        return str(self.division)

    # *****CSV export methods*****

    # *****Email methods*****

class BaseEventAttendance(SaveDeleteMixin, models.Model):
    # Foreign keys
    event = models.ForeignKey('events.Event', verbose_name='Event', on_delete=models.CASCADE, limit_choices_to={'status': 'published'})
    division = models.ForeignKey('events.Division', verbose_name='Division', on_delete=models.PROTECT)

    # User and school foreign keys
    mentorUser = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Mentor', on_delete=models.PROTECT)
    school = models.ForeignKey('schools.School', verbose_name='School', on_delete=models.PROTECT, null=True, blank=True)
    campus = models.ForeignKey('schools.Campus', verbose_name='Campus', on_delete=models.PROTECT, null=True, blank=True)

    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)

    # Fields
    copiedFrom = models.ForeignKey('BaseEventAttendance', on_delete=models.SET_NULL, related_name='copiedTo', verbose_name='Copied from', blank=True, null=True, editable=False)
    notes = models.TextField('Notes', blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Base attendance'

    def clean(self):
        errors = []
        checkRequiredFieldsNotNone(self, ['event', 'division'])

        # Check correct event type for child
        # eventTypeMapping must be defined on child or defaults to validation errror
        if getattr(self, 'eventTypeMapping', None) != self.event.eventType:
            errors.append(ValidationError('This event attendance is incompatible with this event type'))

        # Check event is published
        if self.event.status != 'published':
            errors.append(ValidationError('Event must be published'))

        # Check campus school matches school on this object
        if self.campus and self.campus.school != self.school:
            errors.append(ValidationError('Campus school must match school'))

        # Check division is from correct state
        if self.division.state is not None and self.division.state != self.event.state:
            errors.append(ValidationError('Division state must match event state'))

        # Check mentor is admin of this object's school
        # Check not None because set after clean in frontend forms
        if getattr(self, 'mentorUser', None) and getattr(self, 'school', None):
            # Check not the current values in case mentor removed as admin of school after the event
            if not self.pk or self.mentorUser != BaseEventAttendance.objects.get(pk=self.pk).mentorUser or self.school != BaseEventAttendance.objects.get(pk=self.pk).school:
                if not SchoolAdministrator.objects.filter(user=self.mentorUser, school=self.school).exists():
                    errors.append(ValidationError(f"{self.mentorUser.get_full_name()} is not an administrator of {self.school}"))

        # Raise any errors
        if errors:
            raise ValidationError(errors)

    # *****Permissions*****
    @classmethod
    def stateCoordinatorPermissions(cls, level):
        return eventCoordinatorEditPermissions(level)

    # Used in state coordinator permission checking
    def getState(self):
        return self.event.state

    # *****Save & Delete Methods*****

    def createUpdateInvoices(self):
        if self.event.paidEvent():
            if self.campusInvoicingEnabled():
                # Get or create invoice with matching campus
                invoice, created = Invoice.objects.get_or_create(
                    school=self.school,
                    campus=self.campus,
                    event=self.event,
                    defaults={'invoiceToUser': self.mentorUser}
                )

            elif self.school:
                # Ignore campus and only look for matching school
                invoice, created = Invoice.objects.get_or_create(
                    school=self.school,
                    event=self.event,
                    defaults={'invoiceToUser': self.mentorUser}
                )

            else:
                # Get invoice for this user for independent entry
                invoice, created = Invoice.objects.get_or_create(
                    invoiceToUser=self.mentorUser,
                    event=self.event,
                    school=None
                )

            if not created:
                invoice.calculateAndSaveAllTotals()

    def preSave(self):
        self.setPreviousSchoolValues()

    def postSave(self):
        self.createUpdateInvoices()
        if self.schoolValuesChanged:
            self.previousObject.createUpdateInvoices()

    def postDelete(self):
        self.createUpdateInvoices()

    # *****Methods*****

    # Check if school, mentorUser or campus changed
    def checkSchoolValuesChanged(self):
        return (
            self.school != self.previousObject.school or
            self.mentorUser != self.previousObject.mentorUser or
            self.campus != self.previousObject.campus
        )

    # Get previous school, mentorUser and campus if changed and set fields on object with old values
    def setPreviousSchoolValues(self):
        self.schoolValuesChanged = False
        try:
            self.previousObject = BaseEventAttendance.objects.get(pk=self.pk)

            if self.checkSchoolValuesChanged():
                self.schoolValuesChanged = True

        except BaseEventAttendance.DoesNotExist:
            pass

    # *****Get Methods*****

    def eventAttendanceType(self):
        # Returns type of eventAttendance. e.g. team, workshopattendee
        for attr in ['team', 'workshopattendee']:
            if hasattr(self, attr):
                return attr

    def childObject(self):
        # Get team or workshop attendance object for this eventAttendee
        return getattr(self, self.eventAttendanceType())

    def __str__(self):
        return str(self.childObject())

    def homeState(self):
        if self.school:
            return self.school.state
        return self.mentorUser.homeState
    homeState.short_description = 'Home state'

    def homeRegion(self):
        if self.school:
            return self.school.region
        return self.mentorUser.homeRegion
    homeRegion.short_description = 'Home region'

    def schoolPostcode(self):
        if self.school:
            return self.school.postcode
        return None
    schoolPostcode.short_description = 'School postcode'

    def mentorUserName(self):
        return self.mentorUser.fullname_or_email()
    mentorUserName.short_description = 'Mentor'
    mentorUserName.admin_order_field = 'mentorUser'

    def mentorUserEmail(self):
        return self.mentorUser.email
    mentorUserEmail.short_description = 'Mentor email'
    mentorUserEmail.admin_order_field = 'mentorUser__email'

    def mentorUserPK(self):
        return self.mentorUser.pk
    mentorUserPK.short_description = 'Mentor PK'

    # Returns true if campus based invoicing enabled for this school for this event
    def campusInvoicingEnabled(self):
        if not self.school:
            return False

        # Check if at least one invoice has campus field set
        return Invoice.objects.filter(school=self.school, event=self.event, campus__isnull=False).exists()

    # File upload

    def availableFileUploadTypes(self):
        return self.event.eventavailablefiletype_set.filter(uploadDeadline__gte=datetime.datetime.today())

    # *****CSV export methods*****

    # *****Email methods*****
