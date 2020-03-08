from django.db import models
from common.models import *
from django.conf import settings

# **********MODELS**********

class Coordinator(CustomSaveDeleteModel):
    # Foreign keys
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='User', on_delete=models.CASCADE)
    state = models.ForeignKey('regions.state', verbose_name='State', on_delete=models.CASCADE)
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
    position = models.CharField('Position', max_length=50) # if want to tie permissions to this will need to set options. Without considerable work user will get permissions of most permissive state.

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Coordinator'
        unique_together = ('user', 'state')
        ordering = ['state', 'user']

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

    def postSave(self):
        self.updateUserPermissions()

    def postDelete(self):
        self.updateUserPermissions()

    # *****Methods*****

    def updateUserPermissions(self):
        # Get coordinator objects for this user
        coordinators = Coordinator.objects.filter(user=self.user)

        # Staff flag
        self.user.is_staff = self.user.is_superuser or coordinators.exists()
        self.user.save()

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
        self.user.user_permissions.clear()
        self.user.user_permissions.add(*permissionObjects)

    def checkPermission(self, obj, permission):
        return True if permission in obj.coordinatorPermissions(self.permissions) else False

    # *****Get Methods*****

    def __str__(self):
        return f'{self.user}: {self.state}'

    # *****CSV export methods*****

    # *****Email methods*****
