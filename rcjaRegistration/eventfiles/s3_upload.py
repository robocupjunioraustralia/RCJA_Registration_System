import re
import uuid

import boto3
from django.conf import settings
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat

from rcjaRegistration.storageBackends import PrivateMediaStorage

MENTOR_FILE_UPLOAD_PREFIX = 'MentorFile'
MENTOR_FILE_FINAL_PREFIX = f'{MENTOR_FILE_UPLOAD_PREFIX}s'
# Incomplete browser uploads land here. Expire this prefix with an S3 lifecycle
# rule (MentorFiles/pending/, 1 day) so abandoned uploads are deleted.
MENTOR_FILE_PENDING_PREFIX = f'{MENTOR_FILE_FINAL_PREFIX}/pending'
_MENTOR_FILE_NAME_PATTERN = (
    rf'{MENTOR_FILE_UPLOAD_PREFIX}_[0-9a-f]{{8}}-[0-9a-f]{{4}}-[0-9a-f]{{4}}-'
    rf'[0-9a-f]{{4}}-[0-9a-f]{{12}}\.[a-zA-Z0-9]+'
)
MENTOR_FILE_S3_KEY_PATTERN = re.compile(
    rf'^{MENTOR_FILE_FINAL_PREFIX}/{_MENTOR_FILE_NAME_PATTERN}$'
)
MENTOR_FILE_PENDING_S3_KEY_PATTERN = re.compile(
    rf'^{MENTOR_FILE_PENDING_PREFIX}/{_MENTOR_FILE_NAME_PATTERN}$'
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

    return f'{MENTOR_FILE_PENDING_PREFIX}/{MENTOR_FILE_UPLOAD_PREFIX}_{uuid.uuid4()}.{extension}'


def pending_key_to_final_key(pending_key):
    if not MENTOR_FILE_PENDING_S3_KEY_PATTERN.match(pending_key):
        raise ValidationError('Invalid upload key')

    return f'{MENTOR_FILE_FINAL_PREFIX}/{pending_key.rsplit("/", 1)[1]}'


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


def get_s3_client():
    return boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    )


def generate_presigned_put_url(s3_key, content_type):
    return get_s3_client().generate_presigned_url(
        'put_object',
        Params={
            'Bucket': settings.PRIVATE_BUCKET,
            'Key': s3_key,
            'ContentType': content_type,
            'ACL': 'private',
        },
        ExpiresIn=PRESIGNED_URL_EXPIRY_SECONDS,
    )


def copy_s3_object(source_key, dest_key):
    get_s3_client().copy_object(
        Bucket=settings.PRIVATE_BUCKET,
        CopySource={
            'Bucket': settings.PRIVATE_BUCKET,
            'Key': source_key,
        },
        Key=dest_key,
        MetadataDirective='COPY',
    )


def delete_s3_object(s3_key):
    get_s3_client().delete_object(
        Bucket=settings.PRIVATE_BUCKET,
        Key=s3_key,
    )


def promote_pending_s3_object(pending_key):
    final_key = pending_key_to_final_key(pending_key)
    try:
        copy_s3_object(pending_key, final_key)
    except Exception as exc:
        raise ValidationError('Failed to save uploaded file') from exc
    return final_key


def verify_s3_object(s3_key, file_type):
    if not MENTOR_FILE_PENDING_S3_KEY_PATTERN.match(s3_key):
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
