# Changelog

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
