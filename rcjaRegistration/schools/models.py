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
    user = models.OneToOneField('auth.user', verbose_name='User', on_delete=models.PROTECT, editable=False, null=True, blank=True) # Temporary, need a way for super user to edit
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    # Name and email fields are stored on user model, no need to duplicate here
    firstName = models.CharField('First name', max_length=50)
    lastName = models.CharField('Last name', max_length=50)
    email = models.EmailField('Email', unique=True, help_text='Email is also username')
    mobileNumber = models.CharField('Phone Number', max_length=12)

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

    def preSave(self):
        self.updateUser()

    # Update User object
    def updateUser(self):
        # Username unique validation needed here
        if self.user:
            self.user.first_name = self.firstName
            self.user.last_name = self.lastName
            self.user.username = self.email
            self.user.email = self.email
            self.user.save()
        else:
            from django.contrib.auth.models import User
            self.user = User.objects.create(
                username=self.email,
                first_name=self.firstName,
                last_name=self.lastName,
                email=self.email
            )

    # Delete User object
    def deleteUser(self):
        if self.user:
            self.user.delete()

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return f'{self.firstName} {self.lastName}'

    # *****CSV export methods*****

    # *****Email methods*****
