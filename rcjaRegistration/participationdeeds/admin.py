from django.contrib import admin
from common.adminMixins import ExportCSVMixin, FKActionsRemove
from coordination.permissions import AdminPermissions

from .models import ParticipationDeed


@admin.register(ParticipationDeed)
class ParticipationDeedAdmin(FKActionsRemove, AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        'submittedFullName',
        'submittedYearLevel',
        'parentName',
        'signedDateTime',
        'originalEvent',
        'school',
        'mentorUser',
        'isAttached',
    ]
    list_filter = [
        'originalEvent',
        'school',
    ]
    search_fields = [
        'submittedFirstName',
        'submittedLastName',
        'parentName',
        'originalEvent__name',
        'school__name',
        'mentorUser__email',
        'mentorUser__first_name',
        'mentorUser__last_name',
    ]
    readonly_fields = [
        'creationDateTime',
        'updatedDateTime',
        'signedDateTime',
        'isAttached',
        'bleachedParticipationDeedText',
        'ipAddress',
        'userAgent',
        'loggedInUser',
    ]
    autocomplete_fields = [
        'school',
        'mentorUser',
        'originalEvent',
    ]
    actions = ['export_as_csv']
    exportFields = [
        'submittedFirstName',
        'submittedLastName',
        'submittedYearLevel',
        'parentName',
        'signedDateTime',
        'originalEvent',
        'school',
        'mentorUser',
        'ipAddress',
        'loggedInUser',
    ]

    statePermissionsFilterLookup = 'originalEvent__state__coordinator'
    fieldFilteringModel = ParticipationDeed
    filterQuerysetOnSelected = True
    stateSelectedFilterLookup = 'originalEvent__state'
    yearSelectedFilterLookup = 'originalEvent__year'

    def has_change_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request, obj=None):
        return False
