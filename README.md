# django-adr

[![PyPI](https://img.shields.io/pypi/v/django-adr?label=pypi)](https://pypi.org/project/django-adr/)
[![Python](https://img.shields.io/pypi/pyversions/django-adr?label=python)](https://pypi.org/project/django-adr/)
[![Django](https://img.shields.io/pypi/frameworkversions/django/django-adr?label=django)](https://pypi.org/project/django-adr/)
[![CI](https://github.com/niccolomineo/django-adr/actions/workflows/ci.yml/badge.svg)](https://github.com/niccolomineo/django-adr/actions/workflows/ci.yml)
[![License](https://img.shields.io/pypi/l/django-adr?label=license)](LICENSE)

A Django reusable package to manage **[Architectural Decision Records (ADR)](https://niccolomineo.com/articles/django-architectural-decisions/)**.

Requires Python 3.12 or newer and Django 5.2 LTS or newer. Every supported
combination — Python 3.12/3.13/3.14 against Django 5.2/6.0/6.1 — is exercised
by the test suite on every push.

## Features

- Django Admin interface to create and manage ADRs
- HTML list and detail views with status filtering
- Read-only REST API (Django REST Framework) with pre-rendered Markdown HTML fields
- Management command `create_adr` to create ADRs from the CLI, with optional `--supersedes` to mark an existing ADR as superseded in one step
- Management command `export_adrs` to export all ADRs as Markdown files
- Markdown support for context, decision, and consequences fields
- Internationalization (i18n) support — English locale included

## Installation

```bash
pip install django-adr
```

Add to `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    "django_adr",
]
```

Include the URLs:

```python
from django.urls import include, path

urlpatterns = [
    ...
    path("adrs/", include("django_adr.urls", namespace="django_adr")),
]
```

Run migrations:

```bash
python manage.py migrate
```

## Usage

### Admin

Visit `/admin/django_adr/adr/` to manage ADRs through the Django admin.

### HTML views

- `/adrs/` — list all ADRs
- `/adrs/?status=accepted` — filter by status
- `/adrs/<number>/` — view a single ADR

### REST API

- `GET /adrs/api/adrs/` — list all ADRs
- `GET /adrs/api/adrs/<number>/` — retrieve a single ADR

### Management commands

Create a new ADR:

```bash
python manage.py create_adr "Use PostgreSQL" \
    --context="We need a relational database." \
    --decision="Use PostgreSQL." \
    --consequences="Team must know SQL."
```

Create a new ADR and supersede an existing one in a single step:

```bash
python manage.py create_adr "Use CockroachDB" --supersedes=3
```

This creates the new ADR and automatically marks ADR-0003 as `Superseded`.

Export all ADRs as Markdown files:

```bash
python manage.py export_adrs --output-dir=docs/adr
```

Each ADR is written to `<output-dir>/<number>-<slug>.md`.

## ADR statuses

| Status | Description |
|--------|-------------|
| `proposed` | Under discussion |
| `accepted` | Agreed and in effect |
| `deprecated` | No longer relevant |
| `superseded` | Replaced by a newer ADR |
| `rejected` | Considered and not adopted |

## Protecting the views

The HTML views and REST API are public by default. The package does not enforce any authentication strategy — that is left to the host project.

**HTML views** — in `urls.py`, wrap the URL include with `login_required`:

```python
from django.contrib.auth.decorators import login_required
from django.urls import include, path

urlpatterns = [
    path("adrs/", login_required(include("django_adr.urls", namespace="django_adr"))),
]
```

**REST API** — set `DEFAULT_PERMISSION_CLASSES` in `settings.py`:

```python
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}
```

Or scope it to the ADR router only by subclassing `ADRViewSet`:

```python
from django_adr.api import ADRViewSet
from rest_framework.permissions import IsAuthenticated

class ProtectedADRViewSet(ADRViewSet):
    permission_classes = [IsAuthenticated]
```

## Translations

All user-facing strings are translatable. The package ships with an English locale. To generate translations for your project:

```bash
python manage.py makemessages -l it
```

Ensure `USE_I18N = True` in your project settings.

## License

MIT
