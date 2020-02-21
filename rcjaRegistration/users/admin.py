from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Group
from .models import User

# Unregister group

admin.site.unregister(Group)

# User admin


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Define admin model for custom User model with no email field."""
    fieldsets = (
        (None, {'fields': (
            'email',
            'password'
        )}),
        (_('Personal info'), {'fields': (
            'first_name',
            'last_name',
            'mobileNumber'
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
        'is_staff',
        'is_superuser',
        'is_superuser',
        'is_active',
        'mobileNumber',
    ]
    search_fields = [
        'email',
        'first_name',
        'last_name',
    ]
