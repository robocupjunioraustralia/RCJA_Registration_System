from django.db import models
from common.models import *

# **********MODELS**********


class Profile(CustomSaveDeleteModel):
    # Foreign keys
    user = models.OneToOneField('auth.user', verbose_name='User', on_delete=models.CASCADE, editable=False) # Temporary, need a way for super user to edit
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    mobileNumber = models.CharField('Phone Number', max_length=12, null=True, blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Profile'
        ordering = ['user']

    # *****Permissions*****

    # *****Save & Delete Methods*****

    # Need to stop deleting of the model because creates orphaned user models, which casues errors. Would like to do through permissions but that prevents cascade delete from the user object in the django admin.
    def deletingAllowed(self):
        return False

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username}'

    # *****CSV export methods*****

    # *****Email methods*****
