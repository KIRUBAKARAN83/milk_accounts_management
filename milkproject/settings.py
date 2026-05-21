import os
import re
import logging
from pathlib import Path
from dotenv import load_dotenv

# ------------------------------------------------------------------------------
# Load Environment
# ------------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ------------------------------------------------------------------------------
# Core Settings
# ------------------------------------------------------------------------------

SECRET_KEY = os.getenv("SECRET_KEY", "django-insecure-change-me")

DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1")

ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    "localhost,127.0.0.1"
).split(",")

# ------------------------------------------------------------------------------
# Groq AI Configuration
# ------------------------------------------------------------------------------

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY not found in environment variables")

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

# ------------------------------------------------------------------------------
# OCR.Space Configuration
# ------------------------------------------------------------------------------

# Free key "helloworld" works for testing (25k req/month on paid key)
# Get a free API key at: https://ocr.space/ocrapi
OCRSPACE_API_KEY = os.getenv("OCRSPACE_API_KEY", "helloworld")

# ------------------------------------------------------------------------------
# Applications
# ------------------------------------------------------------------------------

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "accounts",
]

# ------------------------------------------------------------------------------
# Middleware
# ------------------------------------------------------------------------------

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",          # ← must be second
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "milkproject.urls"
WSGI_APPLICATION = "milkproject.wsgi.application"

# ------------------------------------------------------------------------------
# Templates
# ------------------------------------------------------------------------------

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# ------------------------------------------------------------------------------
# Database — Supabase (PostgreSQL) / SQLite fallback
# ------------------------------------------------------------------------------
# FIX: urlparse and dj-database-url both fail when the Supabase password
# contains special chars like [ ] @ # — common in auto-generated passwords.
# Solution: manually split the URL string so Django receives the raw password
# directly (Django's db layer does NOT need URL-encoded passwords).
# ------------------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    try:
        # Strip scheme  →  user:password@host:port/dbname
        without_scheme = re.sub(r'^postgres(?:ql)?://', '', DATABASE_URL)

        # Split on the LAST @ so passwords containing @ are handled correctly
        at_pos      = without_scheme.rfind('@')
        userinfo    = without_scheme[:at_pos]        # "user:raw_password"
        hostinfo    = without_scheme[at_pos + 1:]    # "host:port/dbname"

        # Split userinfo on the FIRST colon only
        colon_pos   = userinfo.index(':')
        db_user     = userinfo[:colon_pos]
        db_password = userinfo[colon_pos + 1:]       # raw — no encoding needed

        # Parse host / port / dbname
        if '/' in hostinfo:
            host_port, db_name = hostinfo.rsplit('/', 1)
        else:
            host_port, db_name = hostinfo, 'postgres'

        db_host, db_port = (host_port.rsplit(':', 1)
                            if ':' in host_port
                            else (host_port, '5432'))

        DATABASES = {
            "default": {
                "ENGINE":       "django.db.backends.postgresql",
                "NAME":         db_name,
                "USER":         db_user,
                "PASSWORD":     db_password,
                "HOST":         db_host,
                "PORT":         int(db_port),
                "CONN_MAX_AGE": 600,
                "OPTIONS":      {
                    "sslmode": os.getenv("DB_SSLMODE", "require"),
                },
            }
        }

    except Exception as exc:
        raise RuntimeError(
            f"Could not parse DATABASE_URL — check format and special characters: {exc}"
        )

else:
    # Local development — plain SQLite, zero config needed
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME":   BASE_DIR / "db.sqlite3",
        }
    }

# ------------------------------------------------------------------------------
# Auth / Internationalisation
# ------------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = []   # tighten in production if needed

LANGUAGE_CODE = "en-us"
TIME_ZONE     = "Asia/Kolkata"
USE_I18N      = True
USE_TZ        = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------------------------------------------------------
# Static files  (WhiteNoise serves them on Render — no nginx needed)
# ------------------------------------------------------------------------------

STATIC_URL  = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

STATICFILES_DIRS = []
if (BASE_DIR / "static").exists():
    STATICFILES_DIRS.append(BASE_DIR / "static")

# ------------------------------------------------------------------------------
# Media files
# ------------------------------------------------------------------------------
# WARNING: Render's disk is ephemeral — uploaded files (OCR docs, images) are
# wiped on every redeploy.  For production persistence add Cloudinary:
#   pip install cloudinary django-cloudinary-storage
#   INSTALLED_APPS += ["cloudinary_storage", "cloudinary"]
#   DEFAULT_FILE_STORAGE = "cloudinary_storage.storage.MediaCloudinaryStorage"
#   CLOUDINARY_STORAGE = {"CLOUD_NAME": ..., "API_KEY": ..., "API_SECRET": ...}
# Until then, media works fine locally and for short-lived uploads on Render.
# ------------------------------------------------------------------------------

MEDIA_URL  = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ------------------------------------------------------------------------------
# Business Logic
# ------------------------------------------------------------------------------

PRICE_PER_LITRE = float(os.getenv("PRICE_PER_LITRE", "50.0"))

# ------------------------------------------------------------------------------
# Twilio  (WhatsApp notifications — optional)
# ------------------------------------------------------------------------------

TWILIO_ACCOUNT_SID     = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN      = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

# ------------------------------------------------------------------------------
# Logging  (replaces the flat-file ai_audit_log.txt which is lost on Render)
# ------------------------------------------------------------------------------

LOGGING = {
    "version":                  1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {message}",
            "style":  "{",
        },
    },
    "handlers": {
        "console": {
            "class":     "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        # Captures logger.info(...) calls in views.py for the AI audit trail
        "accounts": {
            "handlers": ["console"],
            "level":    "INFO",
            "propagate": False,
        },
        "django": {
            "handlers": ["console"],
            "level":    os.getenv("DJANGO_LOG_LEVEL", "WARNING"),
            "propagate": False,
        },
    },
}

# ------------------------------------------------------------------------------
# Security  (hardened for Render HTTPS)
# ------------------------------------------------------------------------------

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Render sets this automatically — used to whitelist the deployment URL
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")
if os.getenv("CSRF_TRUSTED_ORIGINS"):
    CSRF_TRUSTED_ORIGINS += os.getenv("CSRF_TRUSTED_ORIGINS").split(",")  # pyright: ignore[reportOptionalMemberAccess]

CSRF_COOKIE_SECURE    = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG

if not DEBUG:
    SECURE_HSTS_SECONDS            = 31536000   # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD            = True
    SECURE_SSL_REDIRECT            = True

# ------------------------------------------------------------------------------
# Auth Redirects
# ------------------------------------------------------------------------------

LOGIN_URL           = "login"
LOGIN_REDIRECT_URL  = "accounts:home"
LOGOUT_REDIRECT_URL = "login"
