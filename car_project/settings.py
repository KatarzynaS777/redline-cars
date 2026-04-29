import os
from pathlib import Path

import dj_database_url


def _env_bool(name, default=False):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_list(name, default=""):
    return [
        item.strip()
        for item in os.getenv(name, default).split(",")
        if item.strip()
    ]


def _load_dotenv(path):
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")

        if key:
            os.environ.setdefault(key, value)


BASE_DIR = Path(__file__).resolve().parent.parent
_load_dotenv(BASE_DIR / ".env")


SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY",
    os.getenv(
        "SECRET_KEY",
        "django-insecure-dev-key-for-local-portfolio-project",
    ),
)

DEBUG = _env_bool("DEBUG", True)

_allowed_hosts = set(_env_list("ALLOWED_HOSTS", "127.0.0.1,localhost"))
_render_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
if _render_hostname:
    _allowed_hosts.add(_render_hostname)
ALLOWED_HOSTS = sorted(_allowed_hosts)

_csrf_trusted_origins = set(_env_list("CSRF_TRUSTED_ORIGINS"))
if _render_hostname:
    _csrf_trusted_origins.add(f"https://{_render_hostname}")
CSRF_TRUSTED_ORIGINS = sorted(_csrf_trusted_origins)


INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'cars',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'car_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'car_project.wsgi.application'


DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{(BASE_DIR / 'db.sqlite3').as_posix()}",
        conn_max_age=600,
        conn_health_checks=True,
    )
}


AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


LANGUAGE_CODE = 'pl'

TIME_ZONE = 'Europe/Warsaw'

USE_I18N = True

USE_TZ = True


STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

STATICFILES_DIRS = [
    BASE_DIR / "cars/static",
]

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

SECURE_SSL_REDIRECT = _env_bool("SECURE_SSL_REDIRECT", not DEBUG)
SESSION_COOKIE_SECURE = _env_bool("SESSION_COOKIE_SECURE", not DEBUG)
CSRF_COOKIE_SECURE = _env_bool("CSRF_COOKIE_SECURE", not DEBUG)
SESSION_COOKIE_AGE = int(os.getenv("SESSION_COOKIE_AGE", str(60 * 60 * 24 * 365 * 10)))
SESSION_EXPIRE_AT_BROWSER_CLOSE = _env_bool("SESSION_EXPIRE_AT_BROWSER_CLOSE", False)
SESSION_SAVE_EVERY_REQUEST = _env_bool("SESSION_SAVE_EVERY_REQUEST", True)

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

_has_smtp_credentials = bool(
    os.getenv("EMAIL_HOST_USER") and os.getenv("EMAIL_HOST_PASSWORD")
)
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "")

if os.getenv("EMAIL_BACKEND"):
    _default_email_backend = os.getenv("EMAIL_BACKEND")
elif RESEND_API_KEY:
    _default_email_backend = "anymail.backends.resend.EmailBackend"
elif _has_smtp_credentials:
    _default_email_backend = "django.core.mail.backends.smtp.EmailBackend"
else:
    _default_email_backend = "django.core.mail.backends.console.EmailBackend"

EMAIL_BACKEND = _default_email_backend
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
EMAIL_USE_TLS = _env_bool("EMAIL_USE_TLS", True)
EMAIL_USE_SSL = _env_bool("EMAIL_USE_SSL", False)
DEFAULT_FROM_EMAIL = os.getenv(
    "DEFAULT_FROM_EMAIL",
    RESEND_FROM_EMAIL or EMAIL_HOST_USER or "noreply@redlinecars.local",
)
ANYMAIL = {
    "RESEND_API_KEY": RESEND_API_KEY,
}
EMAIL_LINKS_IN_RESPONSE = _env_bool(
    "EMAIL_LINKS_IN_RESPONSE",
    EMAIL_BACKEND == "django.core.mail.backends.console.EmailBackend",
)
MAGIC_LINK_EXPIRE_SECONDS = int(os.getenv("MAGIC_LINK_EXPIRE_SECONDS", "900"))
