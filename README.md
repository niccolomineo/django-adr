# django-adr

[![PyPI](https://img.shields.io/pypi/v/django-adr?label=pypi)](https://pypi.org/project/django-adr/)
[![Python](https://img.shields.io/pypi/pyversions/django-adr?label=python)](https://pypi.org/project/django-adr/)
[![Django](https://img.shields.io/pypi/frameworkversions/django/django-adr?label=django)](https://pypi.org/project/django-adr/)
[![CI](https://github.com/niccolomineo/django-adr/actions/workflows/ci.yml/badge.svg)](https://github.com/niccolomineo/django-adr/actions/workflows/ci.yml)
[![License](https://img.shields.io/pypi/l/django-adr?label=license)](LICENSE)

A Django-native decision log for software architecture — a structured, queryable database of **[Architectural Decision Records (ADR)](https://niccolomineo.com/articles/django-architectural-decisions/)** that lives inside your application rather than in loose Markdown files.

Requires Python 3.12 or newer and Django 5.2 LTS or newer. Every supported
combination — Python 3.12/3.13/3.14 against Django 5.2/6.0/6.1 — is exercised
by the test suite on every push.

## Features

- Django Admin interface to create and manage ADRs
- HTML list and detail views with status filtering
- Supersession lineages — every ADR links to the decisions it replaced and the one that replaced it, with a timeline view across the whole log
- Read-only REST API (Django REST Framework) with pre-rendered Markdown HTML fields, status filtering, and a per-ADR supersession chain endpoint
- Management command `create_adr` to create ADRs from the CLI, with optional `--supersedes` to mark an existing ADR as superseded in one step
- Management command `export_adrs` to export all ADRs as Markdown files, optionally with YAML front matter for MkDocs, Sphinx, or Docusaurus
- Markdown support for context, decision, and consequences fields, escaped by default
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
- `/adrs/<number>/` — view a single ADR, including its supersession history
- `/adrs/timeline/` — every supersession lineage, grouped

### REST API

- `GET /adrs/api/adrs/` — list all ADRs
- `GET /adrs/api/adrs/?status=accepted` — filter by status
- `GET /adrs/api/adrs/<number>/` — retrieve a single ADR
- `GET /adrs/api/adrs/<number>/chain/` — the ADR's full supersession lineage, oldest decision first

The API is unpaginated by default, so it inherits whatever the host project
configures:

```python
REST_FRAMEWORK = {
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}
```

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

Add `--front-matter` to prefix each file with a YAML block, so the export drops
straight into a docs-as-code pipeline:

```bash
python manage.py export_adrs --output-dir=docs/adr --front-matter
```

```yaml
---
adr: 0003
title: "Use PostgreSQL"
status: accepted
date: 2026-08-21
superseded_by: 0012
---
```

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

**HTML views** — `login_required` cannot wrap an `include()`, because `include()`
returns a URLconf rather than a view. Either protect the whole project with
`LoginRequiredMiddleware` (Django 5.1+):

```python
MIDDLEWARE = [
    ...
    "django.contrib.auth.middleware.LoginRequiredMiddleware",
]
```

or subclass the views and route them yourself:

```python
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import path

from django_adr.views import ADRDetailView, ADRListView, ADRTimelineView


class ProtectedADRListView(LoginRequiredMixin, ADRListView):
    pass


class ProtectedADRDetailView(LoginRequiredMixin, ADRDetailView):
    pass


class ProtectedADRTimelineView(LoginRequiredMixin, ADRTimelineView):
    pass


app_name = "django_adr"

urlpatterns = [
    path("", ProtectedADRListView.as_view(), name="adr-list"),
    path("timeline/", ProtectedADRTimelineView.as_view(), name="adr-timeline"),
    path("<int:number>/", ProtectedADRDetailView.as_view(), name="adr-detail"),
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

## Markdown rendering

ADR bodies are rendered with [mistune](https://github.com/lepture/mistune) and
raw HTML in the source is **escaped**, so an ADR body cannot inject markup into
the HTML views or the API. Link schemes such as `javascript:` and `data:` are
neutralised by the renderer.

If every author of an ADR is trusted and you need raw HTML to pass through, opt
out explicitly:

```python
DJANGO_ADR_MARKDOWN_ESCAPE = False
```

Anyone who can write an ADR can then execute script in the browser of anyone who
reads one.

## Translations

All user-facing strings are translatable. The package ships with an English locale. To generate translations for your project:

```bash
python manage.py makemessages -l it
```

Ensure `USE_I18N = True` in your project settings.

## License

MIT
