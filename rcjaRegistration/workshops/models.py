from django.db import models
from common.models import *

from events.models import BaseEventAttendance

# **********MODELS**********

class WorkshopAttendee(BaseEventAttendance):
    # Foreign keys

    # Fields
    attendeeTypeChoices = (('teacher', 'Teacher'), ('student', 'Student'))
    attendeeType = models.CharField('Attendee type', max_length=15, choices=attendeeTypeChoices)

    # Compulsory for all attendee types
    firstName = models.CharField('First name', max_length=50)
    lastName = models.CharField('Last name', max_length=50)

    # Optional for all
    email = models.EmailField('Email', blank=True)

    # Only required for students
    yearLevel = models.PositiveIntegerField('Year level', null=True, blank=True)
    genderOptions = (('male','Male'),('female','Female'),('other','Other'))
    gender = models.CharField('Gender', choices=genderOptions, max_length=10, blank=True)
    birthday = models.DateField('Birthday', null=True, blank=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Workshop attendee'
        ordering = ['event', 'school', 'division', 'lastName']

    def clean(self):
        super().clean()
        errors = []

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