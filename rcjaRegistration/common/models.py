from django.core.exceptions import ValidationError

from PIL import Image

from io import BytesIO
from django.core import files
from django.core.files.images import ImageFile


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

def checkImage(imageField):
    RATIO = 4/3
    LEEWAY = 0.01
    width = imageField.width
    height = imageField.height
    if width < 50 or height <50:
        raise ValidationError("The image is too small")
    if abs(width/height - RATIO) > LEEWAY:
        imageField.open()
        if width/height> RATIO: # Too wide
            (left, upper, right, lower) = (width/2-height*RATIO/2, 0, width/2+height*RATIO/2,height)
        else: # Too tall
            (left, upper, right, lower) = (0,height/2-width/RATIO/2, width, height/2+width/RATIO/2)

        with Image.open(imageField) as im:
            im_crop = im.crop((left, upper, right, lower))
            output = BytesIO()
            im_crop.save(output, format=im.format)
            output.seek(0)
        return ImageFile(output, imageField.name)
    return imageField