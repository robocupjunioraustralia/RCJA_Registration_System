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
        'campus'
    ]
    inlines = [
        StudentInline
    ]
    list_filter = [
        'event',
        'division',
    ]
    search_fields = [
        'school__name',
        'school__abbreviation',
        'mentorUser__first_name',
        'mentorUser__last_name',
        'mentorUser__email',
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'event',
        'division',
        'school',
        'name'
    ]

    def stateFilteringAttributes(self, request):
        from coordination.models import Coordinator
        return {
            'event__state__coordinator__in': Coordinator.objects.filter(user=request.user)
        }

@admin.register(Student)
class StudentAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'team',
        'firstName',
        'lastName',
        'yearLevel',
        'gender',
        'birthday'
    ]

    def stateFilteringAttributes(self, request):
        from coordination.models import Coordinator
        return {
            'team__event__state__coordinator__in': Coordinator.objects.filter(user=request.user)
        }
