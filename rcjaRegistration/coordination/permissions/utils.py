
from django.db.models import Q
from django.contrib.auth import get_permission_codename

from coordination.models import Coordinator


def isGlobalObject(model, obj):
    # Why model and obj?

    # Models without getState are global across all states
    # But non super users won't have access unless stateCoordinatorPermissions() is defined
    if not hasattr(model, 'getState'):
        return True

    # Models with getState() and but with a blank state are global across all states
    # But non super users won't have access unless stateCoordinatorPermissions() is defined
    if hasattr(obj, 'getState') and obj.getState() is None:
        return True
    
    return False

def checkCoordinatorPermission(request, model, obj, permission):
    # Check user is active. Should be covered by Django checks, but additional safety.
    if not request.user.is_active:
        return False

    # Return true if super user
    if request.user.is_superuser:
        return True

    # Check has Django permission
    codename = get_permission_codename(permission, model._meta)
    if not request.user.has_perm(f'{model._meta.app_label}.{codename}'):
        return False

    # Check global coordinator permissions
    for coordinator in request.user.coordinator_set.filter(state=None):
        statePermissions = model.stateCoordinatorPermissions # Default to state permissions if globalCoordinatorPermissions not defined
        if permission in getattr(model, 'globalCoordinatorPermissions', statePermissions)(coordinator.permissionLevel):
            return True

    # Check for global objects
    # Have already checked the permissions for this object using the Django permissions
    # Global coordinator editing globals is handled above. This is only for state coordinators, who can only view global objects
    # And they can only view global objects if they have the permission in stateCoordinatorPermissions, the checking of which is handled above by Django permissions check
    # For an admin inline, this will check against the parent
    if isGlobalObject(model, obj) and permission == 'view':
        return True

    # Can now assume that object is not global and user is not superuser or global coordinator

    # Can't do state coordinator check if object is none
    # Return True because already tested that has the Django permission
    if obj is None:
        return True

    # Check state coordinator permissions
    for coordinator in Coordinator.objects.filter(state=obj.getState(), user=request.user):
        if permission in model.stateCoordinatorPermissions(coordinator.permissionLevel):
            return True

    # If nothing granting access, return False
    return False

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

def checkStatePermissionsLevels(request, obj, permisisonLevels):
    if commonCheckStatePermissions(request, obj):
        return True

    # Check coordinator object
    return Coordinator.objects.filter(Q(state=None) | Q(state=obj.getState()), user=request.user, permissionLevel__in=permisisonLevels).exists()

def reverseStatePermisisons(model, permissions):
    levels = []
    for level in Coordinator.permissionLevelOptions:
        for permission in permissions:
            if permission in model.stateCoordinatorPermissions(level[0]):
                levels.append(level[0])
    return levels

def reverseGlobalPermisisons(model, permissions):
    if not hasattr(model, 'globalCoordinatorPermissions'):
        return reverseStatePermisisons(model, permissions)

    levels = []
    for level in Coordinator.permissionLevelOptions:
        for permission in permissions:
            if permission in model.globalCoordinatorPermissions(level[0]):
                levels.append(level[0])
    return levels

def getFilteringPermissionLevels(model, permissions, permissionLevelOverride=None):
    # But what if empty list?
    statePermissionLevels = permissionLevelOverride or reverseStatePermisisons(model, permissions)
    globalPermissionLevels = permissionLevelOverride or reverseGlobalPermisisons(model, permissions)

    return statePermissionLevels, globalPermissionLevels
