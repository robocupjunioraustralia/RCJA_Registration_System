from .utils import checkStatePermissions, getFilteringPermissionLevels

from coordination.models import Coordinator

class BaseAdminPermissions:
    @classmethod
    def filterQuerysetByState(cls, queryset, request, statePermissionLevels, globalPermissionLevels):
        # Return complete queryset if super user
        if request.user.is_superuser:
            return queryset

        # Global coordinator filtering
        # Return the entire queryset if the user is a global coordinator with permissions to this model
        if request.user.coordinator_set.filter(state=None, permissionLevel__in=globalPermissionLevels).exists():
            return queryset

        # Determine which filters to apply
        stateFiltering = hasattr(cls, 'stateFilterLookup')
        globalFiltering = hasattr(cls, 'globalFilterLookup')

        # If no filtering applied return base queryset
        if not (stateFiltering or globalFiltering):
            return queryset

        stateQueryset = queryset.none()
        globalQueryset = queryset.none()

        # State filtering
        if stateFiltering:

            filterString = cls.stateFilterLookup

            stateQueryset = queryset.filter(**{
                f'{filterString}__in': request.user.coordinator_set.all(),
                f'{filterString}__permissionLevel__in': statePermissionLevels,
            })

        # Global object filtering
        if globalFiltering:

            filterString = cls.globalFilterLookup

            if filterString is None:
                # Means no relationship to state
                # Simply return the full queryset
                return queryset
            
            else:
                # Means model has a relationship to state, want only stateless objects
                globalQueryset = queryset.filter(**{
                    filterString: None,                    
                })

        return (stateQueryset | globalQueryset).distinct()

    def get_queryset(self, request):
        # Get base queryset
        queryset = super().get_queryset(request)

        permissionLevelOverride = getattr(self, 'filteringPermissionLevels', None)
        statePermissionLevels, globalPermissionLevels = getFilteringPermissionLevels(self.model, ['view', 'change'], permissionLevelOverride)

        return self.filterQuerysetByState(queryset, request, statePermissionLevels, globalPermissionLevels)

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

                    objAdmin = fieldToFilter['fieldAdmin']
                    # Use fieldModel attribute in fieldToFilter, if not specified use model specified on the target admin
                    objModel = fieldToFilter.get('fieldModel', objAdmin.fieldFilteringModel)

                    if not objectFiltering:
                        queryset = objModel.objects.all()

                    # Use defined permissions if present, else default to add and change on current model
                    permissionLevelOverride = fieldToFilter.get('permissionLevels', None)
                    statePermissionLevels, globalPermissionLevels = getFilteringPermissionLevels(self.model, ['add', 'change'], permissionLevelOverride)

                    queryset = objAdmin.filterQuerysetByState(queryset, request, statePermissionLevels, globalPermissionLevels)

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

    # Add permisison only needed for inline, defined there

    def has_view_permission(self, request, obj=None):
        # Check django permissions
        if not super().has_view_permission(request, obj=obj):
            return False
        
        # Allow viewing of global objects
        if hasattr(obj, 'getState') and obj.getState() is None:
            return True

        # Check state permissions
        return checkStatePermissions(request, obj, 'view')

    def has_change_permission(self, request, obj=None):
        # Check django permissions
        if not super().has_change_permission(request, obj=obj):
            return False

        # Only superuser can change or delete global objects
        if hasattr(obj, 'getState') and obj.getState() is None and not request.user.is_superuser:
            return False

        # Check state permissions
        return checkStatePermissions(request, obj, 'change', permissionsModel=self.model)

    def has_delete_permission(self, request, obj=None):
        # Check django permissions
        if not super().has_delete_permission(request, obj=obj):
            return False

        # Only superuser can change or delete global objects
        if hasattr(obj, 'getState') and obj.getState() is None and not request.user.is_superuser:
            return False

        # Check state permissions
        return checkStatePermissions(request, obj, 'delete', permissionsModel=self.model)


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
        # Check django permissions
        if not super().has_add_permission(request, obj):
            return False

        # Check state permissions
        return checkStatePermissions(request, obj, 'add', permissionsModel=self.model)
