from django.db import models
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator

from events.models import BaseEventAttendance

import re

# **********MODELS**********

class WorkshopAttendee(BaseEventAttendance):
    # Foreign keys

    # Fields
    attendeeTypeChoices = (('teacher', 'Teacher'), ('student', 'Student'))
    attendeeType = models.CharField('Attendee type', max_length=15, choices=attendeeTypeChoices)

    # Compulsory for all attendee types
    firstName = models.CharField('First name', max_length=50, validators=[RegexValidator(regex=r"^[0-9a-zA-Z \-\_]*$", message="Contains character that isn't allowed. Allowed characters are a-z, A-Z, 0-9, -_ and space.")])
    lastName = models.CharField('Last name', max_length=50, validators=[RegexValidator(regex=r"^[0-9a-zA-Z \-\_]*$", message="Contains character that isn't allowed. Allowed characters are a-z, A-Z, 0-9, -_ and space.")])
    yearLevel = models.CharField('Year level', max_length=10)
    genderOptions = (('male','Male'),('female','Female'),('other','Other'))
    gender = models.CharField('Gender', choices=genderOptions, max_length=10)

    # Required for teachers
    email = models.EmailField('Email', blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Workshop attendee'
        ordering = ['event', 'school', 'division', 'lastName']

    eventTypeMapping = 'workshop'

    def clean(self):
        super().clean()
        errors = []

        # Check student fields are filled out
        if self.attendeeType == 'student':
            for field in []:
                if not getattr(self, field, None):
                    errors.append(ValidationError('{} must not be blank for student attendee'.format(self._meta.get_field(field).verbose_name)))

        # Check teacher fields filled out
        if self.attendeeType == 'teacher':
            for field in ['email']:
                if not getattr(self, field, None):
                    errors.append(ValidationError('{} must not be blank for teacher attendee'.format(self._meta.get_field(field).verbose_name)))

        # Validate year level
        if self.attendeeType == 'student':
            if not re.match(r"(^[0-9]+$)", self.yearLevel):
                errors.append(ValidationError('Year level must be a number'))
        
        else:
            if not re.match(r"(^[0-9,-]+$)", self.yearLevel):
                errors.append(ValidationError('Year level can contain numbers, comma and hyphen'))

        # Raise any errors
        if errors:
            raise ValidationError(errors)

    # *****Permissions*****

    # *****Save & Delete Methods*****


    # *****Methods*****

    # *****Get Methods*****

    def attendeeFullName(self):
        return f'{self.firstName} {self.lastName}'
    attendeeFullName.short_description = 'Name'
    attendeeFullName.admin_order_field = 'lastName'

    def strNameAndSchool(self):
        if self.school:
            return f"{self.attendeeFullName()} ({self.school})"

        return f"{self.attendeeFullName()} ({self.mentorUser.fullname_or_email()})"

    def __str__(self):
        return f"{self.attendeeFullName()} ({self.event.name} {self.event.year})"

    # *****CSV export methods*****

    # *****Email methods*****