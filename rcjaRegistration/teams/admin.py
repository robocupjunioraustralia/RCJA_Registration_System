from django.contrib import admin
from common.admin import *
from coordination.adminPermissions import AdminPermissions

from .models import *

# Register your models here.

class StudentInline(admin.TabularInline):
    model = Student
    extra = 0


@admin.register(Team)
class TeamAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'name',
        'event',
        'division',
        'mentorUser',
        'school',
        'campus',
    ]
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
        'mentorUser',
        'school',
        'campus',
    ]

    # State based filtering

    def fieldsToFilter(self, request):
        from coordination.adminPermissions import reversePermisisons
        from users.models import User
        from schools.models import School, Campus
        from events.models import Event, Division
        return [
            {
                'field': 'event',
                'queryset': Event.objects.filter(
                    state__coordinator__user=request.user,
                    state__coordinator__permissions__in=reversePermisisons(Team, ['add', 'change'])
                )
            },
            {
                'field': 'division',
                'queryset': Division.objects.filter(
                    Q(state__coordinator__user=request.user)  | Q(state=None),
                    Q(state__coordinator__permissions__in=reversePermisisons(Team, ['add', 'change'])) | Q(state=None)
                )
            },
            {
                'field': 'mentorUser',
                'queryset': User.objects.filter(
                    homeState__coordinator__user=request.user,
                    homeState__coordinator__permissions__in=reversePermisisons(Team, ['add', 'change'])
                )
            },
            {
                'field': 'school',
                'queryset': School.objects.filter(
                    state__coordinator__user=request.user,
                    state__coordinator__permissions__in=reversePermisisons(Team, ['add', 'change'])
                )
            },
            {
                'field': 'campus',
                'queryset': Campus.objects.filter(
                    school__state__coordinator__user=request.user,
                    school__state__coordinator__permissions__in=reversePermisisons(Team, ['add', 'change'])
                )
            }
        ]

    def stateFilteringAttributes(self, request):
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

    def fieldsToFilter(self, request):
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

    def stateFilteringAttributes(self, request):
        from coordination.models import Coordinator
        return {
            'team__event__state__coordinator__in': Coordinator.objects.filter(user=request.user)
        }
