from django.contrib import admin
from common.admin import *
from coordination.adminPermissions import AdminPermissions

from .models import *

# Register your models here.

@admin.register(School)
class SchoolAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        '__str__',
        'abbreviation',
        'state',
        'region'
    ]
    list_filter = [
        'state',
        'region'
    ]
    search_fields = [
        'state__name',
        'name',
        'abbreviation'
    ]
    autocomplete_fields = [
        'state'
    ]
    actions = [
        'export_as_csv'
    ]
    exportFields = [
        'name',
        'abbreviation',
        'state',
        'region'
    ]

    def stateFilteringAttributes(self, request):
        from coordination.models import Coordinator
        return {
            'state__coordinator__in': Coordinator.objects.filter(user=request.user)
        }

@admin.register(Campus)
class CampusAdmin(AdminPermissions, admin.ModelAdmin):
    
    def stateFilteringAttributes(self, request):
        from coordination.models import Coordinator
        return {
            'school__state__coordinator__in': Coordinator.objects.filter(user=request.user)
        }

@admin.register(SchoolAdministrator)
class SchoolAdministratorAdmin(AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        '__str__',
        'school',
        'campus'
    ]
    list_filter = [
        'school__state',
        'school__region'
    ]
    search_fields = [
        'school__state__name',
        'school__name',
        'school__abbreviation'
    ]
    autocomplete_fields = [
        'school'
    ]
    # actions = [
    #     'export_as_csv'
    # ]
    # exportFields = [
    #     'firstName',
    #     'lastName',
    #     'school',
    #     'email',
    #     'mobileNumber'
    # ]
    from mentorquestions.admin import MentorQuestionResponseInline
    inlines = [
        MentorQuestionResponseInline
    ]

    def stateFilteringAttributes(self, request):
        from coordination.models import Coordinator
        return {
            'school__state__coordinator__in': Coordinator.objects.filter(user=request.user)
        }
