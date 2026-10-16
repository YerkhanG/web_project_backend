"""
Django settings for the leaderboard project.

Everything that differs between machines (secret key, debug flag, database
host/user/password) comes from ENVIRONMENT VARIABLES, so no secret is stored
in the code or committed to Git. Docker Compose injects them from the .env file.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# os.environ["NAME"] (square brackets) crashes at startup if the variable is
# missing - good: the app refuses to run without its secrets.
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

# .get() with a default: optional settings.
DEBUG = os.environ.get("DJANGO_DEBUG", "0") == "1"
ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# Minimal app: no admin, no sessions, no users - just our "scores" app.
INSTALLED_APPS = ["scores"]
MIDDLEWARE = ["django.middleware.common.CommonMiddleware"]

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,  # look for templates inside each app (scores/templates/)
        "OPTIONS": {"context_processors": []},
    }
]

# PostgreSQL. HOST is the Compose SERVICE NAME ("db"), not "localhost":
# inside a container, "localhost" would mean the backend container itself.
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ["DB_NAME"],
        "USER": os.environ["DB_USER"],
        "PASSWORD": os.environ["DB_PASSWORD"],
        "HOST": os.environ.get("DB_HOST", "db"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_TZ = True
