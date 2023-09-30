from django.contrib import admin
from common.adminMixins import ExportCSVMixin, DifferentAddFieldsMixin, FKActionsRemove
from coordination.permissions import AdminPermissions, InlineAdminPermissions

from .models import AssociationMember
from users.admin import UserAdmin
from users.models import User

# Register your models here.

@admin.register(AssociationMember)
class SchoolAdmin(FKActionsRemove, AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        '__str__',
    ]
    list_filter = [
        ('user__homeState', admin.RelatedOnlyFieldListFilter),
    ]
    search_fields = [
        'user__first_name',
        'user__last_name',
        'user__email',
        'user__homeState__name',
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
        'birthday',
        'address',
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
