from django.contrib import admin
from django.db.models import F, Q
from common.adminMixins import ExportCSVMixin, DifferentAddFieldsMixin, FKActionsRemove
from coordination.permissions import AdminPermissions, InlineAdminPermissions
from coordination.models import Coordinator
from django.contrib import messages
from django import forms
from django.forms import TextInput, Textarea
from django.core.exceptions import ValidationError
from django.db import models

from .models import DivisionCategory, Division, Venue, Year, Event, AvailableDivision
from regions.models import State
from schools.models import Campus
from eventfiles.adminInlines import EventAvailableFileTypeInline

from regions.admin import StateAdmin

# Register your models here.

@admin.register(DivisionCategory)
class DivisionCategoryAdmin(AdminPermissions, admin.ModelAdmin):
    pass

@admin.register(Division)
class DivisionAdmin(FKActionsRemove, AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'name',
        'state',
        'category',
        'description',
    ]
    search_fields = [
        'name',
        'state__name',
        'state__abbreviation',
        'category__name'
    ]
    list_filter = [
        'category',
        'state',
    ]
    actions = [
        'export_as_csv',
    ]
    exportFields = [
        'pk',
        'name',
        'state',
        'category',
        'description',
    ]
    autocomplete_fields = [
        'state',
    ]

    # State based filtering

    @classmethod
    def fieldsToFilterRequest(cls, request):
        return [
            {
                'field': 'state',
                'stateCoordinatorRequired': True,
                'fieldAdmin': StateAdmin,
            }
        ]

    stateFilterLookup = 'state__coordinator'
    globalFilterLookup = 'state'

@admin.register(Venue)
class VenueAdmin(FKActionsRemove, AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'name',
        'state',
        'address',
    ]
    fields = [
        'state',
        'name',
        'address',
        ('venueImage', 'venueImageOriginalFilename', 'venueImageFilesize', 'venueImageTag'),
    ]
    readonly_fields = [
        'venueImageOriginalFilename',
        'venueImageFilesize',
        'venueImageTag',
    ]
    search_fields = [
        'name',
        'state__name',
        'state__abbreviation',
        'address',
    ]
    list_filter = [
        'state',
    ]
    actions = [
        'export_as_csv',
    ]
    exportFields = [
        'pk',
        'name',
        'state',
        'address',
    ]
    autocomplete_fields = [
        'state',
    ]

    # State based filtering

    @classmethod
    def fieldsToFilterRequest(cls, request):
        return [
            {
                'field': 'state',
                'fieldAdmin': StateAdmin,
            }
        ]

    stateFilterLookup = 'state__coordinator'

@admin.register(Year)
class YearAdmin(AdminPermissions, admin.ModelAdmin):
    list_display = [
        '__str__',
        'displayEventsOnWebsite',
    ]

class AvailableDivisionInline(FKActionsRemove, InlineAdminPermissions, admin.TabularInline):
    model = AvailableDivision
    extra = 0
    autocomplete_fields = [
        'division',
    ]

    def get_exclude(self, request, obj=None):
        if obj:
            if obj.eventType == 'workshop':
                return [
                    'division_maxTeamsPerSchool',
                    'division_maxTeamsForDivision',
                    'division_billingType',
                    'division_entryFee',
                ]
        return super().get_exclude(request, obj)

    @classmethod
    def fieldsToFilterObj(cls, request, obj):
        return [
            {
                'field': 'division',
                'queryset': Division.objects.filter(Q(state=obj.state) | Q(state=None)) if obj is not None else Division.objects.none(), # Inline not displayed on create so will never fallback to None
                'filterNone': True
            }
        ]

