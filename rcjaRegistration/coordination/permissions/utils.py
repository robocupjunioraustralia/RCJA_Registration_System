
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
    if isGlobalObject(model, obj):
        return permission == 'view'

    # Return True if object is None
    # Already tested that has the Django permission and can't do any further checks
    if obj is None:
        return True

    # State coordinator check

    # Check state coordinator permissions
    for coordinator in request.user.coordinator_set.filter(state=obj.getState()):
        if permission in model.stateCoordinatorPermissions(coordinator.permissionLevel):
            return True

    # If nothing granting access, return False
    return False

def checkCoordinatorPermissionLevel(request, obj, permisisonLevels):
    """
    Returns True if:
    - user is super user
    - user is global coordinator of specified permission level
    - user has a permission level in the supplied permissionLevels for the state of specified object
    """
    # Check user is active. Should be covered by Django checks, but additional safety.
    if not request.user.is_active:
        return False

    # Return true if super user
    if request.user.is_superuser:
        return True

    # Strict check = obj must not be None
    if obj is None:
        return False

    # Strict check = obj must have a State
    if not hasattr(obj, 'getState'):
        return False

    # Check coordinator object
    # Check for both global coordinator (state=None) and state coordinator (state=obj.getState())
    return request.user.coordinator_set.filter(Q(state=None) | Q(state=obj.getState()), permissionLevel__in=permisisonLevels).exists()

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
