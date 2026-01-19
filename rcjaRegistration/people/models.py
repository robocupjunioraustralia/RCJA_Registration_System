from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from common.models import SaveDeleteMixin
from django.conf import settings
import datetime

import re

from schools.models import School
from events.models import BaseEventAttendance, eventCoordinatorEditPermissions, eventCoordinatorViewPermissions

# **********MODELS**********

class Person(SaveDeleteMixin, models.Model):
    firstName = models.CharField('First name', max_length=50, validators=[RegexValidator(regex=r"^[0-9a-zA-Z \-\_]*$", message="Contains character that isn't allowed. Allowed characters are a-z, A-Z, 0-9, -_ and space.")])
    lastName = models.CharField('Last name', max_length=50, validators=[RegexValidator(regex=r"^[0-9a-zA-Z \-\_]*$", message="Contains character that isn't allowed. Allowed characters are a-z, A-Z, 0-9, -_ and space.")])
    genderOptions = (('male','Male'),('female','Female'),('other','Other'))
    gender = models.CharField('Gender', choices=genderOptions, max_length=10)

    school = models.ForeignKey('schools.School', verbose_name='School', on_delete=models.PROTECT, null=True, blank=True)
    campus = models.ForeignKey('schools.Campus', verbose_name='Campus', on_delete=models.PROTECT, null=True, blank=True)

    def clean(self):
        errors = []

        # Raise any errors
        if errors:
            raise ValidationError(errors)

class Mentor(Person):
    email = models.EmailField('Email')
    yearLevel = models.CharField('Year level', max_length=10)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='Mentor', on_delete=models.PROTECT)

    def clean(self):
        super().clean()
        errors = []

        if not re.match(r"(^[0-9,-]+$)", self.yearLevel):
            errors.append(ValidationError('Year level can contain numbers, comma and hyphen'))

        # Raise any errors
        if errors:
            raise ValidationError(errors)

class Student(Person):
    graduationYear = models.PositiveIntegerField('Year 12 Graduation Year')
    
    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Student'
        ordering = ['school', 'lastName', 'firstName']

    # *****Permissions*****
    @classmethod
    def stateCoordinatorPermissions(cls, level):
        return eventCoordinatorEditPermissions(level)

    # Used in state coordinator permission checking


    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return f'{self.firstName} {self.lastName}'
    
    def yearLevel(self):
        return datetime.datetime.now().year-self.graduationYear+12

    # *****CSV export methods*****
    """
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
        ]

    # Dictionary of values for each header
    def csvValues(self):
        studentNumber = self.getStudentNumber()
        return {
            f'Member {studentNumber} First Name': self.firstName,
            f'Member {studentNumber} Last Name': self.lastName,
            f'Member {studentNumber} Year Level': self.yearLevel,
            f'Member {studentNumber} Gender': self.get_gender_display(),
        }
    """
    # *****Email methods*****
