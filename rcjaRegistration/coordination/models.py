from django.db import models
from common.models import *
from django.conf import settings

# **********MODELS**********

class Coordinator(CustomSaveDeleteModel):
    # Foreign keys
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='User', on_delete=models.CASCADE)
    state = models.ForeignKey('regions.state', verbose_name='State', on_delete=models.CASCADE, null=True, blank=True)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    permissionsOptions = (
        ('viewall', 'View all'),
        ('eventmanager', 'Event manager'),
        ('schoolmanager', 'School manager'),
        ('billingmanager', 'Billing manager'),
        ('full','Full'))
    permissions = models.CharField('Permissions', max_length=20, choices=permissionsOptions)
    position = models.CharField('Position', max_length=50)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Coordinator'
        constraints = [
            models.UniqueConstraint(fields=['user', 'permissions'], condition=Q(state=None), name='user_permissions'),
            models.UniqueConstraint(fields=['user', 'state', 'permissions'], name='user_state_permissions'),
        ]
        ordering = ['state', 'user']

    def clean(self):
        errors = []
        # Check required fields are not None
        checkRequiredFieldsNotNone(self, ['user', 'permissions', 'position'])

        # Check only one global coordinator per permission and user
        if Coordinator.objects.filter(user=self.user, permissions=self.permissions, state=self.state).exclude(pk=self.pk).exists():
            errors.append(ValidationError('Already coordinator for this user and permission level'))

        # Raise any errors
        if errors:
            raise ValidationError(errors)

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        if level in ['full']:
            return [
                'add',
                'view',
                'change',
                'delete'
            ]
        
        return []

    # Used in state coordinator permission checking
    def getState(self):
        return self.state

    # *****Save & Delete Methods*****
    def preSave(self):
        if self.pk:
            self.previousUser = Coordinator.objects.get(pk=self.pk).user
    
    def postSave(self):
        Coordinator.updateUserPermissions(user=self.user)

        if hasattr(self, 'previousUser',) and self.user != self.previousUser:
            Coordinator.updateUserPermissions(user=self.previousUser)

    def postDelete(self):
        Coordinator.updateUserPermissions(user=self.user)

    # *****Methods*****

    @classmethod
    def updateUserPermissions(cls, user):
        # Get coordinator objects for this user
        coordinators = Coordinator.objects.filter(user=user)

        # Staff flag
        user.is_staff = user.is_superuser or coordinators.exists()
        user.save()

        # Permissions

        # Get permissions for all models for all states that this user is a coordinator of
        permissionsToAdd = []

        import django.apps
        for coordinator in coordinators:
            for model in django.apps.apps.get_models():
                if hasattr(model, 'coordinatorPermissions'):
                    permissionsToAdd += map(lambda x: f'{x}_{model._meta.object_name.lower()}', getattr(model, 'coordinatorPermissions')(coordinator.permissions))

        # Add permissions to user
        from django.contrib.auth.models import Permission
        permissionObjects = Permission.objects.filter(codename__in=permissionsToAdd)
        user.user_permissions.clear()
        user.user_permissions.add(*permissionObjects)

    def checkPermission(self, obj, permission):
        return True if permission in obj.coordinatorPermissions(self.permissions) else False

    # *****Get Methods*****

    def userName(self):
        return self.user.fullname_or_email()
    userName.short_description = 'User'
    userName.admin_order_field = 'user'   

    def userEmail(self):
        return self.user.email
    userEmail.short_description = 'User email'
    userEmail.admin_order_field = 'user__email'

    def __str__(self):
        return f'{self.userName()}: {self.state}'

    # *****CSV export methods*****

    # *****Email methods*****
