from django.db import models
from common.models import *

# **********MODELS**********

class MentorQuestion(models.Model):
    # Fields and primary key
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    questionText = models.TextField('Question text')
    required = models.BooleanField('Required', default=True, help_text='Mentors must accept required questions to register')

    # *****Meta and clean*****
    class Meta:
        verbose_name = "Mentor Question"
        ordering = ['-creationDateTime']

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return str(self.questionText)

    # *****CSV export methods*****

    # *****Email methods*****
