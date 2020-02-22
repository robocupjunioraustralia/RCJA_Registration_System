from django.contrib import admin
from django.db.models import F, Q

from django.http import HttpResponseRedirect, HttpResponse
from django.core.exceptions import FieldDoesNotExist, ValidationError

from django.forms import TextInput, Textarea
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
    export_as_csv.allowed_permissions = ('change',)

# Disable key-value store admin
admin.site.unregister(keyvaluestore.admin.KeyValueStore)
