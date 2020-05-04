from django.contrib import admin

from .models import *

from django.contrib.auth import get_permission_codename

def commonCheckStatePermissions(request, obj):
    # First check super user
    if request.user.is_superuser:
        return True

    # If no object return True because can't do state level filtering
    if obj is None:
        return True

    # Check state level filtering is possible
    if not hasattr(obj, 'getState'):
        return True

    return False

def checkStatePermissions(request, obj, permission):
    if commonCheckStatePermissions(request, obj):
        return True

    # Check state level permission for object
    for coordinator in Coordinator.objects.filter(Q(state=None) | Q(state=obj.getState()), user=request.user):
        if permission in obj.coordinatorPermissions(coordinator.permissions):
            return True

    return False

def checkStatePermissionsLevels(request, obj, permisisonLevels):
    if commonCheckStatePermissions(request, obj):
        return True

    # Check coordinator object
    return Coordinator.objects.filter(Q(state=None) | Q(state=obj.getState()), user=request.user, permissions__in=permisisonLevels).exists()

def reversePermisisons(obj, permissions):
    levels = []
    for level in Coordinator.permissionsOptions:
        for permission in permissions:
            if permission in obj.coordinatorPermissions(level[0]):
                levels.append(level[0])
    return levels

class BaseAdminPermissions:
    @classmethod
    def filterQuerysetByState(cls, queryset, request, permisisonLevels):
        # Return complete queryset if super user
        if request.user.is_superuser:
            return queryset

        # Filter based on state coordinator
        # Use filter function as first priority
        if hasattr(cls, 'stateFilteringAttributes'):
            filteringAttributes = cls.stateFilteringAttributes(request)
            if isinstance(filteringAttributes, list):
                queryset = queryset.filter(*filteringAttributes)
            else:
                queryset = queryset.filter(**filteringAttributes)

            return queryset.distinct()

        # User filter string as second priority
        if hasattr(cls, 'stateFilterLookup'):
            filterString = cls.stateFilterLookup

            # Check for global coordinator and permissions for this model
            for coordinator in Coordinator.objects.filter(user=request.user, state=None, permissions__in=permisisonLevels).filter():
                return queryset

            filteringAttributes = {
                f'{filterString}__in': Coordinator.objects.filter(user=request.user),
                f'{filterString}__permissions__in': permisisonLevels,
            }

            return queryset.filter(**filteringAttributes).distinct()
        
        return queryset

    def get_queryset(self, request):
        # Get base queryset
        queryset = super().get_queryset(request)
        
        defaultPermissions = reversePermisisons(self.model, ['view', 'change'])
        permissions = getattr(self, 'stateFilteringPermissions', defaultPermissions)

        return self.filterQuerysetByState(queryset, request, permissions)

    # Foreign key filtering

    @classmethod
    def fieldsToFilterRequest(cls, request):
        return []

    @classmethod
    def fieldsToFilterObj(cls, request, obj):
        return []

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Filter by object
        objectFiltering = False
        for fieldToFilter in self.fieldsToFilterObj(request, self.obj):
            if db_field.name == fieldToFilter['field']:
                if self.obj is not None or fieldToFilter.get('filterNone', False):
                    queryset = fieldToFilter['queryset']
                    kwargs['queryset'] = queryset
                    objectFiltering = True

        # Filter by state
        if not request.user.is_superuser:
            for fieldToFilter in self.fieldsToFilterRequest(request):
                if db_field.name == fieldToFilter['field']:

                    if not objectFiltering:
                        queryset = fieldToFilter['fieldModel'].objects.all()

                    # Use defined permissions if present, else default to add and change on current model
                    defaultPermissions = reversePermisisons(self.model, ['add', 'change'])
                    permissions = fieldToFilter.get('permissions', defaultPermissions)
                    
                    queryset = fieldToFilter['fieldAdmin'].filterQuerysetByState(queryset, request, permissions)

                    kwargs['queryset'] = queryset

                    # Set required if specified
                    # Do with an if statement because never want to override to make false
                    if fieldToFilter.get('required', False):
                        kwargs['required'] = True

                    # Try and set the default to save admins time, but not if objectFiltering because might not be the ideal default
                    if queryset.count() == 1 and not objectFiltering:
                        kwargs['initial'] = queryset.first().id

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_autocomplete_fields(self, request):
        autocompleteFields = super().get_autocomplete_fields(request)

        for fieldToFilter in self.fieldsToFilterObj(request, self.obj):
            if (self.obj is not None or fieldToFilter.get('filterNone', False)) and not fieldToFilter.get('useAutocomplete', False):
                field = fieldToFilter['field']
                while field in autocompleteFields: autocompleteFields.remove(field)

        return autocompleteFields

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

    def checkStatePermissionsLevels(self, request, obj, permisisonLevels):
        return checkStatePermissionsLevels(request, obj, permisisonLevels)

    # Add permisison only needed for inline, defined there

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

class AdminPermissions(BaseAdminPermissions):
    def get_form(self, request, obj=None, **kwargs):
        self.obj = obj
        return super().get_form(request, obj, **kwargs)

class InlineAdminPermissions(BaseAdminPermissions):
    # Set parent obj on class so available to inline
    def get_formset(self, request, obj=None, **kwargs):
        self.obj = obj
        return super().get_formset(request, obj, **kwargs)

    def has_add_permission(self, request, obj):
        # Check django permissions and editing allowed
        if not (super().has_add_permission(request, obj) and self.checkModelEditingAllowed(obj)):
            return False

        # Check state permissions
        return self.checkStatePermissions(request, obj, 'add')
