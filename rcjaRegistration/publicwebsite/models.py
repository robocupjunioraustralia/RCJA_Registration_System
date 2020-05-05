from django.db import models
from common.models import *
from django.conf import settings

# **********MODELS**********

class CommitteeMember(CustomSaveDeleteModel):
    # Foreign keys
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='User', on_delete=models.CASCADE)
    state = models.ForeignKey('regions.State', verbose_name='State', on_delete=models.CASCADE) # Don't restrict to registration states because can assign to purely website states
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    position = models.CharField('Position', max_length=50)
    biography = models.TextField('Biography', blank=True)


    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Committee member'
        ordering = ['state', 'user']

    def clean(self):
        errors = []

        # Raise any errors
        if errors:
            raise ValidationError(errors)

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        if level in ['full', 'webeditor']:
            return [
                'add',
                'view',
                'change',
                'delete'
            ]
        elif level in ['viewall']:
            return [
                'view',
            ]
        
        return []

    # Used in state coordinator permission checking
    def getState(self):
        return self.state

    # *****Save & Delete Methods*****

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
        return f'{self.userName()}: {self.state}'

    # *****CSV export methods*****

    # *****Email methods*****
