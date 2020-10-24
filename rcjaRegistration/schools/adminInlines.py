from django.contrib import admin
from coordination.adminPermissions import InlineAdminPermissions
from common.adminMixins import FKActionsRemove

from .models import SchoolAdministrator, Campus

class SchoolAdministratorInline(FKActionsRemove, InlineAdminPermissions, admin.TabularInline):
    model = SchoolAdministrator
    extra = 0
    verbose_name = "Administrator"
    verbose_name_plural = "Administrators"
    # Define fields to define order
    fields = [
        'user',
        'campus',
    ]
    autocomplete_fields = [
        'user',
        'campus',
    ]

    @classmethod
    def fieldsToFilterObj(cls, request, obj):
        return [
            {
                'field': 'campus',
                'queryset': Campus.objects.filter(school=obj),
                'filterNone': True
            }
        ]
