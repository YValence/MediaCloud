"""Réglages Django du projet MediaCloud (développement local)."""

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ATTENTION : clé et mode debug réservés au développement local.
SECRET_KEY = 'django-insecure-w#77mws^n!2f-c#zcyag)59nrh+y*mam&p6_92!!r2a=8!p+)%'
DEBUG = True
ALLOWED_HOSTS = []


# ===== Application =====

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'storages',
    'Stockage_Cloud',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'Stockage_Cloud.urls'
WSGI_APPLICATION = 'Stockage_Cloud.wsgi.application'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'Templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Page vers laquelle @login_required redirige les visiteurs non connectés
LOGIN_URL = 'connexion'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# ===== Langue et fuseau horaire =====

LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Europe/Paris'
USE_I18N = True
USE_TZ = True


# ===== Fichiers statiques (CSS, JS) =====

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']


# ===== Téléversement =====

FILE_UPLOAD_MAX_MEMORY_SIZE = 500 * 1024 * 1024  # 500 Mo
DATA_UPLOAD_MAX_MEMORY_SIZE = 500 * 1024 * 1024  # 500 Mo

# Extensions acceptées pour chaque type de média (utilisé par views._detecter_type)
MEDIA_EXTENSIONS = {
    'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'],
    'video': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm', '.mkv'],
    'document': ['.pdf', '.doc', '.docx', '.txt', '.rtf', '.odt', '.ppt', '.pptx', '.xls', '.xlsx'],
}


# ===== Stockage des fichiers sur MinIO (compatible S3) =====

AWS_ACCESS_KEY_ID = 'tkKsUMcKAEdK9rhlUsI3'
AWS_SECRET_ACCESS_KEY = 'HYPSWr3YiGxFoHA72ztGC58nn5zxeZwfxHQpUyoU'
AWS_STORAGE_BUCKET_NAME = 'appstockage'
AWS_S3_ENDPOINT_URL = 'http://localhost:9000'
AWS_S3_USE_SSL = False
AWS_S3_VERIFY = False
AWS_DEFAULT_ACL = None
AWS_S3_SIGNATURE_VERSION = 's3v4'

STORAGES = {
    'default': {'BACKEND': 'Stockage_Cloud.storage_backends.MinIOMediaStorage'},
    'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
}
