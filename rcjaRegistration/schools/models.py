from django.db import models
from common.models import SaveDeleteMixin, checkRequiredFieldsNotNone
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinLengthValidator

# **********MODELS**********

class School(SaveDeleteMixin, models.Model):
    # Foreign keys
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField(
        'Name',
        max_length=100,
        unique=True,
        validators=[RegexValidator(regex=r"^[0-9a-zA-Z \-\_]*$", message="Contains character that isn't allowed. Allowed characters are a-z, A-Z, 0-9, -_ and space.")]
    )
    # Details
    state = models.ForeignKey('regions.State', verbose_name='State', on_delete=models.PROTECT, null=True, limit_choices_to={'typeUserRegistration': True}) # Needed because null on initial data import
    region = models.ForeignKey('regions.Region', verbose_name='Region', on_delete=models.PROTECT, null=True)
    postcode = models.CharField(
        'Postcode',
        max_length=4,
        null=True,
        blank=True,
        validators=[
            RegexValidator(regex=r"^[0-9]*$", message="Postcode must be numeric"),
            MinLengthValidator(4, message="Postcode too short")
        ]
    )
    # Flags
    forceSchoolDetailsUpdate = models.BooleanField('Force details update', default=False)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'School'
        ordering = ['name']

    def clean(self):
        errors = {}

        # Case insenstive name unique check
        if School.objects.filter(name__iexact=self.name).exclude(pk=self.pk).exists():
            errors['name'] = 'School with this name exists. Please ask your school administrator to add you. If your school administrator has left, please contact us at entersupport@robocupjunior.org.au'

        # Validate school not using name reserved for independent entries
        # TODO: use regex to catch similar
        if self.name.upper() == 'INDEPENDENT':
            errors['name'] = 'Independent is reserved for independent entries. If you are an independent entry, you do not need to create a school.'

        # Validate region state
        if self.region and self.region.state is not None and self.region.state != self.state:
            errors['region'] = "Region not valid for selected state"

        # Raise any errors
        if errors:
            raise ValidationError(errors)

    # *****Permissions*****
    @classmethod
    def stateCoordinatorPermissions(cls, level):
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

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return self.name

    # *****CSV export methods*****

    # *****Email methods*****

class Campus(models.Model):
    # Foreign keys
    school = models.ForeignKey(School, verbose_name='School', on_delete=models.CASCADE)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=100, validators=[RegexValidator(regex=r"^[0-9a-zA-Z \-\_]*$", message="Contains character that isn't allowed. Allowed characters are a-z, A-Z, 0-9, -_ and space.")])
    postcode = models.CharField(
        'Postcode',
        max_length=4,
        null=True,
        blank=True,
        validators=[
            RegexValidator(regex=r"^[0-9]*$", message="Postcode must be numeric"),
            MinLengthValidator(4, message="Postcode too short")
        ]
    )

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Campus'
        verbose_name_plural = 'Campuses'
        ordering = ['school', 'name']
        unique_together = ('school', 'name')

    # *****Permissions*****
    @classmethod
    def stateCoordinatorPermissions(cls, level):
        return School.stateCoordinatorPermissions(level)

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

class SchoolAdministrator(SaveDeleteMixin, models.Model):
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
    def stateCoordinatorPermissions(cls, level):
        return School.stateCoordinatorPermissions(level)

    # Used in state coordinator permission checking
    def getState(self):
        return self.school.state

    # *****Save & Delete Methods*****

    def preSave(self):
        if self.pk:
            self.previousUser = SchoolAdministrator.objects.get(pk=self.pk).user
            self.previousSchool = SchoolAdministrator.objects.get(pk=self.pk).school

    def postSave(self):
        # Set currently selected school if not set
        if self.user.currentlySelectedSchool is None or (hasattr(self, 'previousSchool') and self.user.currentlySelectedSchool == self.previousSchool):
            self.user.currentlySelectedSchool = self.school
            self.user.save(update_fields=['currentlySelectedSchool'])

        if hasattr(self, 'previousUser') and self.user != self.previousUser:
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
        return f'{self.school}: {self.user.fullname_or_email()}'

    # *****CSV export methods*****

    # *****Email methods*****
