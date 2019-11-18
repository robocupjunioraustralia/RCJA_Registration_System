from django.db import models

# Create your models here.

class School(models.Model):
    # Foreign keys
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=50)

    # *****Meta and clean*****

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    # *****CSV export methods*****

    # *****Email methods*****

class Mentor(models.Model):
    # Foreign keys
    school = models.ForeignKey(School, verbose_name='School', on_delete=models.CASCADE)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields

    # *****Meta and clean*****

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    # *****CSV export methods*****

    # *****Email methods*****
