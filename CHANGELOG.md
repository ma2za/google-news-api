# Changelog

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
