from django.db import models
from common.models import *
from django.conf import settings

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
    state = models.ForeignKey('regions.State', verbose_name='State', on_delete=models.PROTECT)
    region = models.ForeignKey('regions.Region', verbose_name='Region', on_delete=models.PROTECT)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'School'
        ordering = ['name']

    def clean(self):
        errors = []

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

class Campus(CustomSaveDeleteModel):
    # Foreign keys
    school = models.ForeignKey(School, verbose_name='School', on_delete=models.CASCADE)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=100, unique=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Campus'
        verbose_name_plural = 'Campuses'
        ordering = ['school', 'name']

    def clean(self, cleanDownstreamObjects=True):
        errors = []
 
        # Check school change doesn't effect any attached administrators
        cleanDownstream(self,'schooladministrator_set', 'campus', errors)
        cleanDownstream(self,'team_set', 'campus', errors)
    
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

    def clean(self, cleanDownstreamObjects=True):
        # Check campus school matches school on this object
        if self.campus and self.campus.school != self.school:
            raise(ValidationError('Campus school must match school'))

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

    def postSave(self):
        # Set currently selected school if not set
        if self.user.currentlySelectedSchool is None:
            self.user.currentlySelectedSchool = self.school
            self.user.save(update_fields=['currentlySelectedSchool'])

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return f'{self.user.get_full_name()}'

    # *****CSV export methods*****

    # *****Email methods*****
