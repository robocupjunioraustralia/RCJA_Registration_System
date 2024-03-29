from django.db.models import Q
from django.core.exceptions import PermissionDenied
from django.contrib.auth import get_permission_codename

from coordination.models import Coordinator

def coordinatorFilterQueryset(queryset, user, statePermissionLevels, globalPermissionLevels, statePermissionsFilterLookup, globalPermissionsFilterLookup):
    # Check user and is authenticated
    # Queryset filtering should not be attempted for users not logged in.
    if user is None or not user.is_authenticated:
        raise PermissionDenied

    # Check user is active. Queryset filtering should not be attempted for inactive users.
    if not (user.is_active and user.is_staff):
        raise PermissionDenied

    # Return complete queryset if super user
    if user.is_superuser:
        return queryset

    # Global coordinator filtering
    # Return the entire queryset if the user is a global coordinator with permissions to this model
    if user.isGobalCoordinator(globalPermissionLevels):
        return queryset

    # If no filtering applied return base queryset
    if not (statePermissionsFilterLookup or globalPermissionsFilterLookup):
        return queryset

    stateQueryset = queryset.none()
    globalQueryset = queryset.none()

    # State filtering
    if statePermissionsFilterLookup:
        stateQueryset = queryset.filter(**{
            f'{statePermissionsFilterLookup}__in': user.coordinator_set.all(),
            f'{statePermissionsFilterLookup}__permissionLevel__in': statePermissionLevels,
        })

    # Global object filtering
    if globalPermissionsFilterLookup:
        # Means model has a relationship to state, want only stateless objects
        globalQueryset = queryset.filter(**{
            globalPermissionsFilterLookup: None,
        })

    return (stateQueryset | globalQueryset).distinct()

def selectedFilterQueryset(cls, queryset, user):
    selectedFilterDict = {}

    stateSelectedFilterLookup = getattr(cls, 'stateSelectedFilterLookup', None)
    if stateSelectedFilterLookup and user.currentlySelectedAdminState:
        selectedFilterDict[stateSelectedFilterLookup] = user.currentlySelectedAdminState

    yearSelectedFilterLookup = getattr(cls, 'yearSelectedFilterLookup', None)
    if yearSelectedFilterLookup and user.currentlySelectedAdminYear:
        selectedFilterDict[yearSelectedFilterLookup] = user.currentlySelectedAdminYear

    return queryset.filter(**selectedFilterDict)

def isGlobalObject(model, obj):
    # Models without getState are global across all states
    # But non super users won't have access unless stateCoordinatorPermissions() is defined
    # Use model (rather than obj) in case obj is none, checking if getState is defined on the class
    if not hasattr(model, 'getState'):
        return True

    # Models with getState() and but with a blank state are global across all states
    # But non super users won't have access unless stateCoordinatorPermissions() is defined
    if hasattr(obj, 'getState') and obj.getState() is None:
        return True

    return False

def checkCoordinatorPermission(request, model, obj, permission):
    # Check user exists and is authenticated
    # Should probably never be passed request.user = None but better to check
    if request.user is None or not request.user.is_authenticated:
        return False

    # Check user is active. Should be covered by Django checks, but additional safety.
    if not (request.user.is_active and request.user.is_staff):
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
        return permission == 'view' and getattr(model, 'stateCoordinatorViewGlobal', False)

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
    # Check user exists and is authenticated
    # Should probably never be passed request.user = None but better to check
    if request.user is None or not request.user.is_authenticated:
        return False

    # Check user is active. Should be covered by Django checks, but additional safety.
    if not (request.user.is_active and request.user.is_staff):
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

def getFilteringPermissionLevels(objectModel, permissions, permissionLevelOverride=None):
    def reversePermissionsBase(permissionModel, objectModel, permissionsLookupName, permissions):
        levels = []
        for level in permissionModel.permissionLevelOptions:
            for permission in permissions:
                if permission in getattr(objectModel, permissionsLookupName)(level[0]):
                    levels.append(level[0])
        return levels

    def reverseStatePermisisons(objectModel, permissions):
        return reversePermissionsBase(Coordinator, objectModel, 'stateCoordinatorPermissions', permissions)

    def reverseGlobalPermisisons(objectModel, permissions):
        if not hasattr(objectModel, 'globalCoordinatorPermissions'):
            return reverseStatePermisisons(objectModel, permissions)
        
        return reversePermissionsBase(Coordinator, objectModel, 'globalCoordinatorPermissions', permissions)

    # Need to use ternary to check for None and not just anything that evaluates to false, such as an empty list
    statePermissionLevels = permissionLevelOverride if permissionLevelOverride is not None else reverseStatePermisisons(objectModel, permissions)
    globalPermissionLevels = permissionLevelOverride if permissionLevelOverride is not None else reverseGlobalPermisisons(objectModel, permissions)

    return statePermissionLevels, globalPermissionLevels
