
from django.db.models import Q

from coordination.models import Coordinator

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

def checkStatePermissions(request, obj, permission, permissionsModel=None):
    if commonCheckStatePermissions(request, obj):
        return True

    if permissionsModel is None:
        permissionsModel = obj

    # Check state level permission for object
    for coordinator in Coordinator.objects.filter(Q(state=None) | Q(state=obj.getState()), user=request.user):
        if permission in permissionsModel.stateCoordinatorPermissions(coordinator.permissionLevel):
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
