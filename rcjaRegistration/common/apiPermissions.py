from rest_framework.permissions import BasePermission, SAFE_METHODS
from django.conf import settings

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

class CmsSecretPermission(BasePermission):
    """
    Requires that the request have an Authorization header of the form:
        Authorization: Bearer <CMS_JWT_SECRET>
    """
    def has_permission(self, request, view):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return False

        token = auth_header[len("Bearer "):]
        return token == settings.CMS_JWT_SECRET
