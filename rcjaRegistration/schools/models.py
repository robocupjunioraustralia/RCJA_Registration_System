from django.db import models
from common.models import *

# **********MODELS**********

class School(CustomSaveDeleteModel):
    # Foreign keys
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=100, unique=True)
    abbreviation = models.CharField('Abbreviation', max_length=5, unique=True)
    # Details
    state = models.ForeignKey('regions.State', verbose_name='State', on_delete=models.PROTECT)
    region = models.ForeignKey('regions.Region', verbose_name='Region', on_delete=models.PROTECT, null=True) # because imported teams don't have this field
    joinKey = models.CharField('Join key', max_length=10, blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'School'
        ordering = ['name']

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        if level in ['full', 'schoolmanager']:
            return [
                'add',
                'view',
                'change',
                'delete'
            ]
        elif level in ['viewall', 'billingmanager']:
            return [
                'view',
            ]
        
        return []

    # Used in state coordinator permission checking
    def getState(self):
        return self.state

    # *****Save & Delete Methods*****

    def preSave(self):
        self.abbreviation = self.abbreviation.upper()

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return self.name

    # *****CSV export methods*****

    # *****Email methods*****

class Mentor(CustomSaveDeleteModel):
    # Foreign keys
    school = models.ForeignKey(School, verbose_name='School', on_delete=models.CASCADE)
    user = models.ForeignKey('auth.user', verbose_name='User', on_delete=models.PROTECT)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Mentor'
        ordering = ['user']

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        if level in ['full', 'schoolmanager']:
            return [
                'add',
                'view',
                'change',
                'delete'
            ]
        elif level in ['viewall', 'billingmanager']:
            return [
                'view',
            ]
        
        return []

    # Used in state coordinator permission checking
    def getState(self):
        return self.school.state

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return f'{self.user.get_full_name}'

    # *****CSV export methods*****

    # *****Email methods*****
