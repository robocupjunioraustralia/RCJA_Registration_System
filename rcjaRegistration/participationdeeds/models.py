from django.db import models
from django.conf import settings
from django.core.validators import RegexValidator
from django.utils.safestring import mark_safe

import bleach

from common.models import SaveDeleteMixin
from events.models import eventCoordinatorEditPermissions
from regions.models import PARTICIPANT_DEED_BLEACH_TAGS


class ParticipationDeed(SaveDeleteMixin, models.Model):
    # Foreign keys
    school = models.ForeignKey(
        'schools.School',
        verbose_name='School',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    mentorUser = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name='Mentor',
        on_delete=models.PROTECT,
        null=True,
        blank=True,
    )
    originalEvent = models.ForeignKey(
        'events.Event',
        verbose_name='Original event',
        on_delete=models.PROTECT,
    )
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date', auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date', auto_now=True)

    # Fields
    parentName = models.CharField('Parent name', max_length=100)
    signedDateTime = models.DateTimeField('Signed date/time', auto_now_add=True)
    submittedFirstName = models.CharField(
        'Submitted first name',
        max_length=50,
        validators=[RegexValidator(
            regex=r"^[0-9a-zA-Z \-\_']*$",
            message="Contains character that isn't allowed. Allowed characters are a-z, A-Z, 0-9, -_' and space.",
        )],
    )
    submittedLastName = models.CharField(
        'Submitted last name',
        max_length=50,
        validators=[RegexValidator(
            regex=r"^[0-9a-zA-Z \-\_']*$",
            message="Contains character that isn't allowed. Allowed characters are a-z, A-Z, 0-9, -_' and space.",
        )],
    )
    submittedYearLevel = models.PositiveIntegerField('Submitted year level')
    participationDeedText = models.TextField(
        'Participation deed text',
        editable=False,
        help_text='Snapshot of the state participation deed text at the time of signing.',
    )

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Participation deed'
        ordering = ['-signedDateTime']

    # *****Permissions*****
    @classmethod
    def stateCoordinatorPermissions(cls, level):
        return eventCoordinatorEditPermissions(level)

    # Used in state coordinator permission checking
    def getState(self):
        return self.originalEvent.state

    # *****Save & Delete Methods*****

    def preSave(self):
        if self._state.adding and not self.participationDeedText:
            self.participationDeedText = self.originalEvent.state.participationDeedText

    # *****Methods*****

    # *****Get Methods*****

    def submittedFullName(self):
        return f'{self.submittedFirstName} {self.submittedLastName}'

    def isAttached(self):
        return self.student_set.exists() or self.workshopattendee_set.exists()
    isAttached.short_description = 'Is attached'

    def bleachedParticipationDeedText(self):
        return mark_safe(bleach.clean(
            self.participationDeedText,
            tags=PARTICIPANT_DEED_BLEACH_TAGS
        ))
    bleachedParticipationDeedText.short_description = 'Participation deed text'

    def __str__(self):
        return f'{self.submittedFirstName} {self.submittedLastName} ({self.parentName})'

    # *****CSV export methods*****

    # *****Email methods*****
