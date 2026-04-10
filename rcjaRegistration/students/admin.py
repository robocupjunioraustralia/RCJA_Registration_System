from django.contrib import admin
from common.adminMixins import ExportCSVMixin, FKActionsRemove
from coordination.permissions import AdminPermissions, InlineAdminPermissions
from django.contrib import messages
from django.forms import Textarea
from django.db import models
from common.filters import FilteredRelatedOnlyFieldListFilter
from django.utils.html import format_html
from django.urls import reverse

from .models import Student

# Register your models here.


@admin.register(Student)
class StudentAdmin(FKActionsRemove, AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        "__str__",
    ]
    search_fields = [
        "firstName",
        "lastName",
        "school__state__name",
        "school__state__abbreviation",
        "school__region__name",
        "school__name",
        "campus__name",
    ]
    actions = ["export_as_csv"]
    exportFields = [
        "pk",
        "firstName",
        "lastName",
        "yearLevel",
        "gender",
    ]

    filterQuerysetOnSelected = True


"""
@admin.register(Student)
class StudentAdmin(FKActionsRemove, AdminPermissions, admin.ModelAdmin, ExportCSVMixin):
    list_display = [
        '__str__',
        'team',
    ]
    autocomplete_fields = [
        'team',
    ]
    list_filter = [
        ('team__event', FilteredRelatedOnlyFieldListFilter),
        ('team__division', FilteredRelatedOnlyFieldListFilter),
    ]
    search_fields = [
        'firstName',
        'lastName',
        'team__name',
        'team__school__state__name',
        'team__school__state__abbreviation',
        'team__school__region__name',
        'team__school__name',
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
        'pk',
        'team',
        'teamPK',
        'firstName',
        'lastName',
        'yearLevel',
        'gender',
    ]

    # State based filtering

    fkFilterFields = {
        'team': {
            'fieldAdmin': TeamAdmin,
        },
    }

    statePermissionsFilterLookup = 'team__event__state__coordinator'
    filterQuerysetOnSelected = True
    stateSelectedFilterLookup = 'team__event__state'
    yearSelectedFilterLookup = 'team__event__year'
"""
