from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import Group

from common.admin import ExportCSVMixin
from coordination.adminPermissions import AdminPermissions, FilteredFKForm

from .models import User

from userquestions.admin import QuestionResponseInline

# Unregister group
admin.site.unregister(Group)

# User admin

class SchoolAdministratorInline(admin.TabularInline):
    from schools.models import SchoolAdministrator
    model = SchoolAdministrator
    extra = 0
    verbose_name = "School administrator of"
    verbose_name_plural = "School administrator of"
    autocomplete_fields = [
        'school',
        'campus',
    ]
    # Don't need to make read only here (unlike on the School admin) because only accessible to super users

class CoordinatorInline(admin.TabularInline):
    from coordination.models import Coordinator
    model = Coordinator
    extra = 0
    verbose_name = "Coordinator of"
    verbose_name_plural = "Coordinator of"

class User_QuestionResponse_Filter(admin.SimpleListFilter):
    title = "Question"
    parameter_name = "question"

    def lookups(self, request, model_admin):
        from userquestions.models import Question
        options = []
        for question in Question.objects.all():
            option = (question.id),question.shortTitle
            options.append(option)
        return options

    def queryset(self, request, queryset):
        try:
            return queryset.filter(questionresponse__response = True, questionresponse__question__id = int(self.value()))
        except (ValueError,TypeError):
            return queryset

from django.contrib.auth.forms import UserChangeForm, UserCreationForm

class Filtered_UserChangeForm(FilteredFKForm, UserChangeForm):
    pass

class Filtered_UserCreationForm(FilteredFKForm, UserCreationForm):
    pass

@admin.register(User)
class UserAdmin(AdminPermissions, DjangoUserAdmin, ExportCSVMixin):
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
            # 'groups',
            'user_permissions'
        )}),
        (_('Flags'), {'fields': (
            'forcePasswordChange',
            'forceDetailsUpdate',
        )}),
        (_('Important dates'), {'fields': (
            'last_login',
            'date_joined',
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
        (_('Personal info'), {
            'classes': ('wide',),
            'fields': (
                'first_name',
                'last_name',
                'mobileNumber',
                'homeState',
                'homeRegion',
            ),
        }),
    )
    ordering = ('email',)

    readonly_fields = DjangoUserAdmin.readonly_fields + (
        'user_permissions',
        'groups',
        'last_login',
        'date_joined',
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
        'homeState__name',
        'homeState__abbreviation',
        'homeRegion__name',
    ]
    list_filter = DjangoUserAdmin.list_filter + (
        'homeState',
        'homeRegion',
        User_QuestionResponse_Filter,
    )
    autocomplete_fields = [
        'homeState',
    ]
    actions = [
        'export_as_csv',
        'setForcePasswordChange',
        'setForceDetailsUpdate'
    ]
    exportFields = [
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
    exportFieldsManyRelations = ['questionresponse_set']

    # Set forceDetailsUpdate if a field is blank
    def save_model(self, request, obj, form, change):
        for field in ['first_name', 'last_name', 'mobileNumber', 'homeState', 'homeRegion']:
            if getattr(obj, field) is None:
                obj.forceDetailsUpdate = True
        
        super().save_model(request, obj, form, change)

    # State based filtering

    def fieldsToFilter(self, request):
        from coordination.adminPermissions import reversePermisisons
        from regions.models import State
        return [
            {
                'field': 'homeState',
                'required': True,
                'queryset': State.objects.filter(
                    coordinator__user=request.user,
                    coordinator__permissions='full',
                )
            }
        ]

    form = Filtered_UserChangeForm
    add_form = Filtered_UserCreationForm

    def stateFilteringAttributes(self, request):
        from coordination.models import Coordinator
        return {
            'homeState__coordinator__in': Coordinator.objects.filter(user=request.user)
        }

    # Only superuser can change permissions on users
    def get_readonly_fields(self, request, obj=None):
        if request.user.is_superuser:
            return self.readonly_fields
        return self.readonly_fields + ('is_staff','is_superuser', 'is_active')

    def get_inlines(self, request, obj):
        # Don't want to show inline on create user page
        if obj is None:
            return []

        # Only superuser can edit inlines on admin
        if request.user.is_superuser:
            return [
            SchoolAdministratorInline,
            CoordinatorInline,
            QuestionResponseInline,
        ]
        return [
            QuestionResponseInline,
        ]

    # Actions

    def setForcePasswordChange(self, request, queryset):
        queryset.update(forcePasswordChange=True)
    setForcePasswordChange.short_description = "Force password change"
    setForcePasswordChange.allowed_permissions = ('change',)

    def setForceDetailsUpdate(self, request, queryset):
        queryset.update(forceDetailsUpdate=True)
    setForceDetailsUpdate.short_description = "Require details update"
    setForceDetailsUpdate.allowed_permissions = ('change',)
