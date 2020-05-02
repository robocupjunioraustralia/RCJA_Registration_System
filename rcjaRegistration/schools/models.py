from django.db import models
from common.models import *
from django.conf import settings

import re

# **********MODELS**********

class School(CustomSaveDeleteModel):
    # Foreign keys
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=100, unique=True)
    abbreviation = models.CharField('Abbreviation', max_length=5, unique=True, help_text="Abbreviation is used in the schedule and scoring system")
    # Details
    state = models.ForeignKey('regions.State', verbose_name='State', on_delete=models.PROTECT, null=True) # Needed because null on initial data import
    region = models.ForeignKey('regions.Region', verbose_name='Region', on_delete=models.PROTECT, null=True)
    postcode = models.CharField('Postcode', max_length=4, null=True, blank=True)
    # Flags
    forceSchoolDetailsUpdate = models.BooleanField('Force details update', default=False)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'School'
        ordering = ['name']

    def clean(self):
        errors = []

        # Check min length of abbreviation
        if not self.abbreviation or len(self.abbreviation) < 3:
            errors.append(ValidationError('Abbreviation must be at least three characters'))

        # Case insenstive abbreviation and name unique check
        if School.objects.filter(name__iexact=self.name).exclude(pk=self.pk).exists():
            errors.append(ValidationError('School with this name exists. Please ask your school administrator to add you.'))

        if School.objects.filter(abbreviation__iexact=self.abbreviation).exclude(pk=self.pk).exists():
            errors.append(ValidationError('School with this abbreviation exists. Please ask your school administrator to add you.'))

        # Validate school not using name or abbreviation reserved for independent entries
        if self.abbreviation.upper() == 'IND':
            errors.append(ValidationError('IND is reserved for independent entries. If you are an independent entry, you do not need to create a school.'))

        # TODO: use regex to catch similar
        if self.name.upper() == 'INDEPENDENT':
            errors.append(ValidationError('Independent is reserved for independent entries. If you are an independent entry, you do not need to create a school.'))

        # Validate postcode
        if self.postcode is not None:
            if not re.match(r"(^[0-9]+$)", self.postcode):
                errors.append(ValidationError('Postcode must be numeric'))

            if len(self.postcode) < 4:
                errors.append(ValidationError('Postcode too short'))

        # Raise any errors
        if errors:
            raise ValidationError(errors)

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
        elif level in ['viewall', 'billingmanager', 'eventmanager']:
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

class Campus(CustomSaveDeleteModel):
    # Foreign keys
    school = models.ForeignKey(School, verbose_name='School', on_delete=models.CASCADE)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=100, unique=True)
    postcode = models.CharField('Postcode', max_length=4, null=True, blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Campus'
        verbose_name_plural = 'Campuses'
        ordering = ['school', 'name']

    def clean(self):
        errors = []

        # Validate postcode
        if self.postcode is not None:
            if not re.match(r"(^[0-9]+$)", self.postcode):
                errors.append(ValidationError('Postcode must be numeric'))

            if len(self.postcode) < 4:
                errors.append(ValidationError('Postcode too short'))

        # Raise any errors
        if errors:
            raise ValidationError(errors)

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        return School.coordinatorPermissions(level)

    # Used in state coordinator permission checking
    def getState(self):
        return self.school.state

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return f'{self.name}'

    # *****CSV export methods*****

    # *****Email methods*****  

class SchoolAdministrator(CustomSaveDeleteModel):
    # Foreign keys
    school = models.ForeignKey(School, verbose_name='School', on_delete=models.CASCADE)
    campus = models.ForeignKey(Campus, verbose_name='Campus', on_delete=models.SET_NULL, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='User', on_delete=models.PROTECT)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'School administrator'
        unique_together = ('school', 'user')
        ordering = ['user']

    def clean(self):
        checkRequiredFieldsNotNone(self, ['school', 'user'])
        # Check campus school matches school on this object
        if self.campus and self.campus.school != self.school:
            raise(ValidationError('Campus school must match school'))

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        return School.coordinatorPermissions(level)

    # Used in state coordinator permission checking
    def getState(self):
        return self.school.state

    # *****Save & Delete Methods*****

    def preSave(self):
        if self.pk:
            self.previousUser = SchoolAdministrator.objects.get(pk=self.pk).user

    def postSave(self):
        # Set currently selected school if not set
        if self.user.currentlySelectedSchool is None:
            self.user.currentlySelectedSchool = self.school
            self.user.save(update_fields=['currentlySelectedSchool'])

        if hasattr(self, 'previousUser',) and self.user != self.previousUser:
            self.previousUser.setCurrentlySelectedSchool()

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
        return f'{self.user.fullname_or_email()}'

    # *****CSV export methods*****

    # *****Email methods*****
