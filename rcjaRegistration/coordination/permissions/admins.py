from .utils import coordinatorFilterQueryset, getFilteringPermissionLevels, checkCoordinatorPermission

class BaseAdminPermissions:
    @classmethod
    def filterQueryset(cls, queryset, request, statePermissionLevels, globalPermissionLevels):
        # Determine which filters to apply
        stateFilterLookup = getattr(cls, 'stateFilterLookup', False)
        globalFilterLookup = getattr(cls, 'globalFilterLookup', False)
    
        return coordinatorFilterQueryset(queryset, request, statePermissionLevels, globalPermissionLevels, stateFilterLookup, globalFilterLookup)

    def get_queryset(self, request):
        # Get base queryset
        queryset = super().get_queryset(request)

        permissionLevelOverride = getattr(self, 'filteringPermissionLevels', None)
        statePermissionLevels, globalPermissionLevels = getFilteringPermissionLevels(self.model, ['view', 'change'], permissionLevelOverride)

        return self.filterQueryset(queryset, request, statePermissionLevels, globalPermissionLevels)

    # Foreign key filtering

    fkFilterFields = {}

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

        # Filter by coordinator permissions
        try:
            # Get filtering parameters for this field. If no filtering is defined for this field KeyError will be caught below.
            filterParams = self.fkFilterFields[db_field.name]

            # Get admin and model classes
            objAdmin = filterParams['fieldAdmin']
            objModel = filterParams.get('fieldModel', objAdmin.fieldFilteringModel) # Use fieldModel attribute in filterParams, if not specified use model specified on the target admin

            # Get the base queryset
            # Use the queryset from object filtering if it exists, otherwise start with all objects
            if not objectFiltering:
                queryset = objModel.objects.all()

            # Get permission levels to filter queryset
            # Use defined permissions if present, otherwise default to add and change on current model
            permissionLevelOverride = filterParams.get('permissionLevels', None)
            statePermissionLevels, globalPermissionLevels = getFilteringPermissionLevels(self.model, ['add', 'change'], permissionLevelOverride)

            # Filter queryset
            queryset = objAdmin.filterQueryset(queryset, request, statePermissionLevels, globalPermissionLevels)
            kwargs['queryset'] = queryset

            # Set the field to required if specified in parameters
            if not request.user.is_superuser: # Never want to set required for superuser - is controlled only by field options on the model
                # Different settings for state and global coordinator
                if request.user.isGobalCoordinator(globalPermissionLevels):
                    # Do with an if statement because never want to override to make false
                    if filterParams.get('globalCoordinatorRequired', False):
                        kwargs['required'] = True

                else:
                    # Do with an if statement because never want to override to make false
                    if filterParams.get('stateCoordinatorRequired', False):
                        kwargs['required'] = True

            # Try and set the default to save admins time, but not if objectFiltering because might result in the ideal default
            if queryset.count() == 1 and not objectFiltering:
                kwargs['initial'] = queryset.first().id

        except KeyError:
            # Catch cases where field not in fkFilterFields and ignore - no filtering required
            pass

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
        return super().has_view_permission(request, obj=obj) and checkCoordinatorPermission(request, self.model, obj, 'view')

    def has_change_permission(self, request, obj=None):
        return super().has_change_permission(request, obj=obj) and checkCoordinatorPermission(request, self.model, obj, 'change')

    def has_delete_permission(self, request, obj=None):
        return super().has_delete_permission(request, obj=obj) and checkCoordinatorPermission(request, self.model, obj, 'delete')

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
        return super().has_add_permission(request, obj) and checkCoordinatorPermission(request, self.model, obj, 'add')