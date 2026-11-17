import boto3
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

class MinIOMediaStorage(S3Boto3Storage):
    """Backend de stockage personnalisé pour MinIO"""
    bucket_name = 'appstockage'
    endpoint_url = 'http://localhost:9000'
    access_key = 'qv6QjoEcNVwmwGwdGKLK'
    secret_key = 'ZaWK9qOT1DRrfarpopHcYuE208NgzDgMPZ5Nn63N'
    file_overwrite = False
    default_acl = None