from django.db import models
from common.models import *
from django.conf import settings

# **********MODELS**********

class Question(models.Model):
    # Fields and primary key
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    shortTitle = models.CharField('Short title', max_length=20, unique=True, help_text="This will appear in the admin where the full question text won't fit. Users will never see this.")
    questionText = models.TextField('Question text')
    required = models.BooleanField('Required', default=True, help_text='Users must accept required questions to register')

    # *****Meta and clean*****
    class Meta:
        verbose_name = "Question"
        ordering = ['-required', '-creationDateTime']

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return str(self.questionText)

    # *****CSV export methods*****

    # *****Email methods*****

class QuestionResponse(models.Model):
    # Fields and primary key
    question = models.ForeignKey(Question, verbose_name='Question', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='User', on_delete=models.CASCADE)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    response = models.BooleanField('Response')

    # *****Meta and clean*****
    class Meta:
        verbose_name = "Question Response"
        ordering = ['question', 'user']
        unique_together = ('question', 'user')

    # *****Permissions*****
    @classmethod
    def coordinatorPermissions(cls, level):
        if level in ['full', 'viewall', 'eventmanager', 'schoolmanager', 'billingmanager']:
            return [
                'view',
            ]
        
        return []

    # Used in state coordinator permission checking
    def getState(self):
        return self.user.homeState

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return str(self.question)

    # *****CSV export methods*****

    # List of all csv headers for instance of this model
    def csvHeaders(self):
        return [
            {'header': self.question.shortTitle, 'order': self.question.shortTitle},
        ]

    # Dictionary of values for each header
    def csvValues(self):
        return {
            self.question.shortTitle: self.response,
        }

    # *****Email methods*****
