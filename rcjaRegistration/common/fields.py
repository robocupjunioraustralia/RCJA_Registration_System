from django.db import models
import uuid

class UUIDFIeld:
    def generateUUIDFilename(self, obj, filename,):
        if self.originalFilenameField is not None:
            setattr(obj, self.originalFilenameField, filename)

        if self.uploadPrefix is not None:
            extension = filename.rsplit('.', 1)[1]
            newFilename = f'{self.uploadPrefix}s/{self.uploadPrefix}_{str(uuid.uuid4())}.{extension}'
            return newFilename
        
        return filename

class UUIDFileField(UUIDFIeld, models.FileField):

    description = "UUID File Field"

    def __init__(self, *args, **kwargs):
        self.uploadPrefix = kwargs.pop("upload_prefix", None)
        self.originalFilenameField = kwargs.pop("original_filename_field", None)

        kwargs['upload_to'] = self.generateUUIDFilename

        super().__init__(*args, **kwargs)

class UUIDImageField(UUIDFIeld, models.ImageField):

    description = "UUID Image Field"

    def __init__(self, *args, **kwargs):
        self.uploadPrefix = kwargs.pop("upload_prefix", None)
        self.originalFilenameField = kwargs.pop("original_filename_field", None)

        kwargs['upload_to'] = self.generateUUIDFilename

        super().__init__(*args, **kwargs)
