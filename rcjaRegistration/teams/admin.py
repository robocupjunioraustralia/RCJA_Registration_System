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
        'event',
        'division',
        'school',
        'name'
    ]
    inlines = [
        StudentInline
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
