from django.contrib import admin
from coordination.permissions import InlineAdminPermissions
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
    ]

    @classmethod
    def fkObjectFilterFields(cls, request, obj):
        return {
            'campus': {
                'queryset': Campus.objects.filter(school=obj), # Don't need to check for obj=None because not accessing an attribute
            },
        }
