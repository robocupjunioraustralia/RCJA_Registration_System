from django.contrib import admin
from common.adminMixins import ExportCSVMixin, DifferentAddFieldsMixin, FKActionsRemove
from coordination.permissions import AdminPermissions, InlineAdminPermissions

from .models import AssociationMember
from users.admin import UserAdmin
from users.models import User

@admin.register(AssociationMember)
class SchoolAdmin(FKActionsRemove, AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        '__str__',
        'getState',
        'membershipActive',
        'membershipType',
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

    # State based filtering

    fkFilterFields = {
        'user': {
            'fieldAdmin': UserAdmin,
            'fieldModel': User,
        },
    }

    statePermissionsFilterLookup = 'user__homeState__coordinator'
