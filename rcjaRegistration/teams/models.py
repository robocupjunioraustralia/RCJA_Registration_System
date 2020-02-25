from django.db import models
from common.models import *

from invoices.models import Invoice

# **********MODELS**********

class Team(CustomSaveDeleteModel):
    # Foreign keys
    event = models.ForeignKey('events.Event', verbose_name='Event', on_delete=models.CASCADE)
    division = models.ForeignKey('events.Division', verbose_name='Division', on_delete=models.PROTECT)

    # User and school foreign keys
    mentorUser = models.ForeignKey('users.User', verbose_name='Mentor', on_delete=models.PROTECT)
    school = models.ForeignKey('schools.School', verbose_name='School', on_delete=models.PROTECT, null=True, blank=True)
    campus = models.ForeignKey('schools.Campus', verbose_name='Campus', on_delete=models.PROTECT, null=True, blank=True)

    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)

    # Fields
    name = models.CharField('Name', max_length=50)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Team'
        unique_together = ('event', 'name')
        ordering = ['event', 'school', 'division', 'name']

    def clean(self, cleanDownstreamObjects=True):
        # Check campus school matches school on this object
        if self.campus and self.campus.school != self.school:
            raise(ValidationError('Campus school must match school'))

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        if level in ['full', 'eventmanager']:
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
        return self.event.state

    # *****Save & Delete Methods*****

    def postSave(self):
        # Create invoice
        if self.campusInvoicingEnabled():
            # Get or create invoice with matching campus
            Invoice.objects.get_or_create(
                school=self.school,
                campus=self.campus,
                event=self.event,
                defaults={'invoiceToUser': self.mentorUser}
            )

        elif self.school:
            # Ignore campus and only look for matching school
            Invoice.objects.get_or_create(
                school=self.school,
                event=self.event,
                defaults={'invoiceToUser': self.mentorUser}
            )

        else:
            # Get invoice for this user for independent entry
            Invoice.objects.get_or_create(
                invoiceToUser=self.mentorUser,
                event=self.event,
                school=None
            )

    # *****Methods*****

    # *****Get Methods*****

    # Returns true if campus based invoicing enabled for this school for this event
    def campusInvoicingEnabled(self):
        if not self.school:
            return False

        # Check if at least one invoice has campus field set
        return Invoice.objects.filter(school=self.school, event=self.event, campus__isnull=False).exists()

    def __str__(self):
        return self.name

    # *****CSV export methods*****

    # *****Email methods*****

class Student(models.Model):
    # Foreign keys
    team = models.ForeignKey(Team, verbose_name='Team', on_delete=models.CASCADE)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    firstName = models.CharField('First name', max_length=50)
    lastName = models.CharField('Last name', max_length=50)
    yearLevel = models.PositiveIntegerField('Year level')
    genderOptions = (('male','Male'),('female','Female'),('other','Other'))
    gender = models.CharField('Gender', choices=genderOptions, max_length=10)
    birthday = models.DateField('Birthday')

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Student'
        ordering = ['team', 'lastName', 'firstName']

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        if level in ['full', 'eventmanager']:
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
        return self.team.event.state

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return f'{self.firstName} {self.lastName}'

    # *****CSV export methods*****

    # *****Email methods*****
