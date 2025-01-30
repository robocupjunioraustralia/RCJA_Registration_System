from django.contrib import admin
from common.adminMixins import ExportCSVMixin, DifferentAddFieldsMixin, FKActionsRemove
from coordination.permissions import AdminPermissions, InlineAdminPermissions

from .models import AssociationMember
from users.admin import UserAdmin
from users.models import User

import datetime

@admin.register(AssociationMember)
class SchoolAdmin(FKActionsRemove, AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        '__str__',
        'getState',
        'membershipActive',
        'membershipType',
        'approvalStatus',
        'membershipStartDate',
        'membershipEndDate',
    ]
    readonly_fields = [
        'getState',
        'homeRegion',
        'email',
        'mobileNumber',
        'membershipActive',
        'membershipType',
        'rulesAcceptedDate',
        'approvalRejectionBy',
        'approvalRejectionDate',
    ]
    fieldsets = [
        ('User details', {
            'fields': [
                'user',
                'birthday',
                'address',
                'email',
                'mobileNumber',
                'getState',
                'homeRegion',
            ]
        }),
        ('Membership details', {
            'fields': [
                'membershipStartDate',
                'membershipEndDate',
                'lifeMemberAwardedDate',
                'membershipType',
                'membershipActive',
                'rulesAcceptedDate',
            ]
        }),
        ('Approval details', {
            'fields': [
                'approvalStatus',
                'approvalRejectionBy',
                'approvalRejectionDate',
            ]
        }),
    ]
    list_filter = [
        ('user__homeState', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__email',
        'user__homeState__name',
        'user__homeState__abbreviation',
        'user__homeRegion__name',
        'user__email',
        'user__mobileNumber',
    ]
    autocomplete_fields = [
        'user'
    ]
    actions = [
        'export_as_csv',
    ]
    exportFields = [
        'pk',
        'user',
        'email',
        'mobileNumber',
        'homeRegion',
        'birthday',
        'address',
        'membershipActive',
        'membershipType',
        'membershipStartDate',
        'membershipEndDate',
    ]

    # Set approvalRejectionBy and approvedDate
    def save_model(self, request, obj, form, change):
        if obj.approvalRejectionBy is None and obj.approvalStatus != 'pending':
            obj.approvalRejectionBy = request.user
        
        if obj.approvalRejectionDate is None and obj.approvalStatus != 'pending':
            obj.approvalRejectionDate = datetime.date.today()
        
        super().save_model(request, obj, form, change)

    def get_readonly_fields(self, request, obj):
        readonly_fields = super().get_readonly_fields(request, obj).copy()

        if obj is None:
            return readonly_fields

        # Make approvalStatus readonly if not pending
        if obj.approvalStatus != 'pending' and obj.approvalRejectionDate:
            readonly_fields += ['approvalStatus']

        return readonly_fields

    # State based filtering

    fkFilterFields = {
        'user': {
            'fieldAdmin': UserAdmin,
            'fieldModel': User,
        },
    }

    statePermissionsFilterLookup = 'user__homeState__coordinator'
