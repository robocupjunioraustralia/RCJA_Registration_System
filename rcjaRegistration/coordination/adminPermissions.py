from django.contrib import admin
# from common.admin import *

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

class AdminPermissions:
    def get_queryset(self, request):
        # Get base queryset
        qs = super().get_queryset(request)

        # Return complete queryset if super user
        if request.user.is_superuser:
            return qs

        # Filter based on state coordinator
        if hasattr(self, 'stateFilteringAttributes'):
            qs = qs.filter(**self.stateFilteringAttributes(request))

        return qs

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
        
        # Check state permissions
        return self.checkStatePermissions(request, obj, 'view')

    def has_change_permission(self, request, obj=None):
        # Check django permissions and editing allowed
        if not (super().has_change_permission(request, obj=obj) and self.checkModelEditingAllowed(obj)):
            return False

        # Check state permissions
        return self.checkStatePermissions(request, obj, 'change')

    def has_delete_permission(self, request, obj=None):
        # Check django permissions and editing allowed
        if not (super().has_delete_permission(request, obj=obj) and self.checkModelEditingAllowed(obj)):
            return False

        # Check state permissions
        return self.checkStatePermissions(request, obj, 'delete')
