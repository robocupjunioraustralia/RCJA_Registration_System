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

    def teamPK(self):
        return self.team.pk
    teamPK.short_description = 'Team PK'

    # *****CSV export methods*****

    # Returns index of this group membship in queryset of groupMemberships for this group
    def getStudentNumber(self):
        students = self.team.student_set.all()
        studentNumber = 1 # Start at 1 not 0 because columns should start at 1 not 0
        for student in students:
            if student == self:
                return studentNumber
            studentNumber += 1

    # List of all csv headers for instance of this model
    def csvHeaders(self):
        studentNumber = self.getStudentNumber()
        return [
            {'header': f'Member {studentNumber} First Name', 'order': f'{studentNumber}a'},
            {'header': f'Member {studentNumber} Last Name', 'order': f'{studentNumber}b'},
            {'header': f'Member {studentNumber} Year Level', 'order': f'{studentNumber}c'},
            {'header': f'Member {studentNumber} Gender', 'order': f'{studentNumber}d'},
            {'header': f'Member {studentNumber} Birthday', 'order': f'{studentNumber}e'},
        ]

    # Dictionary of values for each header
    def csvValues(self):
        studentNumber = self.getStudentNumber()
        print(self.birthday)
        return {
            f'Member {studentNumber} First Name': self.firstName,
            f'Member {studentNumber} Last Name': self.lastName,
            f'Member {studentNumber} Year Level': self.yearLevel,
            f'Member {studentNumber} Gender': self.get_gender_display(),
            f'Member {studentNumber} Birthday': self.birthday.strftime("%d/%m/%Y"),
        }

    # *****Email methods*****
