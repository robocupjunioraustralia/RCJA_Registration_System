from django.db import models

# Create your models here.

class State(models.Model):
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

class Division(models.Model):
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

class Competition(models.Model):
    # Foreign keys
    division = models.ForeignKey(Division, verbose_name='Division', on_delete=models.PROTECT)
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