@admin.register(Event)
class EventAdmin(FKActionsRemove, DifferentAddFieldsMixin, AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        '__str__',
        'eventType',
        'status',
        'year',
        'state',
        'globalEvent',
        'startDate',
        'registrationsCloseDate',
        'directEnquiriesToName',
        'venue',
    ]
    competition_fieldsets = (
        (None, {
            'description': "You do not need to place the year or state name in the event name as these are automatically added.",
            'fields': ('year', ('state', 'globalEvent'), 'name', 'eventType', 'status')
        }),
        ('Display image', {
            'description': "This is the image that is displayed for this event. Will use the first of event image, venue image, state image, default image.",
            'fields': (('eventBannerImage', 'eventBannerImageOriginalFilename', 'bannerImageFilesize', 'effectiveBannerImageTag'),)
        }),
        ('Dates', {
            'fields': ('startDate', 'endDate', 'registrationsOpenDate', 'registrationsCloseDate')
        }),
        ('Team settings', {
            'fields': ('maxMembersPerTeam', 'event_maxTeamsPerSchool', 'event_maxTeamsForEvent',)
        }),
        ('Billing settings', {
            'fields': ('entryFeeIncludesGST', 'event_billingType', 'event_defaultEntryFee', ('event_specialRateNumber', 'event_specialRateFee'), 'paymentDueDate')
        }),
        ('Details', {
            'fields': ('directEnquiriesTo', 'venue', 'eventDetails', 'additionalInvoiceMessage')
        }),
    )
    workshop_fieldsets = (
        (None, {
            'description': "You do not need to place the year or state name in the event name as these are automatically added.",
            'fields': ('year', ('state', 'globalEvent'), 'name', 'eventType', 'status')
        }),
        ('Display image', {
            'description': "This is the image that is displayed for this event. Will use the first of event image, venue image, state image, default image.",
            'fields': (('eventBannerImage', 'eventBannerImageOriginalFilename', 'bannerImageFilesize', 'effectiveBannerImageTag'),)
        }),
        ('Dates', {
            'fields': ('startDate', 'endDate', 'registrationsOpenDate', 'registrationsCloseDate')
        }),
        ('Billing settings', {
            'fields': ('entryFeeIncludesGST', 'workshopTeacherEntryFee', 'workshopStudentEntryFee', 'paymentDueDate')
        }),
        ('Details', {
            'fields': ('directEnquiriesTo', 'venue', 'eventDetails', 'additionalInvoiceMessage')
        }),
    )
    add_fieldsets = (
        (None, {
            'description': "You do not need to place the year or state name in the event name as these are automatically added.",
            'fields': ('year', ('state', 'globalEvent'), 'name')
        }),
        ('Event type', {
            'description': "Please choose carefully, this can't be changed after the event is created",
            'fields': ('eventType',)
        }),
        ('Dates', {
            'fields': ('startDate', 'endDate', 'registrationsOpenDate', 'registrationsCloseDate')
        }),
        ('Billing settings', {
            'description': "More options will be available after you click save",
            'fields': ('entryFeeIncludesGST', 'event_defaultEntryFee')
        }),
        ('Details', {
            'description': "More options will be available after you click save",
            'fields': ('directEnquiriesTo', 'venue',)
        }),
    )

    readonly_fields = [
        'eventType', # Can't change event type after creation, because would make team and workshop fk validation very difficult and messy
        'eventBannerImageOriginalFilename',
        'bannerImageFilesize',
        'effectiveBannerImageTag',
    ]
    add_readonly_fields = [
    ]

    def get_readonly_fields(self, request, obj):
        readonly_fields = super().get_readonly_fields(request, obj)

        if obj is None:
            return readonly_fields

        # Make status read only if can't unpublish
        if obj.status == 'published' and (obj.baseeventattendance_set.exists() or obj.invoice_set.exists()):
            readonly_fields = readonly_fields + ['status']

        return readonly_fields

    autocomplete_fields = [
        'state',
        'directEnquiriesTo',
        'venue',
    ]
    inlines = [
        AvailableDivisionInline,
        EventAvailableFileTypeInline,
    ]
    add_inlines = [ # Don't include available divisions here so the divisions will be filtered when shown
    ]
    list_filter = [
        'status',
        'eventType',
        'year',
        'state',
        'globalEvent',
    ]
    search_fields = [
        'name',
        'state__name',
        'state__abbreviation',
        'directEnquiriesTo__first_name',
        'directEnquiriesTo__last_name',
        'directEnquiriesTo__email',
        'venue__name',
        'venue__address',
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'pk',
        'name',
        'year',
        'state',
        'globalEvent',
        'eventType',
        'startDate',
        'endDate',
        'registrationsOpenDate',
        'registrationsCloseDate',
        'venue',
        'directEnquiriesToName',
        'directEnquiriesToEmail',
        'maxMembersPerTeam',
        'event_maxTeamsPerSchool',
        'event_maxTeamsForEvent',
        'entryFeeIncludesGST',
        'event_billingType',
        'event_defaultEntryFee',
        'event_specialRateNumber',
        'event_specialRateFee',
        'paymentDueDate',
        'eventDetails',
        'additionalInvoiceMessage',
    ]

    formfield_overrides = {
        models.TextField: {'widget': Textarea(attrs={'rows':4, 'cols':130})},
    }
    fkAddEditButtons = [
        'venue',
    ]

    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets

        if obj.eventType == 'workshop':
            return self.workshop_fieldsets

        if obj.eventType == 'competition':
            return self.competition_fieldsets

        return super().get_fieldsets(request, obj)

    # Message user during save
    def save_model(self, request, obj, form, change):
        if obj.pk:
            if obj.venue is None:
                self.message_user(request, f"{obj}: You haven't added a venue yet, we recommend adding a venue.", messages.WARNING)

            if not obj.published():
                self.message_user(request, f"{obj}: Event is not published, publish event to make visible.", messages.WARNING)

        super().save_model(request, obj, form, change)

    # Message user regarding divisions during inline save
    def save_formset(self, request, form, formset, change):
        # Don't want to display error on add page because inlines not shown so impossible to add divisions
        if change and str(formset.form) == "<class 'django.forms.widgets.AvailableDivisionForm'>": # This is a really hacky way of checking the formset
            if len(formset.cleaned_data) == 0:
                self.message_user(request, f"{form.instance}: You haven't added any divisions yet, people won't be able to register.", messages.WARNING)

        super().save_formset(request, form, formset, change)

    # Filter in team and workshop autocompletes
    def get_search_results(self, request, queryset, search_term):
        if 'teams/team/' in request.META.get('HTTP_REFERER', ''):
            queryset = queryset.filter(eventType='competition', status='published')

        if 'workshops/workshopattendee/' in request.META.get('HTTP_REFERER', ''):
            queryset = queryset.filter(eventType='workshop', status='published')

        return super().get_search_results(request, queryset, search_term)

    # State based filtering

    @classmethod
    def fieldsToFilterRequest(cls, request):
        return [
            {
                'field': 'state',
                'fieldAdmin': StateAdmin,
            }
        ]

    stateFilterLookup = 'state__coordinator'
    fieldFilteringModel = Event

    @classmethod
    def fieldsToFilterObj(cls, request, obj):
        return [
            {
                'field': 'venue',
                'queryset': Venue.objects.filter(state=obj.state) if obj is not None else Venue.objects.none(), # Field not displayed on create so will never fallback to None
                'filterNone': True
            }
        ]

