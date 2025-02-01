from django.db import models
from django.db.models import F, Q
from common.models import SaveDeleteMixin, checkRequiredFieldsNotNone
from django.conf import settings
from django.core.exceptions import ValidationError

# **********MODELS**********

class Coordinator(SaveDeleteMixin, models.Model):
    # Foreign keys
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='User', on_delete=models.CASCADE)
    state = models.ForeignKey('regions.state', verbose_name='State', on_delete=models.CASCADE, null=True, blank=True) # Don't restrict to registration states to allow delegation of website administration
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    permissionLevelOptions = (
        ('viewall', 'View all'),
        ('eventmanager', 'Event manager'),
        ('schoolmanager', 'School manager'),
        ('billingmanager', 'Billing manager'),
        ('associationmanager', 'Association manager'),
        ('webeditor', 'Web editor'),
        ('full','Full'))
    permissionLevel = models.CharField('Permission level', max_length=20, choices=permissionLevelOptions)
    position = models.CharField('Position', max_length=50)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Coordinator'
        constraints = [
            models.UniqueConstraint(fields=['user', 'permissionLevel'], condition=Q(state=None), name='user_permissions'),
            models.UniqueConstraint(fields=['user', 'state', 'permissionLevel'], name='user_state_permissions'),
        ]
        ordering = ['state', 'user']

    def clean(self):
        errors = []
        # Check required fields are not None
        checkRequiredFieldsNotNone(self, ['user', 'permissionLevel', 'position'])

        # Check only one global coordinator per permissionLevel and user
        if Coordinator.objects.filter(user=self.user, permissionLevel=self.permissionLevel, state=self.state).exclude(pk=self.pk).exists():
            errors.append(ValidationError('Already coordinator for this user, permission level and state'))

        # Check user is member of association if new coordinator permission
        if not self.pk:
            from association.models import AssociationMember
            try:
                if not self.user.associationmember.rulesAcceptedDate:
                    errors.append(ValidationError('User must accept Association rules before being a coordinator'))
            except AssociationMember.DoesNotExist:
                errors.append(ValidationError('User must be a member of the Association to be a coordinator'))

        # Raise any errors
        if errors:
            raise ValidationError(errors)

    # *****Permissions*****
    @classmethod
    def stateCoordinatorPermissions(cls, level):
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
        self.user.updateUserPermissions()

        if hasattr(self, 'previousUser',) and self.user != self.previousUser:
            self.previousUser.updateUserPermissions()

    # *****Methods*****

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
        if self.state:
            return f'{self.userName()}: {self.state} - {self.get_permissionLevel_display()}'
        return f'{self.userName()}: {self.get_permissionLevel_display()}'

    # *****CSV export methods*****

    # *****Email methods*****
