from django.contrib import admin
from django.db.models import F, Q

from django.http import HttpResponseRedirect, HttpResponse
from django.core.exceptions import FieldDoesNotExist, ValidationError

from django.utils.html import format_html, escape
from django.contrib import messages
from django.urls import reverse
from django.shortcuts import render

import csv
import datetime
import keyvaluestore.admin

# Register your models here.

# **********Action Mixins**********

class ExportCSVMixin:
    def export_as_csv(self, request, queryset):

        fields = self.exportFields

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename={self.model._meta.verbose_name_plural.title()} {datetime.date.today()}.csv'
        writer = csv.writer(response)

        # Get field display names
        fieldHeaderNames = []
        for field in fields:
            try:
                fieldHeaderNames.append(self.model._meta.get_field(field).verbose_name)
            except FieldDoesNotExist: # If field doesn't exist is a callable and should use short_description
                try:
                    fieldHeaderNames.append(getattr(self.model, field).short_description)
                except AttributeError: # If no short_description defined use field name
                    fieldHeaderNames.append(field)

        # Get field names for many to many objects
        manyFieldHeaderDicts = []

        # Go through all related objects on all objects in queryset for all fields and add unique headers to list
        if hasattr(self, 'exportFieldsManyRelations'):
            for field in self.exportFieldsManyRelations:
                for obj in queryset:
                    for manyObj in getattr(obj, field).all():
                        for headerDict in manyObj.csvHeaders():
                            if headerDict not in manyFieldHeaderDicts:
                                manyFieldHeaderDicts.append(headerDict)
        
        # Sort headers and add to list without dicts
        def headerOrderField(headerDict):
            return headerDict['order']
        manyFieldHeaderDicts.sort(key=headerOrderField)
        manyFieldHeaderNames = [x['header'] for x in manyFieldHeaderDicts]

        # Write field names to CSV
        writer.writerow(fieldHeaderNames+manyFieldHeaderNames)

        # Get and write field data values to CSV for each object in queryset
        for obj in queryset:
            row = []
            # Write database fields and method fields
            for field in fields:
                fieldData = getattr(obj, field)
                if callable(fieldData):
                    row.append(fieldData())
                else:
                    row.append(fieldData)

            # Write many relation fields
            if hasattr(self, 'exportFieldsManyRelations'):
                # Get dictionary of many values
                csvValues = {}
                for field in self.exportFieldsManyRelations:
                    for manyObj in getattr(obj, field).all():
                        csvValues = {**csvValues, **manyObj.csvValues()}

                # Add values to row
                for field in manyFieldHeaderNames:
                    try:
                        row.append(csvValues[field])
                    except KeyError:
                        row.append('') # append blank value if no value for this column

            writer.writerow(row)

        return response

    export_as_csv.short_description = "Export selected"
    export_as_csv.allowed_permissions = ('view',)

class DifferentAddFieldsMixin:
    """
    Adapted from Django UserAdmin methods.
    """
    def get_fieldsets(self, request, obj=None):
        if not obj and hasattr(self, 'add_fieldsets'):
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)

    def get_fields(self, request, obj=None):
        if not obj and hasattr(self, 'add_fields'):
            return self.add_fields
        return super().get_fields(request, obj)

    def get_inlines(self, request, obj):
        if not obj and hasattr(self, 'add_inlines'):
            return self.add_inlines
        return super().get_inlines(request, obj)

    def get_readonly_fields(self, request, obj):
        if not obj and hasattr(self, 'add_readonly_fields'):
            return self.add_readonly_fields
        return super().get_readonly_fields(request, obj)

    def response_add(self, request, obj, post_url_continue=None):
        """
        Determine the HttpResponse for the add_view stage. It mostly defers to
        its superclass implementation but is customized because the User model
        has a slightly different workflow.
        """
        # We should allow further modification of the user just added i.e. the
        # 'Save' button should behave like the 'Save and continue editing'
        # button except in two scenarios:
        # * The user has pressed the 'Save and add another' button
        # * We are adding a user in a popup
        from django.contrib.admin.options import IS_POPUP_VAR
        if '_addanother' not in request.POST and IS_POPUP_VAR not in request.POST:
            request.POST = request.POST.copy()
            request.POST['_continue'] = 1
        return super().response_add(request, obj, post_url_continue)

# Disable key-value store admin
admin.site.unregister(keyvaluestore.admin.KeyValueStore)

# Axes admin overrides

import axes.admin
from axes.admin import AccessLogAdmin as AxesAccessLogAdmin
from axes.admin import AccessAttemptAdmin as AxesAccessAttempAdmin
from axes.models import AccessLog, AccessAttempt

admin.site.unregister(axes.admin.AccessLog)
admin.site.unregister(axes.admin.AccessAttempt)

@admin.register(AccessLog)
class AccessLogAdmin(AxesAccessLogAdmin):
    def has_change_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request, obj=None):
        return False
    def has_delete_permission(self, request, obj=None):
        return False

@admin.register(AccessAttempt)
class AccessAttempAdmin(AxesAccessAttempAdmin):
    def has_change_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request, obj=None):
        return False

# Token admin overrides

from rest_framework.authtoken.admin import TokenAdmin as RestTokenAdmin
from rest_framework.authtoken.models import Token
import rest_framework

admin.site.unregister(rest_framework.authtoken.admin.Token)

@admin.register(Token)
class TokenAdmin(RestTokenAdmin):
    def has_change_permission(self, request, obj=None):
        return False
    def has_add_permission(self, request, obj=None):
        return False

    list_display = ['user', 'created']
