import os
from pathlib import Path
from urllib.parse import urlparse, unquote
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent
DEBUG = os.getenv("DJANGO_DEBUG", "0") == "1"
SECRET_KEY = os.getenv(
    "DJANGO_SECRET_KEY", "development-only-not-for-production" if DEBUG else ""
)
if not SECRET_KEY:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY is required")
ALLOWED_HOSTS = [
    s.strip()
    for s in os.getenv("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1,testserver").split(
        ","
    )
    if s.strip()
]
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "drf_spectacular",
    "core",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "core.middleware.ApiHeadersMiddleware",
]
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
u = urlparse(
    os.getenv("DATABASE_URL", "postgresql://magribi:magribi@127.0.0.1:5432/magribi")
)
if u.scheme not in ("postgres", "postgresql"):
    raise ImproperlyConfigured("PostgreSQL DATABASE_URL is required")
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": unquote(u.path.lstrip("/")),
        "USER": unquote(u.username or ""),
        "PASSWORD": unquote(u.password or ""),
        "HOST": u.hostname,
        "PORT": u.port or 5432,
        "CONN_MAX_AGE": 60,
        "CONN_HEALTH_CHECKS": True,
        "OPTIONS": {
            "connect_timeout": 5,
            **(
                {"sslmode": os.environ["DB_SSLMODE"]} if os.getenv("DB_SSLMODE") else {}
            ),
        },
    }
}
AUTH_USER_MODEL = "core.User"
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 10},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "kk"
TIME_ZONE = "Asia/Almaty"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.SessionAuthentication"
    ],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "core.exceptions.exception_handler",
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
}
SPECTACULAR_SETTINGS = {
    "TITLE": "Magribi API",
    "VERSION": "1.0.0",
    "SERVE_PERMISSIONS": ["core.permissions.ManagerPermission"],
}
CSRF_TRUSTED_ORIGINS = [
    s.strip()
    for s in os.getenv(
        "CSRF_TRUSTED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000"
    ).split(",")
    if s.strip()
]
SESSION_COOKIE_NAME = "magribi_session"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = not DEBUG
SESSION_COOKIE_AGE = 60 * 60 * 12
CSRF_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SAMESITE = "Lax"
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = "no-referrer"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_HSTS_SECONDS = 0 if DEBUG else 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
X_FRAME_OPTIONS = "DENY"
DATA_UPLOAD_MAX_MEMORY_SIZE = 32768
