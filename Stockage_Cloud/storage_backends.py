import boto3
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

class MinIOMediaStorage(S3Boto3Storage):
    """Backend de stockage personnalisé pour MinIO"""
    bucket_name = 'appstockage'
    endpoint_url = 'http://localhost:9000'
    access_key = 'tkKsUMcKAEdK9rhlUsI3'
    secret_key = 'HYPSWr3YiGxFoHA72ztGC58nn5zxeZwfxHQpUyoU'
    file_overwrite = False
    default_acl = None