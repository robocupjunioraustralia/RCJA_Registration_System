from django.db import models

# Create your models here.



class Team(models.Model):
    # Foreign keys
    division = models.ForeignKey('competitions.Division', verbose_name='Division', on_delete=models.PROTECT)
    school = models.ForeignKey('schools.School', verbose_name='School', on_delete=models.PROTECT)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    name = models.CharField('Name', max_length=50)

    # *****Meta and clean*****
    def __str__(self):
        return self.name

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    # *****CSV export methods*****

    # *****Email methods*****


class Student(models.Model):
    # Foreign keys
    team = models.ForeignKey(Team, verbose_name='Team', on_delete=models.CASCADE)
    # Creation and update time
    creationDateTime = models.DateTimeField('Creation date',auto_now_add=True)
    updatedDateTime = models.DateTimeField('Last modified date',auto_now=True)
    # Fields
    first_name = models.CharField('First name', max_length=50)
    last_name = models.CharField('Last name', max_length=50)
    yearLevel = models.PositiveIntegerField('Year level')
    genderOptions = (('male','Male'),('female','Female'),('other','Other'))
    gender = models.CharField('Gender', choices=genderOptions, max_length=10)
    birthday = models.DateField('Birthday')

    # *****Meta and clean*****
    def __str__(self):
        return self.first_name + ' ' + self.last_name

    # *****Save & Delete Methods*****

    # *****Methods*****

    # *****Get Methods*****

    # *****CSV export methods*****

    # *****Email methods*****
