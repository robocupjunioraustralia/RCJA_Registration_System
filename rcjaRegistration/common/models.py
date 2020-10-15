from django.db import models
from django.core.exceptions import ValidationError

# Create your models here.

# **********CUSTOM CLASSES**********

class SaveDeleteMixin:
    # *****Save*****

    # Hook for custom pre save actions
    def preSave(self):
        return

    # Hook for custom post save actions
    def postSave(self):
        return

    # Save
    def save(self, skipPrePostSave=False, *args, **kwargs):
        # Run custom pre save actions
        if not skipPrePostSave:
            self.preSave()
        # Save object
        super().save(*args, **kwargs)
        # Run custom post save actions
        if not skipPrePostSave:
            self.postSave()

    # *****Delete*****

    # Hook for custom pre delete actions
    def preDelete(self):
        return

    # Hook for custom post delete actions
    def postDelete(self):
        return

    # Delete
    def delete(self, skipPrePostDelete=False, *args, **kwargs):
        # Run custom pre save actions
        if not skipPrePostDelete:
            self.preDelete()
        # Save object
        super().delete(*args, **kwargs)
        # Run custom post save actions
        if not skipPrePostDelete:
            self.postDelete()

    class Meta:
        abstract = True

# **********FUNCTIONS**********

def checkRequiredFieldsNotNone(self, requiredFields):
    errors = []
    # Check each field is not None
    for field in requiredFields:
        if getattr(self,field, None) is None:
            errors.append('{} must not be blank'.format(self._meta.get_field(field).verbose_name))
    # Raise any errors
    if errors:
        raise ValidationError(errors)