class BaseWorkshopAttendanceForm(forms.ModelForm):
    def clean(self):
        cleaned_data = super().clean()
        errors = []

        mentorUser = cleaned_data.get('mentorUser', None)
        school = cleaned_data.get('school', None)

        # Check school is selected if mentor is admin of more than one school
        if mentorUser and mentorUser.schooladministrator_set.count() > 1 and school is None:
            errors.append(ValidationError(f'School must not be blank because {mentorUser.fullname_or_email()} is an administrator of multiple schools. Please select a school.'))

        # Check school is set if previously set and mentor still an admin of school
        if self.instance and self.instance.school and not school:
            errors.append(ValidationError(f"Can't remove {self.instance.school} from this team while {self.instance.mentorUser.fullname_or_email()} is still an admin of this school."))

        # Raise any errors
        if errors:
            raise ValidationError(errors)

        return cleaned_data

class BaseWorkshopAttendanceAdmin(FKActionsRemove, AdminPermissions, DifferentAddFieldsMixin, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'event',
        'division',
        'mentorUserName',
        'school',
        'campus',
        'homeState',
    ]
    autocomplete_fields = [
        'event',
        'division',
        'mentorUser',
        'school',
        'campus',
    ]
    list_filter = [
        'event',
        'division',
    ]
    search_fields = [
        'school__state__name',
        'school__state__abbreviation',
        'school__region__name',
        'school__name',
        'school__abbreviation',
        'campus__name',
        'mentorUser__first_name',
        'mentorUser__last_name',
        'mentorUser__email',
        'event__name',
        'division__name',
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'pk',
        'event',
        'division',
        'mentorUserName',
        'mentorUserEmail',
        'school',
        'campus',
        'homeState',
    ]

    form = BaseWorkshopAttendanceForm

    # Set school and campus to that of mentor if only one option
    def save_model(self, request, obj, form, change):
        if not obj.pk and obj.school is None and obj.mentorUser.schooladministrator_set.count() == 1:
            obj.school = obj.mentorUser.schooladministrator_set.first().school
            self.message_user(request, f"{obj.mentorUser.fullname_or_email()}'s school ({obj.school}) automatically added to {obj}", messages.SUCCESS)
        
        super().save_model(request, obj, form, change)

    # State based filtering

    @classmethod
    def fieldsToFilterRequest(cls, request):
        return [
            {
                'field': 'event',
                'fieldAdmin': EventAdmin,
            }
        ]

    @classmethod
    def fieldsToFilterObj(cls, request, obj):
        return [
            {
                'field': 'campus',
                'queryset': Campus.objects.filter(school=obj.school) if obj is not None else Campus.objects.none(),
                'filterNone': True,
            },
            {
                'field': 'event',
                'queryset': Event.objects.filter(eventType=cls.eventTypeMapping),
                'filterNone': True,
                'useAutocomplete': True,
            }
        ]

    stateFilterLookup = 'event__state__coordinator'
