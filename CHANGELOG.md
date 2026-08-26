# Changelog

## Unreleased

### Fixed

- Feeds that feedparser flags as bozo for recoverable defects (undefined
  entities, encoding mismatches) are no longer rejected when they still
  contain usable entries. A warning is logged instead; feeds with no parsed
  entries keep raising `ParsingError`.
- Feed entries missing `title`, `link`, or `published` no longer crash with
  `AttributeError`. Missing fields map to `None`, matching the `Article`
  TypedDict contract.
- Rate-limited responses with an HTTP-date `Retry-After` header (allowed by
  RFC 9110) now raise `RateLimitError` with the remaining delay instead of
  crashing with an unhandled `ValueError`. Malformed header values fall back
  to the previous 60 second default.
- `batch_search()` no longer discards the whole batch when a single query
  fails with an HTTP, rate-limit, or parsing error after retries. The failing
  query now returns an empty list (matching the existing behavior for invalid
  queries) while the other queries keep their results. Configuration errors
  still propagate because they would fail identically for every query.

## 0.0.16 - 2026-08-11

### Added

- Added Python 3.14 to the tested compatibility matrix.
- Added contributor, security, compatibility, release, and structured issue
  guidance.

### Changed

- Expanded CI and publishing validation for built artifacts, package metadata,
  console entry points, optional MCP installation, and test collection.
- Pinned release tooling and updated the GitHub Actions toolchain.
- Updated the optional MCP development lock to `cryptography` 50.0.0.

### Compatibility

- Runtime APIs, CLI commands, MCP tools, defaults, output formats, and article
  dictionaries are unchanged.

## 0.0.17 - 2026-08-21

### Added

- `GoogleNewsClient.location_news()` and `AsyncGoogleNewsClient.location_news()`
  to fetch local headlines for a specific city, region, or country.
- A new `location` CLI command to fetch local headlines (`google-news location "Chicago"`).
- A new `location_news` tool in the MCP server for agent/AI workflows.
- `NewsQuery` builder class to safely construct advanced search queries using
  exact phrases, any-word matching, exclusions, and title targeting.
- New CLI options for the `search` and `batch` commands to leverage the advanced
  query builder: `--exact-phrase`, `--any-word`, `--exclude-word`, `--in-title`,
  and `--show-query`.

### Changed

- Replaced test-name-based integration selection with explicit `@pytest.mark.integration` decorators in the test suite.

## 0.0.15 - 2026-07-29

### Added

- Added `--output PATH` to the `search`, `batch`, and `top` commands for direct
  UTF-8 file output.
- Added `--force` for explicit replacement of existing output files.
- Added public API contract tests for client signatures, exports, and the base
  article dictionary shape.

### Changed

- Release validation now smoke-tests installed wheel and source artifacts,
  including package entry points and optional MCP installation.
- Live-network tests now use explicit integration markers instead of a
  function-name allowlist.
- CI version checks now read installed package metadata instead of hardcoding a
  release number.

### Fixed

- Constrained the optional MCP dependency to the compatible 1.x series so a
  fresh `google-news-api[mcp]` installation cannot select the incompatible MCP
  2.x API.

### Compatibility

- Existing client calls, CLI commands, MCP tools, defaults, stdout output, and
  article dictionaries are unchanged. File output is opt-in, and existing files
  are never replaced without `--force`.

## 0.0.14 - 2026-07-21

### Added

- Added `google-news --version` for installation checks and bug reports.

### Changed

- Extended CI installation smoke coverage to verify the installed package
  version and command-line entry point.

### Compatibility

- Existing client calls, CLI commands, MCP tools, defaults, output formats, and
  article dictionaries are unchanged. The new version option is additive.

## 0.0.13 - 2026-07-17

### Added

- Added trusted-source filtering with repeatable include and exclude domain
  options across synchronous, asynchronous, CLI, and MCP searches.
- Added batch search to the command-line interface and MCP server.

### Changed

- Updated package license metadata to the SPDX format.
- Improved release validation and test isolation without changing runtime
  defaults or article result shapes.

### Compatibility

- Existing client calls, CLI commands, MCP tools, and article dictionaries are
  unchanged. All new filters and commands are opt-in.

## 0.0.12 - 2026-07-09

### Added

- Added the `google-news` command-line interface with `search` and `top`
  commands.
- Added table, JSON, and CSV CLI output formats.
- Added `--decode-links` to the CLI, preserving the original Google News URL in
  `google_link`.
- Added public `Article` and `EnrichedArticle` `TypedDict` exports.

### Changed

- Switched the publishing workflow to PyPI Trusted Publishing.
- Publish now runs on GitHub release publication instead of release creation.
- Added README examples for CLI exports and SearchAPI CLI usage.

### Compatibility

- Existing Python client methods, dictionary result shapes, SearchAPI modes, and
  MCP behavior are unchanged.
