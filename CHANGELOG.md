# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-08-19

### Changed

- Require Django 5.2 LTS or newer. Django 4.2 reached end of life in April 2026, and 5.0 and 5.1 are also unsupported upstream, so they are no longer declared.
- Require Django REST Framework 3.18 or newer, the first release compatible with the whole supported Django range. Earlier releases fail to import under Django 6.1.
- Declare support for Django 6.0 and 6.1 and for Python 3.14, each covered by the test matrix.
- Promote the package to `Development Status :: 5 - Production/Stable`.

### Added

- Expose `django_adr.__version__`.
- Test the full Python 3.12–3.14 × Django 5.2/6.0/6.1 matrix in CI, with the coverage threshold enforced at 100%.

[1.0.0]: https://github.com/niccolomineo/django-adr/releases/tag/v1.0.0
