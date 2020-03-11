from django.contrib import admin
from common.admin import *
from coordination.adminPermissions import AdminPermissions
from django import forms
from django.contrib import messages

from .models import *
from schools.models import Campus

# Register your models here.

class StudentInline(admin.TabularInline):
    model = Student
    extra = 0

class TeamForm(forms.ModelForm):
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

@admin.register(Team)
class TeamAdmin(DifferentAddFieldsMixin, AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'name',
        'event',
        'division',
        'mentorUserName',
        'school',
        'campus',
        'homeState',
    ]
    fieldsets = (
        (None, {
            'fields': ('name',)
        }),
        ('Event', {
            'fields': ('event', 'division')
        }),
        ('School', {
            'fields': ('mentorUser', 'school', 'campus',)
        }),
    )
    add_fieldsets = (
        (None, {
            'fields': ('name',)
        }),
        ('Event', {
            'fields': ('event', 'division')
        }),
        ('School', {
            'description': "Select this team's mentor.<br>If they are a mentor for one school that school will be autofilled. If they are mentor of more than one school you will need to select the school. Leave school blank if independent.<br>You can select campus after you have clicked save.",
            'fields': ('mentorUser', 'school',)
        }),
    )
    autocomplete_fields = [
        'event',
        'division',
        'mentorUser',
        'school',
        'campus',
    ]
    inlines = [
        StudentInline
    ]
    list_filter = [
        'event',
        'division',
    ]
    search_fields = [
        'name',
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
        'student__firstName',
        'student__lastName',
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'name',
        'event',
        'division',
        'mentorUserName',
        'mentorUserEmail',
        'school',
        'campus',
        'homeState',
    ]

    form = TeamForm

    # Set school and campus to that of mentor if only one option
    def save_model(self, request, obj, form, change):
        if not obj.pk and obj.school is None and obj.mentorUser.schooladministrator_set.count() == 1:
            obj.school = obj.mentorUser.schooladministrator_set.first().school
            self.message_user(request, f"{obj.school} automatically added to {obj}", messages.SUCCESS)
        
        super().save_model(request, obj, form, change)

    # State based filtering

    @classmethod
    def fieldsToFilterRequest(cls, request):
        from coordination.adminPermissions import reversePermisisons
        from events.models import Event
        return [
            {
                'field': 'event',
                'queryset': Event.objects.filter(
                    state__coordinator__user=request.user,
                    state__coordinator__permissions__in=reversePermisisons(Team, ['add', 'change'])
                )
            },
        ]

    @classmethod
    def fieldsToFilterObj(cls, request, obj):
        return [
            {
                'field': 'campus',
                'queryset': Campus.objects.filter(school=obj.school) if obj is not None else Campus.objects.none(),
                'filterNone': True,
            }
        ]

    @classmethod
    def stateFilteringAttributes(cls, request):
        from coordination.models import Coordinator
        return {
            'event__state__coordinator__in': Coordinator.objects.filter(user=request.user)
        }

@admin.register(Student)
class StudentAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        '__str__',
        'team',
    ]
    autocomplete_fields = [
        'team',
    ]
    list_filter = [
        'team__event',
        'team__division',
    ]
    search_fields = [
        'firstName',
        'lastName',
        'team__name',
        'team__school__state__name',
        'team__school__state__abbreviation',
        'team__school__region__name',
        'team__school__name',
        'team__school__abbreviation',
        'team__campus__name',
        'team__mentorUser__first_name',
        'team__mentorUser__last_name',
        'team__mentorUser__email',
        'team__event__name',
        'team__division__name',
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'team',
        'firstName',
        'lastName',
        'yearLevel',
        'gender',
        'birthday',
    ]

    # State based filtering

    @classmethod
    def fieldsToFilterRequest(cls, request):
        from coordination.adminPermissions import reversePermisisons
        return [
            {
                'field': 'team',
                'queryset': Team.objects.filter(
                    event__state__coordinator__user=request.user,
                    event__state__coordinator__permissions__in=reversePermisisons(Student, ['add', 'change'])
                )
            }
        ]

    @classmethod
    def stateFilteringAttributes(cls, request):
        from coordination.models import Coordinator
        return {
            'team__event__state__coordinator__in': Coordinator.objects.filter(user=request.user)
        }
