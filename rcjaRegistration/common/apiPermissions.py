from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_active and
            request.user.is_superuser
        )

class AuthenticatedReadOnly(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and
            request.user.is_active and
            request.user.is_authenticated and
            request.method in SAFE_METHODS
        )

class ReadOnly(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.method in SAFE_METHODS
        )
