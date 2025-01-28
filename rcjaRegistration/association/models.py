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
    address = models.TextField('Residential address', blank=True)
    membershipStartDate = models.DateField('Membership start date', null=True, blank=True)
    membershipEndDate = models.DateField('Membership end date', null=True, blank=True)
    lifeMemberAwardedDate = models.DateField('Life membership awarded date', null=True, blank=True)
    approvalStatusChoices = (('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'))
    approvalStatus = models.CharField('Approval status', max_length=8, choices=approvalStatusChoices, default='pending')
    approvalRejectionDate = models.DateField('Approval/ rejection date', null=True, blank=True, editable=False)
    approvalRejectionBy = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Approved/ rejected by', on_delete=models.PROTECT, null=True, blank=True, related_name='approvalRejectionBy', editable=False)
    rulesAcceptedDate = models.DateField('Rules accepted date', null=True, blank=True, editable=False)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Association Member'
        ordering = ['user']

    def clean(self):
        errors = {}

        if self.membershipEndDate:
            if not self.membershipStartDate:
                errors['membershipStartDate'] = 'Membership start date must not be blank if membership end date set.'
            
            elif self.membershipStartDate >= self.membershipEndDate:
                errors['membershipStartDate'] = 'Membership start date must be before membership end date.'

        if self.under18() and self.address:
            errors['address'] = 'Address must be blank for members under 18.'
        
        if not self.under18() and not self.address:
            errors['address'] = 'Address must not be blank for members 18 and over.'

        # Prevent setting approvalStatus to approved if membershipStartDate or rulesAcceptedDate are blank
        if not self.membershipStartDate and self.approvalStatus == 'approved':
            errors['approvalStatus'] = 'Membership start date must be set before approval.'

        if not self.rulesAcceptedDate and self.approvalStatus == 'approved':
            if errors.get('approvalStatus'):
                errors['approvalStatus'] += ' Rules must be accepted before approval.'
            else:
                errors['approvalStatus'] = 'Rules must be accepted before approval.'

        # Raise any errors
        if errors:
            raise ValidationError(errors)

    # *****Permissions*****
    @classmethod
    def stateCoordinatorPermissions(cls, level):
        if level in ['full', 'associationmanager', 'viewall']:
            return [
                'view',
            ]

        return []

    @classmethod
    def globalCoordinatorPermissions(cls, level):
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

    def membershipExpired(self):
        return bool(
            self.membershipEndDate and
            self.membershipEndDate <= datetime.date.today()
        )

    def membershipActive(self):
        return bool(
            self.membershipStartDate and
            self.membershipStartDate <= datetime.date.today() and
            not self.membershipExpired()
        )
    membershipActive.short_description = 'Active'
    membershipActive.boolean = True

    def under18(self):
        if self.birthday is None:
            return None
        age = (datetime.date.today() - self.birthday) // datetime.timedelta(days=365.2425) # Because averaging leap years this could be off by a day or two
        return age < 18

    def membershipType(self):
        if self.under18() is None:
            return 'Not a member'
        if self.lifeMemberAwardedDate:
            return 'Life member'
        if not self.under18():
            return 'Ordinary'
        return 'Associate'
    membershipType.short_description = 'Membership type'

    def membershipStatus(self):
        if self.membershipActive() and self.approvalStatus == 'approved':
            return "Active"
        elif self.membershipActive() and self.approvalStatus == 'pending':
            return "Pending approval"
        elif self.membershipExpired():
            return 'Expired'
        else:
            return 'Not a member'

    def email(self):
        return self.user.email
    email.short_description = 'Email'

    def mobileNumber(self):
        return self.user.mobileNumber
    mobileNumber.short_description = 'Mobile number'

    def homeRegion(self):
        return self.user.homeRegion
    homeRegion.short_description = 'Region'

    def __str__(self):
        return str(self.user)

    # *****CSV export methods*****

    # *****Email methods*****
