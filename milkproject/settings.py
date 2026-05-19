import os
from pathlib import Path
from urllib.parse import urlparse
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

GROQ_MODEL = os.getenv(
    "GROQ_MODEL",
    "llama-3.1-8b-instant"
)

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
    "whitenoise.middleware.WhiteNoiseMiddleware",          # ← Render static files
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
# Database — Supabase (PostgreSQL)
# ------------------------------------------------------------------------------
# Supabase gives you a DATABASE_URL of the form:
#   postgresql://postgres:[password]@db.[ref].supabase.co:5432/postgres
#
# We parse it at runtime so the same settings.py works locally (SQLite fallback)
# and on Render (Supabase Postgres).
# ------------------------------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    parsed = urlparse(DATABASE_URL)
    scheme = parsed.scheme.split("+")[0]   # handles "postgres+psycopg2://" etc.

    if scheme in ("postgres", "postgresql"):
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.postgresql",
                "NAME": parsed.path.lstrip("/"),
                "USER": parsed.username,
                "PASSWORD": parsed.password,
                "HOST": parsed.hostname,
                "PORT": parsed.port or 5432,
                "CONN_MAX_AGE": 600,
                "OPTIONS": {
                    # Supabase requires SSL; use "require" or "verify-full"
                    "sslmode": os.getenv("DB_SSLMODE", "require"),
                },
            }
        }
    else:
        # Fallback: sqlite (useful for local dev with a sqlite DATABASE_URL)
        DATABASES = {
            "default": {
                "ENGINE": "django.db.backends.sqlite3",
                "NAME": BASE_DIR / (parsed.path.lstrip("/") or "db.sqlite3"),
            }
        }
else:
    # Local dev with no DATABASE_URL at all → plain SQLite
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# ------------------------------------------------------------------------------
# Auth / Internationalisation
# ------------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"
TIME_ZONE = "Asia/Kolkata"
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ------------------------------------------------------------------------------
# Static & Media
# ------------------------------------------------------------------------------

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# WhiteNoise compressed manifest storage for Render (production)
if not DEBUG:
    STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

STATICFILES_DIRS = []
if (BASE_DIR / "static").exists():
    STATICFILES_DIRS.append(BASE_DIR / "static")

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# ------------------------------------------------------------------------------
# Business Logic
# ------------------------------------------------------------------------------

PRICE_PER_LITRE = float(os.getenv("PRICE_PER_LITRE", "50.0"))

# ------------------------------------------------------------------------------
# Twilio (Optional)
# ------------------------------------------------------------------------------

TWILIO_ACCOUNT_SID     = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN      = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_NUMBER = os.getenv("TWILIO_WHATSAPP_NUMBER", "whatsapp:+14155238886")

# ------------------------------------------------------------------------------
# Security  (tightened for Render HTTPS)
# ------------------------------------------------------------------------------

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Render's public URL — add your custom domain here too if you have one
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

CSRF_COOKIE_SECURE  = not DEBUG
SESSION_COOKIE_SECURE = not DEBUG

# Render forces HTTPS, so turn on HSTS in production
if not DEBUG:
    SECURE_HSTS_SECONDS           = 31536000   # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD            = True
    SECURE_SSL_REDIRECT            = True

# ------------------------------------------------------------------------------
# Auth Redirects
# ------------------------------------------------------------------------------

LOGIN_URL           = "login"
LOGIN_REDIRECT_URL  = "accounts:home"
LOGOUT_REDIRECT_URL = "login"
