"""Minimal Django settings for the test suite."""

import os

SECRET_KEY = "django-adr-test-secret-key-not-for-production"
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.messages",
    "django.contrib.sessions",
    "rest_framework",
    "django_adr",
]
DATABASES = {
    "default": {
        "ENGINE": os.environ.get("ADR_DB_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("ADR_DB_NAME", ":memory:"),
        "USER": os.environ.get("ADR_DB_USER", ""),
        "PASSWORD": os.environ.get("ADR_DB_PASSWORD", ""),
        "HOST": os.environ.get("ADR_DB_HOST", ""),
        "PORT": os.environ.get("ADR_DB_PORT", ""),
    }
}
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
ROOT_URLCONF = "tests.urls"
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
            ],
        },
    }
]
MIDDLEWARE = [
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
USE_TZ = True
USE_I18N = True
