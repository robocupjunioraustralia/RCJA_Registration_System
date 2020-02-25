from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Group
from .models import User
from coordination.adminPermissions import AdminPermissions

# Unregister group

admin.site.unregister(Group)

# User admin

class SchoolAdministratorInline(admin.TabularInline):
    from schools.models import SchoolAdministrator
    model = SchoolAdministrator
    extra = 0
    verbose_name = "School administrator of"
    verbose_name_plural = "School administrator of"

@admin.register(User)
class UserAdmin(AdminPermissions, DjangoUserAdmin):
    """Define admin model for custom User model with no email field."""
    fieldsets = (
        (None, {'fields': (
            'email',
            'password'
        )}),
        (_('Personal info'), {'fields': (
            'first_name',
            'last_name',
            'mobileNumber',
            'homeState',
            'homeRegion',
        )}),
        (_('Permissions'), {'fields': (
            'is_active',
            'is_staff',
            'is_superuser',
            'groups',
            'user_permissions'
        )}),
        (_('Important dates'), {'fields': (
            'last_login',
            'date_joined'
        )}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'password1',
                'password2'
            ),
        }),
    )
    ordering = ('email',)

    readonly_fields = DjangoUserAdmin.readonly_fields + (
        'user_permissions',
        'groups',
    )
    list_display = [
        'email',
        'first_name',
        'last_name',
        'mobileNumber',
        'homeState',
        'homeRegion',
        'is_staff',
        'is_superuser',
        'is_active',
    ]
    search_fields = [
        'email',
        'first_name',
        'last_name',
        'mobileNumber',
    ]
    inlines = [
        SchoolAdministratorInline,
    ]

    def stateFilteringAttributes(self, request):
        from coordination.models import Coordinator
        return {
            'homeState__coordinator__in': Coordinator.objects.filter(user=request.user)
        }
