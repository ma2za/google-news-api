# Contributing

## Setup

Clone the repository and install the package, development tools, and optional
MCP dependencies:

```bash
poetry install --with dev --all-extras
poetry run pre-commit install
```

## Validation

Run the offline suite:

```bash
poetry run pytest -q -m "not integration" --strict-markers
```

Run formatting and lint checks:

```bash
poetry run black --check google_news_api tests examples mcp_server
poetry run isort --check-only google_news_api tests examples mcp_server
poetry run flake8 google_news_api tests examples mcp_server
```

Live Google News tests are opt-in:

```bash
poetry run pytest -q -m integration --run-integration --strict-markers
```

Live tests depend on an undocumented upstream service and may fail because of
temporary network or response changes. Do not replace offline regression tests
with live-only coverage.

## Pull requests

- Keep changes focused and preserve existing public interfaces and defaults.
- Add a regression test for every bug fix.
- Add offline sync and async tests for shared client behavior.
- Update user-facing documentation and `CHANGELOG.md` when behavior changes.
- Never include API keys, `.env` contents, cookies, or captured request headers.

Feature requests and bug reports are welcome through the repository issue
templates.

## Releases

Maintainer release requirements are documented in
[docs/releasing.md](docs/releasing.md).
