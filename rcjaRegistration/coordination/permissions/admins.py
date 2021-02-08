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
    def fkObjectFilterFields(cls, request, obj):
        return {}

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        # Filter by object
        objectFiltering = False # Need to track if object filtering applied for this field to use in coordinator permissions filtering
        try:
            # Get filtering parameters for this field. If no filtering is defined for this field KeyError will be caught below.
            filterParams = self.fkObjectFilterFields(request, self.obj)[db_field.name]

            # Filter queryset
            queryset = filterParams['queryset'] # Set variable so it can be used as basis in coordinator permissions filtering below
            kwargs['queryset'] = queryset
            objectFiltering = True

        except KeyError:
            # Catch cases where field not in fkFilterFields and ignore - no filtering required
            pass

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
            required = False
            if not request.user.is_superuser: # Never want to set required for superuser - is controlled only by field options on the model
                if request.user.isGobalCoordinator(globalPermissionLevels): # Different settings for state and global coordinator
                    required = filterParams.get('globalCoordinatorRequired', False)
                else:
                    required = filterParams.get('stateCoordinatorRequired', False)

            # Do with an if statement because never want to override to make false
            if required:
                kwargs['required'] = True

            # Try and set the default to save admins time, if there is only one option and the field is required
            if queryset.count() == 1 and required:
                kwargs['initial'] = queryset.first().id

        except KeyError:
            # Catch cases where field not in fkFilterFields and ignore - no filtering required
            pass

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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
