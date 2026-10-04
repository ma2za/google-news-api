# Compatibility policy

`google-news-api` preserves its established public interfaces while progressing
toward 1.0.

## Semantic versioning and release stability

The project adheres to strict stability guarantees:

- **Minor releases (`0.X.0`):** Additive features, new optional parameters,
  additional CLI commands, new MCP tools, and expanded query capabilities. No
  breaking changes.
- **Patch releases (`0.X.Y`):** Bug fixes, parser resilience improvements,
  performance optimizations, and upstream Google News endpoint adjustments.
- **Deprecation policy:** Before removing or altering any established public
  interface, it will be marked as deprecated and emit a `DeprecationWarning`
  for at least two consecutive minor releases prior to removal.
- **Breaking changes:** Breaking changes are forbidden across `0.x` releases
  and will only occur in an explicitly announced major milestone (`1.0.0+`).

## Public versus internal API surface

### Public contracts (guaranteed stable)

The public surface comprises:
- All symbols exported directly from the top-level package namespace
  (`google_news_api.__all__`):
  - `GoogleNewsClient`, `AsyncGoogleNewsClient`, `ClientConfig`
  - `NewsQuery`
  - `ArticleEnricher`, `AsyncArticleEnricher`
  - Result utilities: `normalize_article`, `normalize_articles`,
    `deduplicate_articles`, `sort_articles`, `parse_published`, `source_domain`
  - Typed structures: `Article`, `EnrichedArticle`, `NormalizedArticle`,
    `RelatedArticle`, `ArticleCluster`
  - Cache and rate-limiting utilities: `Cache`, `AsyncCache`, `RateLimiter`,
    `AsyncRateLimiter`
  - Exceptions: `GoogleNewsError`, `HTTPError`, `ParsingError`, `RateLimitError`,
    `ValidationError`, `ConfigurationError`
  - Logging setup: `setup_logging`
- The six canonical base article dictionary keys:
  - `title`
  - `link`
  - `published`
  - `summary`
  - `source`
  - `id`
- Console command line interfaces and defaults:
  - `google-news` (search, top-news, clusters, location, decode, enrich, monitor, watch)
  - `google-news-mcp` (stdio and streamable HTTP transports)
- Model Context Protocol tools and schemas (`news_search`, `batch_news_search`,
  `top_news`, `location_news`, `server_info`).

### Internal modules

Any module, function, or class not exported in `google_news_api.__all__` is
considered internal implementation detail. Direct imports from private
submodules (such as `google_news_api.client.*` internal functions) are not
guaranteed to remain stable across minor releases.

## Deprecation

An established interface may be documented as deprecated, but it will not be
removed before a future explicitly planned breaking release and will emit
warnings for at least two minor releases. Deprecated behavior remains tested
while supported.

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
