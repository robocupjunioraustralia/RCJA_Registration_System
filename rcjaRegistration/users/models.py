from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import django.apps as djangoApps
from common.models import SaveDeleteMixin
from django.core.exceptions import PermissionDenied
from django.core.validators import RegexValidator

from django.contrib.auth.models import Permission

import re

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field"""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

    def get_by_natural_key(self, username):
        # Case insensitive username lookup
        return self.get(**{f'{self.model.USERNAME_FIELD}__iexact': username})

class User(SaveDeleteMixin, AbstractUser):
    """User model"""
    # Replace username with email
    username = None
    email = models.EmailField(_('email address'), unique=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    # Custom manager because no username field
    objects = UserManager()

    # Additional fields
    mobileNumber = models.CharField('Mobile number', max_length=12, null=True, blank=True, validators=[RegexValidator(regex="^[0-9a-zA-Z \-\_\(\)\+]*$", message="Contains character that isn't allowed. Allowed characters are a-z, A-Z, 0-9, -_()+ and space.")])
    homeState = models.ForeignKey('regions.State', verbose_name='Home state', on_delete=models.PROTECT, null=True, blank=True, limit_choices_to={'typeUserRegistration': True})
    homeRegion = models.ForeignKey('regions.Region', verbose_name='Home region', on_delete=models.PROTECT, null=True, blank=True)

    # Preferences and settings
    currentlySelectedSchool = models.ForeignKey('schools.School', verbose_name='Currently selected school', on_delete=models.SET_NULL, null=True, blank=True, editable=False)
    currentlySelectedAdminYear = models.ForeignKey('events.Year', verbose_name='Currently selected admin year', on_delete=models.SET_NULL, related_name='+', null=True, blank=True, editable=False)
    currentlySelectedAdminState = models.ForeignKey('regions.State', verbose_name='Currently selected admin state', on_delete=models.SET_NULL, related_name='+', null=True, blank=True, editable=False)
    adminChangelogVersionShown = models.PositiveIntegerField('Changelog version shown', editable=False, default=0)
    ADMIN_CHANGELOG_CURRENT_VERSION = 5

    # Flags
    forcePasswordChange = models.BooleanField('Force password change', default=False)
    forceDetailsUpdate = models.BooleanField('Force details update', default=False)

    # For axes to work
    backend = 'axes.backends.AxesBackend'

    # *****Clean*****

    def clean(self):
        super().clean()
        errors = {}

        # Force case insentive email
        if User.objects.filter(email__iexact=self.email).exclude(pk=self.pk).exists():
            errors['email'] = _('User with this email address already exists.')

        # Validate region state
        if self.homeRegion and self.homeRegion.state is not None and self.homeRegion.state != self.homeState:
            errors['homeRegion'] = "Region not valid for selected state"

        if not re.match("^[0-9a-zA-Z \-\_]*$", self.first_name):
            errors['first_name'] = "Contains character that isn't allowed. Allowed characters are a-z, A-Z, 0-9, -_ and space."

        if not re.match("^[0-9a-zA-Z \-\_]*$", self.last_name):
            errors['last_name'] = "Contains character that isn't allowed. Allowed characters are a-z, A-Z, 0-9, -_ and space."

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
            ]
        elif level in ['viewall', 'eventmanager', 'schoolmanager', 'billingmanager', 'webeditor']:
            return [
                'view',
            ]
        
        return []

    # Used in state coordinator permission checking
    def getState(self):
        return self.homeState

    # *****Save & Delete Methods*****

    def postSave(self):
        # Update user permissions in case is_superuser set or unset
        self.updateUserPermissions()

    # *****Methods*****

    def updateUserPermissions(self):
        # Get coordinator objects for this user
        coordinators = self.coordinator_set.all()

        # Staff flag
        self.is_staff = self.is_superuser or coordinators.exists()
        self.save(update_fields=['is_staff'], skipPrePostSave=True)

        # Permissions

        # Get permissions for all models for all states that this user is a coordinator of
        permissionsToAdd = []

        def addPermissions(permissionsToAdd, model, coordinator, permissionsLookupName):
            if hasattr(model, permissionsLookupName):
                permissionsToAdd += map(lambda x: f'{x}_{model._meta.object_name.lower()}', getattr(model, permissionsLookupName)(coordinator.permissionLevel))

        # Add permissions for each coordinator object
        for coordinator in coordinators:
            for model in djangoApps.apps.get_models():

                # If global coordinator add global permissions if they are defined
                # Otherwise add state permissions
                if coordinator.state is None and hasattr(model, 'globalCoordinatorPermissions'):
                    addPermissions(permissionsToAdd, model, coordinator, 'globalCoordinatorPermissions')

                else:
                    addPermissions(permissionsToAdd, model, coordinator, 'stateCoordinatorPermissions')

        # Add permissions to user
        permissionObjects = Permission.objects.filter(codename__in=permissionsToAdd)
        self.user_permissions.clear()
        self.user_permissions.add(*permissionObjects)

        # Set state filtering to None if no longer a coordinator of that state
        if self.currentlySelectedAdminState and not (self.is_superuser or coordinators.filter(state=self.currentlySelectedAdminState).exists()):
            self.currentlySelectedAdminState = None
            self.save(update_fields=['currentlySelectedAdminState'], skipPrePostSave=True)

    # Reset forcePasswordChange
    def set_password(self, password):
        super().set_password(password)
        self.forcePasswordChange = False

    def setCurrentlySelectedSchool(self):
        # Set currentlySelectedSchool to another school for this user or None if no other schools
        if self.schooladministrator_set.exists():
            self.currentlySelectedSchool = self.schooladministrator_set.first().school
        else:
            self.currentlySelectedSchool = None
        self.save(update_fields=['currentlySelectedSchool'])

    # *****Get Methods*****

    def isGobalCoordinator(self, permissionLevels):
        return self.coordinator_set.filter(state=None, permissionLevel__in=permissionLevels).exists()

    def adminViewableStates(self):
        from regions.models import State
        from regions.admin import StateAdmin
        from coordination.permissions import coordinatorFilterQueryset, getFilteringPermissionLevels

        statePermissionsFilterLookup = getattr(StateAdmin, 'statePermissionsFilterLookup', False)
        globalPermissionsFilterLookup = getattr(StateAdmin, 'globalPermissionsFilterLookup', False)

        statePermissionLevels, globalPermissionLevels = getFilteringPermissionLevels(State, ['view', 'change'])

        try:
            return coordinatorFilterQueryset(State.objects.all(), self, statePermissionLevels, globalPermissionLevels, statePermissionsFilterLookup, globalPermissionsFilterLookup)
        except PermissionDenied:
            return State.objects.none()

    def strSchoolNames(self):
        return ", ".join(map(lambda x: str(x.school), self.schooladministrator_set.all()))
    strSchoolNames.short_description = "Schools"

    def strSchoolPostcodes(self):
        return ", ".join(map(lambda x: str(x.school.postcode) if x.school.postcode else "", self.schooladministrator_set.all()))
    strSchoolPostcodes.short_description = "School postcodes"

    def fullname_or_email(self):
        return self.get_full_name() or self.email

    def __str__(self):
        if self.get_full_name():
            return f"{self.get_full_name()} ({self.email})"
        return self.email

    # *****CSV export methods*****

    # *****Email methods*****
