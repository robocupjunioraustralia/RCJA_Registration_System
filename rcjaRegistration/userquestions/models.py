from django.db import models
from common.models import *
from django.conf import settings

# **********MODELS**********

class UserQuestion(models.Model):
    # Fields and primary key
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    questionText = models.TextField('Question text')
    required = models.BooleanField('Required', default=True, help_text='Users must accept required questions to register')

    # *****Meta and clean*****
    class Meta:
        verbose_name = "User Question"
        ordering = ['-creationDateTime']

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return str(self.questionText)

    # *****CSV export methods*****

    # *****Email methods*****

class UserQuestionResponse(models.Model):
    # Fields and primary key
    userQuestion = models.ForeignKey(UserQuestion, verbose_name='User question', on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name='User', on_delete=models.CASCADE)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    response = models.BooleanField('Response')

    # *****Meta and clean*****
    class Meta:
        verbose_name = "User Question Response"
        ordering = ['userQuestion', 'user']
        unique_together = ('userQuestion', 'user')

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return str(self.userQuestion)

    # *****CSV export methods*****

    # *****Email methods*****
