import os
from django.core.exceptions import ImproperlyConfigured
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.getenv("SECRET_KEY", "unsafe-development-key")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

INSTALLED_APPS = [
    "django.contrib.admin", "django.contrib.auth", "django.contrib.contenttypes",
    "django.contrib.sessions", "django.contrib.messages", "django.contrib.staticfiles",
    "core", "accounts", "catalog", "cart", "orders", "payments",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware", "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware", "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
MIDDLEWARE.insert(1, "whitenoise.middleware.WhiteNoiseMiddleware")
ROOT_URLCONF = "config.urls"
TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [BASE_DIR / "templates"], "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request", "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages", "cart.context_processors.cart_summary",
    ]},
}]
WSGI_APPLICATION = "config.wsgi.application"
DATABASES = {"default": {
    "ENGINE": os.getenv("DB_ENGINE", "django.db.backends.postgresql"),
    "NAME": os.getenv("POSTGRES_DB", "zain_store"), "USER": os.getenv("POSTGRES_USER", "zain_store"),
    "PASSWORD": os.getenv("POSTGRES_PASSWORD", "zain_store"), "HOST": os.getenv("POSTGRES_HOST", "zain-store-db"),
    "PORT": os.getenv("POSTGRES_PORT", "5432"),
}}
AUTH_PASSWORD_VALIDATORS = []
LANGUAGE_CODE = "en-us"
TIME_ZONE = "Europe/Helsinki"
USE_I18N = True
USE_TZ = True
STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {"staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"}}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "accounts:login"
LOGIN_REDIRECT_URL = "catalog:product_list"
LOGOUT_REDIRECT_URL = "catalog:product_list"
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

if not DEBUG:
    if SECRET_KEY == "unsafe-development-key":
        raise ImproperlyConfigured("SECRET_KEY must be configured when DEBUG=false.")
    SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "true").lower() == "true"
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"
    CSRF_TRUSTED_ORIGINS = [origin for origin in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if origin]
    if os.getenv("BEHIND_HTTPS_PROXY", "false").lower() == "true":
        SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Log to stdout so `docker logs` shows warnings and full tracebacks for 500s, also with DEBUG=false
# (Django's default only emails them to ADMINS).
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"plain": {"format": "{asctime} {levelname} {name}: {message}", "style": "{"}},
    "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "plain"}},
    "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "INFO")},
    "loggers": {"django": {"handlers": ["console"], "level": "WARNING", "propagate": False}},
}
