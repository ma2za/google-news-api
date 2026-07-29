# Changelog

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
