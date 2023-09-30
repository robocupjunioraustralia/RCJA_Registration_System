from django.db import models
from common.models import SaveDeleteMixin, checkRequiredFieldsNotNone
from django.conf import settings
from django.core.exceptions import ValidationError

import datetime

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
    getState.short_description = 'State'

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def activeMembership(self):
        return bool(
            self.membershipStartDate and
            self.membershipStartDate <= datetime.date.today() and
            (not self.membershipEndDate or self.membershipEndDate > datetime.date.today())
        )
    activeMembership.short_description = 'Active'
    activeMembership.boolean = True

    def membershipType(self):
        age = (datetime.date.today() - self.birthday) // datetime.timedelta(days=365.2425) # Because averaging leap years could be off by a day or two
        if age >= 18:
            return 'Ordinary'
        else:
            return 'Associate'
    membershipType.short_description = 'Membership type'

    def __str__(self):
        return str(self.user)

    # *****CSV export methods*****

    # *****Email methods*****
