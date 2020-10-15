from django.db import models
from django.core.exceptions import ValidationError

from events.models import BaseEventAttendance

import re

# **********MODELS**********

class WorkshopAttendee(BaseEventAttendance):
    # Foreign keys

    # Fields
    attendeeTypeChoices = (('teacher', 'Teacher'), ('student', 'Student'))
    attendeeType = models.CharField('Attendee type', max_length=15, choices=attendeeTypeChoices)

    # Compulsory for all attendee types
    firstName = models.CharField('First name', max_length=50)
    lastName = models.CharField('Last name', max_length=50)
    yearLevel = models.CharField('Year level', max_length=10)
    genderOptions = (('male','Male'),('female','Female'),('other','Other'))
    gender = models.CharField('Gender', choices=genderOptions, max_length=10)

    # Required for teachers
    email = models.EmailField('Email', blank=True)

    # Required for students
    birthday = models.DateField('Birthday', null=True, blank=True)

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
            for field in ['birthday']:
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

    def __str__(self):
        return self.attendeeFullName()

    # *****CSV export methods*****

    # *****Email methods*****