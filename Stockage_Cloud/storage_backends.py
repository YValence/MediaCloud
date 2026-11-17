from storages.backends.s3boto3 import S3Boto3Storage


class MinIOMediaStorage(S3Boto3Storage):
    """Stockage des fichiers sur MinIO.

    Les identifiants, le bucket et l'URL viennent des réglages AWS_* de settings.py.
    """
    file_overwrite = False
    default_acl = None
