from django.db import models
from common.models import SaveDeleteMixin, checkRequiredFieldsNotNone
from django.conf import settings
from django.core.exceptions import ValidationError

# **********MODELS**********

class AssociationMember(SaveDeleteMixin, models.Model):
    # Foreign keys
    user = models.OneToOneField(settings.AUTH_USER_MODEL, verbose_name='User', on_delete=models.PROTECT)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    birthday = models.DateField('Birthday')
    address = models.TextField('Address', blank=True)
    membershipStartDate = models.DateField('Membership start date', null=True, blank=True)
    membershipEndDate = models.DateField('Membership end date', null=True, blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Association Member'
        ordering = ['user']

    def clean(self):
        errors = {}

        if self.membershipEndDate:
            if not self.membershipStartDate:
                errors['membershipStartDate'] = 'Membership start date must not be blank if membership end date set'
            
            elif self.membershipStartDate >= self.membershipEndDate:
                errors['membershipStartDate'] = 'Membership start date must be before membership end date'

        # Raise any errors
        if errors:
            raise ValidationError(errors)

    # *****Permissions*****
    @classmethod
    def stateCoordinatorPermissions(cls, level):
        if level in ['full', 'associationmanager']:
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
        return self.user.homeState

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return str(self.user)

    # *****CSV export methods*****

    # *****Email methods*****
