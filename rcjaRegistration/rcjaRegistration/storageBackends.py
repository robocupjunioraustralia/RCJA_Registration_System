from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

class StaticStorage(S3Boto3Storage):
    location = settings.AWS_STATIC_LOCATION
    default_acl = 'public-read'
    file_overwrite = True
    custom_domain = False
    bucket_name = settings.STATIC_BUCKET

class PublicMediaStorage(S3Boto3Storage):
    location = settings.AWS_PUBLIC_MEDIA_LOCATION
    file_overwrite = False
    bucket_name = settings.PUBLIC_BUCKET
    default_acl = 'public-read'
    custom_domain = False

class PrivateMediaStorage(S3Boto3Storage):
    location = settings.AWS_PRIVATE_MEDIA_LOCATION
    default_acl = 'private'
    file_overwrite = False
    custom_domain = False
    bucket_name = settings.PRIVATE_BUCKET
