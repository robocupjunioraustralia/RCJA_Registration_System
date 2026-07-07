import re
import uuid

import boto3
from django.conf import settings
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat

from rcjaRegistration.storageBackends import PrivateMediaStorage

MENTOR_FILE_UPLOAD_PREFIX = 'MentorFile'
MENTOR_FILE_S3_KEY_PATTERN = re.compile(
    r'^MentorFiles/MentorFile_[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\.[a-zA-Z0-9]+$'
)
PRESIGNED_URL_EXPIRY_SECONDS = 15 * 60


def direct_s3_upload_enabled():
    return (
        settings.PRIVATE_BUCKET != 'PRIVATE_BUCKET'
        and settings.AWS_ACCESS_KEY_ID != 'AWS_ACCESS_KEY_ID'
    )


def get_file_extension(original_filename):
    try:
        return original_filename.rsplit('.', 1)[1]
    except IndexError:
        return None


def generate_mentor_file_s3_key(original_filename):
    extension = get_file_extension(original_filename)
    if extension is None:
        raise ValidationError('File must have a file extension')

    return f'{MENTOR_FILE_UPLOAD_PREFIX}s/{MENTOR_FILE_UPLOAD_PREFIX}_{uuid.uuid4()}.{extension}'


def validate_upload_metadata(file_type, original_filename, declared_size):
    errors = []

    extension = get_file_extension(original_filename)
    if extension is None:
        raise ValidationError('File must have a file extension')

    if file_type.allowedFileTypes and extension.lower() not in file_type.allowedFileTypes.lower():
        errors.append(ValidationError(f'File not of allowed type, must be: {file_type.allowedFileTypes}'))

    if declared_size > file_type.maxFilesizeBytes():
        errors.append(ValidationError(
            f'File must be less than {filesizeformat(file_type.maxFilesizeBytes())}. '
            f'Current filesize is {filesizeformat(declared_size)}.'
        ))

    if errors:
        raise ValidationError(errors)


def generate_presigned_put_url(s3_key, content_type):
    s3_client = boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )
    return s3_client.generate_presigned_url(
        'put_object',
        Params={
            'Bucket': settings.PRIVATE_BUCKET,
            'Key': s3_key,
            'ContentType': content_type,
            'ACL': 'private',
        },
        ExpiresIn=PRESIGNED_URL_EXPIRY_SECONDS,
    )


def verify_s3_object(s3_key, file_type):
    if not MENTOR_FILE_S3_KEY_PATTERN.match(s3_key):
        raise ValidationError('Invalid upload key')

    storage = PrivateMediaStorage()
    if not storage.exists(s3_key):
        raise ValidationError('Uploaded file not found')

    actual_size = storage.size(s3_key)
    if actual_size > file_type.maxFilesizeBytes():
        raise ValidationError(
            f'File must be less than {filesizeformat(file_type.maxFilesizeBytes())}. '
            f'Current filesize is {filesizeformat(actual_size)}.'
        )

    extension = get_file_extension(s3_key)
    if extension is None:
        raise ValidationError('File must have a file extension')

    if file_type.allowedFileTypes and extension.lower() not in file_type.allowedFileTypes.lower():
        raise ValidationError(f'File not of allowed type, must be: {file_type.allowedFileTypes}')

    return actual_size
