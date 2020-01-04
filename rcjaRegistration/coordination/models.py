from django.db import models
from common.models import *

# **********MODELS**********

class Coordinator(CustomSaveDeleteModel):
    # Foreign keys
    user = models.ForeignKey('auth.user', verbose_name='User', on_delete=models.CASCADE)
    state = models.ForeignKey('regions.state', verbose_name='State', on_delete=models.CASCADE)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    permissionsOptions = (('readonly','Read only'),('full','Full'))
    permissions = models.CharField('Permissions', max_length=20, choices=permissionsOptions)
    position = models.CharField('Position', max_length=50) # if want to tie permissions to this will need to set options. Without considerable work user will get permissions of most permissive state.

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Coordinator'
        unique_together = ('user', 'state')
        ordering = ['state', 'user']

    # *****Save & Delete Methods*****

    def postSave(self):
        pass
        # need to set user to staff and set desired permissions for state coordinators

    def postSave(self):
        pass
        # Need to reset staff flag and permissions, considering any other states still a coordinator of


    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return f'{self.user}: {self.state}'

    # *****CSV export methods*****

    # *****Email methods*****
