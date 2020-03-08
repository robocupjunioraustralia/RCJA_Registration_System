from django.contrib import admin
# from common.admin import *

from django import forms

from .models import *

from django.contrib.auth import get_permission_codename

def checkStatePermissions(request, obj, permission):
    # First check super user
    if request.user.is_superuser:
        return True

    # If no object return True because can't do state level filtering
    if obj is None:
        return True

    # Check state level filtering is possible
    if not hasattr(obj, 'getState'):
        return True

    # Check state level permission for object
    for coordinator in Coordinator.objects.filter(Q(state=None) | Q(state=obj.getState()), user=request.user):
        if coordinator.checkPermission(obj, permission):
            return True

    return False

def reversePermisisons(obj, permissions):
    levels = []
    for level in Coordinator.permissionsOptions:
        for permission in permissions:
            if permission in obj.coordinatorPermissions(level[0]):
                levels.append(level[0])
    return levels

class FilteredFKForm(forms.ModelForm):
    # Fitler foreign keys for state permissions
    def __init__(self, *args, **kwargs):
        request = kwargs.pop('request')
        fieldsToFilter = kwargs.pop('fieldsToFilter')
        super().__init__(*args, **kwargs)

        # Don't filter if super user
        if not request.user.is_superuser:
            for fieldToFilter in fieldsToFilter:
                try:
                    # Filter based on state with appropriate permissions
                    self.fields[fieldToFilter['field']].queryset = fieldToFilter['queryset']

                    # Set required if specified
                    try:
                        self.fields[fieldToFilter['field']].required = fieldToFilter['required']
                    except KeyError:
                        pass

                    # Try and set the default to save admins time
                    if fieldToFilter['queryset'].count() == 1:
                        self.fields[fieldToFilter['field']].initial = fieldToFilter['queryset'].first().id
                except KeyError:
                    return

class AdminPermissions:
    def get_queryset(self, request):
        # Get base queryset
        qs = super().get_queryset(request)

        # Return complete queryset if super user
        if request.user.is_superuser:
            return qs

        # Filter based on state coordinator
        if hasattr(self, 'stateFilteringAttributes'):
            filteringAttributes = self.stateFilteringAttributes(request)
            if isinstance(filteringAttributes, list):
                qs = qs.filter(*filteringAttributes)
            else:
                qs = qs.filter(**filteringAttributes)

        return qs

    # Foreign key filtering

    form = FilteredFKForm

    def fieldsToFilter(self, request):
        return []

    # Add request and other attributes required for filtering foreign keys
    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super().get_form(request, obj, **kwargs)

        class AdminFormWithAttributes(AdminForm):
            def __new__(cls, *args, **kwargs):
                kwargs['request'] = request
                kwargs['fieldsToFilter'] = self.fieldsToFilter(request)
                return AdminForm(*args, **kwargs)

        return AdminFormWithAttributes

    # Permissions

    def checkModelEditingAllowed(self, obj):
        # Try admin specific editingAllowed first
        try:
            return obj.editingAllowedAdmin()
        except AttributeError:
            pass
        # Revert to generic editing allowed, which may be more db intensive unnesecarily (in admin case because change form not registered, extra db calls still needed in api)
        try:
            return obj.editingAllowed()
        except AttributeError:
            return True

    def checkStatePermissions(self, request, obj, permission):
        return checkStatePermissions(request, obj, permission)

    def has_add_permission(self, request, obj=None):
        # Check django permissions and editing allowed
        if not (super().has_add_permission(request) and self.checkModelEditingAllowed(obj)):
            return False

        # Check state permissions
        return self.checkStatePermissions(request, obj, 'add')
    
    def has_view_permission(self, request, obj=None):
        # Check django permissions
        if not super().has_view_permission(request, obj=obj):
            return False
        
        # Allow viewing of global objects
        if hasattr(obj, 'getState') and obj.getState() is None:
            return True

        # Check state permissions
        return self.checkStatePermissions(request, obj, 'view')

    def has_change_permission(self, request, obj=None):
        # Check django permissions and editing allowed
        if not (super().has_change_permission(request, obj=obj) and self.checkModelEditingAllowed(obj)):
            return False

        # Only superuser can change or delete global objects
        if hasattr(obj, 'getState') and obj.getState() is None and not request.user.is_superuser:
            return False

        # Check state permissions
        return self.checkStatePermissions(request, obj, 'change')

    def has_delete_permission(self, request, obj=None):
        # Check django permissions and editing allowed
        if not (super().has_delete_permission(request, obj=obj) and self.checkModelEditingAllowed(obj)):
            return False

        # Only superuser can change or delete global objects
        if hasattr(obj, 'getState') and obj.getState() is None and not request.user.is_superuser:
            return False

        # Check state permissions
        return self.checkStatePermissions(request, obj, 'delete')
