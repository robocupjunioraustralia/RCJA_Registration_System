from django.db import models
from django.core.exceptions import ValidationError

from events.models import BaseEventAttendance, eventCoordinatorEditPermissions, eventCoordinatorViewPermissions

# **********MODELS**********

class HardwarePlatform(models.Model):
    # Foreign keys
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=50)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Hardware Platform'
        ordering = ['name']

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        return eventCoordinatorViewPermissions(level)

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return self.name

    # *****CSV export methods*****

    # *****Email methods*****

class SoftwarePlatform(models.Model):
    # Foreign keys
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=50)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Software Platform'
        ordering = ['name']

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        return eventCoordinatorViewPermissions(level)

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return self.name

    # *****CSV export methods*****

    # *****Email methods*****

class Team(BaseEventAttendance):
    # Foreign keys
    hardwarePlatform = models.ForeignKey(HardwarePlatform, verbose_name='Hardware platform', on_delete=models.PROTECT, null=True, blank=True)
    softwarePlatform = models.ForeignKey(SoftwarePlatform, verbose_name='Software platform', on_delete=models.PROTECT, null=True, blank=True)

    # Fields
    name = models.CharField('Name', max_length=50)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Team'
        ordering = ['event', 'school', 'division', 'name']

    eventTypeMapping = 'competition'

    def clean(self):
        super().clean()
        errors = []

        # Check team name unique
        if Team.objects.filter(event=self.event, name=self.name).exclude(pk=self.pk).exists():
            errors.append(ValidationError('Team with this name in this event already exists'))

        # Raise any errors
        if errors:
            raise ValidationError(errors)

    # *****Permissions*****

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return f"{self.name} ({self.event.name} {self.event.year})"

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
        return eventCoordinatorEditPermissions(level)

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
