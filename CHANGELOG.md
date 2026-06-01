# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-08-21

### Security

- Escape raw HTML in Markdown bodies by default. Previously `mistune` was configured with `escape=False` while the templates rendered the result through `|safe`, so anyone able to write an ADR could inject script into every reader's browser. Set `DJANGO_ADR_MARKDOWN_ESCAPE = False` to restore the old behaviour if every author is trusted.

### Changed

- **Breaking.** `number` is now a `BigAutoField` primary key allocated by the database, replacing the implicit `id` column and the custom `save()` that read the current maximum and added one. That read-then-write could not be made race-free — the row lock protected the row that existed, not the number about to be taken — so concurrent creation raised `IntegrityError`. Numbers may now contain gaps, which is correct: the number identifies the record, not its position.
- **Breaking.** Exported filenames keep non-ASCII characters (`0003-città.md`, previously `0003-.md`), and a title that slugifies to nothing falls back to `adr`.
- `create_adr --supersedes` now goes through `ADR.supersede_with()` rather than setting the two fields by hand.
- Rewrote the README's authentication example. It wrapped `login_required` around `include()`, which returns a URLconf rather than a view and fails at request time.
- Repositioned the package as "A Django-native decision log for software architecture".

### Added

- `py.typed` marker (PEP 561), so downstream type checkers use the package's inline annotations. CI asserts it reaches both the wheel and the sdist.
- Database-level check constraints enforcing that an ADR is superseded if and only if it references a superseding ADR, and that no ADR supersedes itself. `clean()` alone could not hold this, since `Model.save()` never calls `full_clean()`.
- `ADR.supersede_with()`, writing both halves of the supersession invariant in one transaction.
- `ADR.supersession_chain()`, returning an ADR's full lineage oldest decision first, guarded against cycles.
- Supersession history on the ADR detail page, and an `/adrs/timeline/` view grouping every lineage.
- `GET /adrs/api/adrs/?status=` filtering, matching the HTML list view.
- `GET /adrs/api/adrs/<number>/chain/` returning an ADR's supersession lineage.
- `export_adrs --front-matter`, prefixing each exported file with a YAML metadata block.
- `DJANGO_ADR_MARKDOWN_ESCAPE` setting.
- PostgreSQL CI job exercising the migration chain against a real server.

### Migration notes

`0002`–`0005` move the primary key from `id` to `number`, remapping the `superseded_by` foreign key from `id` values to `number` values along the way, then repair any row that violates the new constraints before applying them. Back up before upgrading and run `python manage.py migrate` — the change rebuilds the table.

## [1.0.0] - 2026-08-19

### Changed

- Require Django 5.2 LTS or newer. Django 4.2 reached end of life in April 2026, and 5.0 and 5.1 are also unsupported upstream, so they are no longer declared.
- Require Django REST Framework 3.18 or newer, the first release compatible with the whole supported Django range. Earlier releases fail to import under Django 6.1.
- Declare support for Django 6.0 and 6.1 and for Python 3.14, each covered by the test matrix.
- Promote the package to `Development Status :: 5 - Production/Stable`.

### Added

- Expose `django_adr.__version__`.
- Test the full Python 3.12–3.14 × Django 5.2/6.0/6.1 matrix in CI, with the coverage threshold enforced at 100%.

[2.0.0]: https://github.com/niccolomineo/django-adr/releases/tag/v2.0.0
[1.0.0]: https://github.com/niccolomineo/django-adr/releases/tag/v1.0.0
