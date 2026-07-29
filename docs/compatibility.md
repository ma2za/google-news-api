# Compatibility policy

`google-news-api` preserves its established public interfaces while progressing
toward 1.0.

## Supported public contracts

- `GoogleNewsClient` and `AsyncGoogleNewsClient`.
- Existing public method names, arguments, meanings, and defaults.
- The six base article keys:
  - `title`
  - `link`
  - `published`
  - `summary`
  - `source`
  - `id`
- Existing exception classes and their documented attributes.
- The `google-news` and `google-news-mcp` console commands.
- Existing CLI commands, flags, output formats, exit codes, and stdout defaults.
- Existing MCP tool names, arguments, defaults, and result behavior.
- `SEARCHAPI_API_KEY` for opt-in SearchAPI modes.
- RSS as the free, keyless default backend.

New optional arguments, methods, commands, tools, result types, and opt-in output
fields may be added.

## Deprecation

An established interface may be documented as deprecated, but it will not be
removed before a future explicitly planned breaking release. Deprecated
behavior remains tested while supported.

## Upstream behavior

Google does not provide a stable public API for the RSS and URL-decoding
operations used by this package. Compatible fixes for upstream endpoint or
response changes may alter internal requests while preserving documented package
behavior.

SearchAPI-backed modes remain optional. A provider change must not change RSS
defaults or require a key for existing calls.

## Version support

Supported Python versions are declared in `pyproject.toml` and on PyPI.
Continuous integration tests every declared minor version. Security and
compatibility fixes target the latest `google-news-api` release.
