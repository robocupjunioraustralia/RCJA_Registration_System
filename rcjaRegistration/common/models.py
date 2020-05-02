from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import F, Q, Avg, Count, Min, Sum, OuterRef, Subquery, ExpressionWrapper, CharField, Value
from django.db.models.functions import Concat

# Create your models here.

# **********CUSTOM CLASSES**********

class SaveDeleteMixin:
    # *****Save*****
    # Save override to provide for arhived object protection

    # Always allow editing by default, override on individual Model to change behaviour
    def editingAllowed(self):
        return True

    # Hook for custom pre save actions
    def preSave(self):
        return

    # Hook for custom post save actions
    def postSave(self):
        return

    # Save
    def save(self, skipPrePostSave=False, *args, **kwargs):
        # Prevent update if editing is not allowed
        if not self.editingAllowed():
            return
        # Run custom pre save actions
        if not skipPrePostSave:
            self.preSave()
        # Save object
        super().save(*args, **kwargs)
        # Run custom post save actions
        if not skipPrePostSave:
            self.postSave()

    # *****Delete*****
    # Delete override to provide for arhived object protection

    # Normally use editingAllowed status
    def deletingAllowed(self):
        return self.editingAllowed()

    # Hook for custom pre delete actions
    def preDelete(self):
        return

    # Hook for custom post delete actions
    def postDelete(self):
        return

    # Delete
    def delete(self, skipPrePostDelete=False, *args, **kwargs):
        # Prevent update if editing is not allowed
        if not self.deletingAllowed():
            return
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

class CustomSaveDeleteModel(SaveDeleteMixin, models.Model):
    class Meta:
        abstract = True

# **********FUNCTIONS**********

def cleanDownstream(objectIn,setName,attributeName,errors, cleanDownstreamObjects=False):
    for obj in getattr(objectIn,setName).all():
        setattr(obj,attributeName,objectIn)
        try:
            obj.clean(cleanDownstreamObjects=cleanDownstreamObjects)
        except Exception as e:
            for message in e.messages:
                errors.append(ValidationError(message))

def checkRequiredFieldsNotNone(self, requiredFields):
    errors = []
    # Check each field is not None
    for field in requiredFields:
        if getattr(self,field, None) is None:
            errors.append('{} must not be blank'.format(self._meta.get_field(field).verbose_name))
    # Raise any errors
    if errors:
        raise ValidationError(errors)
