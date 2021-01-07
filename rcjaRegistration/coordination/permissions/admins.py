from .base import BaseAdminPermissions
from .utils import checkStatePermissions

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

