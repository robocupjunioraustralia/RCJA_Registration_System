from django.db import models

# Create your models here.

class Region(models.Model):
    # Foreign keys
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=30, unique=True)
    description = models.CharField('Description', max_length=200, blank=True, null=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Region'
        ordering = ['name']

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return self.name

    # *****CSV export methods*****

    # *****Email methods***** 

class School(models.Model):
    # Foreign keys
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=100, unique=True)
    abbreviation = models.CharField('Abbreviation', max_length=5, unique=True)
    # Details
    region = models.ForeignKey(Region, verbose_name='Region', on_delete=models.PROTECT, blank=True, null=True)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'School'
        ordering = ['name']

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return self.name

    # *****CSV export methods*****

    # *****Email methods*****

class Mentor(models.Model):
    # Foreign keys
    school = models.ForeignKey(School, verbose_name='School', on_delete=models.CASCADE)
    user = models.OneToOneField('auth.user', verbose_name='User', on_delete=models.PROTECT)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    # Name and email fields are stored on user model, no need to duplicate here
    mobile_phone_number = models.CharField('Phone Number', max_length=12)

    # *****Meta and clean*****
    class Meta:
        verbose_name = 'Mentor'
        ordering = ['user']

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    def __str__(self):
        return str(self.user)

    # *****CSV export methods*****

    # *****Email methods*****
