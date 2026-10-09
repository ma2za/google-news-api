# Release plan

Status: tracked maintainer plan, approved for source control on 2026-10-09
Repository baseline: `v0.1.1` at commit `d6bc637`
Plan updated: 2026-10-09
Planned sequence: `0.1.2` through `0.1.4`

## Fresh-chat handoff: current state and operating rules

### Verified baseline

- Published package and latest tag: `0.1.1` / `v0.1.1`.
- Release commit: `d6bc637` on `main`.
- The `0.1.1` GitHub CI and Publish workflows passed. A clean PyPI
  `google-news-api[mcp]==0.1.1` install verified via PyPI JSON API and smoke tests.
- At the last planning review: no open issues and no open pull requests.
- The last local offline run was `320 passed, 28 deselected` with
  `pytest -q -m "not integration" --strict-markers` and 92% coverage.

### First commands in a new chat

1. Read `AGENTS.md`, `.agents/README.md`, this entire file, and
   `.agents/FAILURE_RETROSPECTIVE.md`.
2. Run `git status --short`, `git fetch origin --tags`, compare `HEAD` with
   `origin/main`, inspect the latest tag, and query PyPI's JSON API for the
   published version.
3. Run `gh pr list --state open` and `gh issue list --state open`. Do not carry
   forward issue numbers from this plan; none were open when it was refreshed.
4. Re-read the selected release section and the relevant implementation and
   tests before editing. Preserve unrelated local work.
5. Keep `pyproject.toml` at the already-published version during implementation.
   Bump it, `CHANGELOG.md`, and public release material only after all feature
   acceptance tests are complete.

### Public contracts that cannot change

- `GoogleNewsClient` and `AsyncGoogleNewsClient`, all existing arguments,
  defaults, exception types, and return container types.
- Base `Article` dictionaries have exactly `title`, `link`, `published`,
  `summary`, `source`, and `id`. New data belongs only in an explicit opt-in
  result type or a new opt-in API.
- RSS remains default and keyless. SearchAPI modes remain opt-in and use
  `SEARCHAPI_API_KEY`.
- `google-news` stays table-first, English/US by default, and does not decode
  links unless asked. `google-news-mcp` defaults to stdio.
- `top_news` named topics and `batch_search` duplicate-query collapse behavior
  remain unchanged. Do not silently turn batch results into a list.
- Core support remains Python 3.9+. Optional MCP/extraction functionality may
  require Python 3.10+ as declared in `pyproject.toml`.

### Code map

- `google_news_api/client.py`: sync and async retrieval, RSS parsing, URL
  decoding, retries, caches, and client lifecycle.
- `google_news_api/results.py` and `types.py`: opt-in normalization and public
  typed result shapes. Never add fields to `Article`.
- `google_news_api/cli.py`: all user-facing command arguments and output.
- `google_news_api/mcp_server.py`: packaged MCP tools and lifecycle; preserve
  in-band error dictionaries and existing tool defaults.
- `google_news_api/monitor.py`: stateful monitoring. Preserve state schema and
  write behavior unless a migration is explicitly designed and tested.
- `tests/`, `mcp_server/tests/`, and `.github/workflows/ci.yml`: regression and
  packaging evidence. Use frozen RSS fixtures or injected transports offline.

### Required release evidence

- Offline: strict-marker pytest, default pytest with integration tests skipped,
  Black, isort, flake8, and `pre-commit run --all-files`.
- Live: only for an authorized release, run the marked integration suite and
  verify at least `en-US` plus one non-English locale for route changes.
- Distribution: `poetry check`, build wheel and sdist, Twine, fresh base and
  `[mcp]` environments, both console commands, imports, `py.typed`, and
  `pip check`.
- Push direct to `main`, wait for every CI job, tag that exact commit, create a
  non-draft GitHub release, verify Trusted Publishing, then install the exact
  PyPI version in a fresh environment. Record release validation results here; never record credentials.

## How to use this document

When asked to implement the next release:

1. Read this entire document and the current repository before editing.
2. Confirm the last published PyPI version and latest Git tag. Do not assume the
   local version is the published version.
3. Select the first release below whose status is not `Released`.
4. Recheck its assumptions against the current Google News behavior and installed
   dependency versions.
5. Keep the published version unchanged while implementing the selected release.
6. Implement only that release. Do not pull work forward from later releases.
7. Bump the version and finalize public release notes only after implementation.
8. Complete every acceptance and release gate before calling it ready.
9. Push the validated commit directly to `main`, wait for CI, and tag that exact
   commit.
10. Publish the GitHub release, verify PyPI, and update this plan's status,
    decisions, baseline metrics, and deferred work. Keep it excluded from Git.

Allowed statuses: `Planned`, `In progress`, `Ready`, `Released`, `Deferred`.

## Maintainer release ordering

Maintainer releases use `main` directly. Do not open a release pull request.

1. Sync local `main` with `origin/main` and require a clean tracked worktree.
2. Record the pre-release package, repository, and adoption baseline in this plan.
3. Leave the existing package version unchanged while implementing the release.
4. Add or update tests and public documentation for shipped behavior.
5. Run focused checks while implementing.
6. When implementation is complete, bump the version and finish release notes.
7. Run the full offline suite with strict markers, linting, packaging checks,
   and clean wheel smoke tests for base and MCP installs.
8. Commit the complete release directly on `main`.
9. Push `main` and wait for every required GitHub Actions check to pass.
10. Fix failures forward on `main`. Never tag a commit with failing checks.
11. Tag the exact successful `origin/main` commit and push the tag.
12. Publish a non-draft GitHub release so Trusted Publishing uploads to PyPI.
13. Monitor publishing and perform a clean post-PyPI install and smoke test.
14. Record results, measurements, and follow-up in this tracked plan.

## Product direction

The package should become the dependable, typed, automation-friendly Google News
RSS client for Python users who need research, monitoring, command-line exports,
or agent tools without an API key.

Growth should come from useful, demonstrable capabilities and trust:

- Preserve the simple `GoogleNewsClient().search(...)` entry point.
- Keep RSS as the free default and SearchAPI modes strictly opt-in.
- Keep sync, async, CLI, and MCP behavior aligned where the surface makes sense.
- Make output easy to clean, enrich, save, and monitor.
- Prefer standard-library implementations and optional extras over new mandatory
  dependencies.
- Publish small releases with one clear user benefit and strong examples.
- Never add telemetry.
- Keep roadmap goals distinct from released capabilities; never expose credentials.

## Baseline assessment

### Public adoption on 2026-07-29

- GitHub: 15 stars, 2 forks, 1 watcher, 0 open issues.
- PyPI downloads excluding mirrors: 39 last day, 345 last week, 1,965 last month.
- Repository age: created 2025-04-25.
- Closest public comparison points:
  - `ranahaani/GNews`: 986 stars, 151 forks, about 116,684 monthly downloads.
  - `kotartemiy/pygooglenews`: 1,389 stars, 144 forks, about 10,383 monthly
    downloads, but less recently maintained.
  - `Iceloof/GoogleNews`: 383 stars and 102 forks.

These numbers are directional, not product quality scores. PyPI downloads include
automation and should be compared as rolling trends, not as exact user counts.

### Current strengths

- Sync and async clients.
- Python 3.9 through 3.14 package compatibility.
- Google News RSS search and topic feeds.
- Relative and absolute date filters.
- Include/exclude publisher domains.
- Batch search.
- Google News URL decoding.
- SearchAPI light and portal modes.
- Typed result dictionaries and a `py.typed` marker.
- JSON and CSV CLI output, including atomic named-file export.
- Packaged MCP server with optional article text extraction.
- Trusted Publishing and release provenance on PyPI.
- A focused README with a short install-to-result path.

### Current adoption gaps

- No stable API reference or documentation site.
- Default topic discovery is limited to eight named sections; long-tail Google
  News section tokens need a safe explicit opt-in.
- Publisher attribution and parsed timestamps remain available only through
  post-processing helpers rather than a single opt-in provenance workflow.
- Sync and async URL decoding still duplicate reverse-engineering logic.
- Static type checking is not part of CI despite publishing `py.typed`.

### Current maintenance risks

- The latest offline suite has 220 passing tests and 28 opt-in integration
  tests; `client.py` coverage remains below the project-wide target.
- Async URL decoding and retry paths need more direct characterization.
- Batch results are dictionaries keyed by query, so duplicate query strings
  collapse and must not be silently changed.
- Article dictionaries have a documented six-key base shape. Enrichment must
  remain opt-in through dedicated result helpers or methods.

## Non-negotiable compatibility contract

Every release in this plan is additive. Until a separately approved major-version
plan exists:

- Keep `GoogleNewsClient` and `AsyncGoogleNewsClient` import paths unchanged.
- Keep existing constructor positional parameters and their defaults unchanged.
- Add new constructor parameters only after `*` as keyword-only parameters.
- Keep existing method names, positional arguments, keyword names, defaults,
  exception types, and return container types unchanged.
- Keep base article dictionaries exactly:
  `title`, `link`, `published`, `summary`, `source`, `id`.
- Put optional fields only in explicitly enriched or normalized results.
- Keep `link` as the Google News RSS URL in default search results unless the
  caller explicitly requests enrichment or decoding.
- Keep RSS mode free, keyless, and the default.
- Keep SearchAPI modes opt-in and continue reading `SEARCHAPI_API_KEY`.
- Keep CLI defaults: table output, no link decoding, English, United States,
  default RSS mode.
- Keep current MCP tool names and defaults. New parameters must be optional.
- Keep current exception classes and their public attributes.
- Keep Python 3.9 support for the core package. Optional features may require
  Python 3.10 only when their dependency genuinely requires it.
- Do not remove dependencies or extras in this release sequence if removal could
  break an existing installation. Dependency cleanup needs separate evidence.
- Do not change negative `max_results` semantics. It currently means no limit.
- Do not change duplicate-query behavior in `batch_search`; document it.

When behavior is ambiguous, add a characterization test before changing code.

## Release gate used for all 10 releases

### Before implementation

- Record `git status --short`, current branch, current commit, current tag, and
  current PyPI version.
- Run the existing offline suite before editing.
- Read files before modifying them.
- Confirm no unrelated user changes overlap the release.
- For undocumented Google News routes or parsing behavior, run a minimal live
  probe in at least two locale combinations before committing to the design.

### Required tests

- `black --check`, `isort --check-only`, and `flake8` on the same paths as CI.
- Full offline `pytest` suite on the development interpreter.
- Tests on Python 3.9 through the minimum-install smoke job.
- Tests on Python 3.10, 3.11, 3.12, 3.13, and 3.14 through the main matrix.
- Use `--strict-markers`; the default suite must skip live integration tests.
- New sync and async tests for every shared capability.
- CLI output tests for stdout and file output where applicable.
- MCP tool registration and argument-forwarding tests where applicable.
- Live integration tests manually before release, never as the only coverage.
- A regression test for every bug found during implementation.

### Distribution checks

- `poetry check`.
- Build both wheel and sdist from a clean tree.
- Run `twine check` on every built distribution.
- Inspect artifact contents for `py.typed`, README, license, and all intended
  modules.
- Install the wheel into a clean Python 3.9 environment and test import, version,
  `google-news --help`, and one mocked/offline command.
- Install the wheel with `[mcp]` into a clean supported environment and test
  `google-news-mcp` startup or app creation without a live network call.
- Run `pip check` after both installs.
- Verify tag `vX.Y.Z` exactly matches `[project].version`.
- Commit and push the validated release directly to `main`; do not use a release
  pull request.
- Wait for required CI on `main`, then tag the exact successful commit.
- Publish only from a GitHub release using the existing trusted publisher.
- After publication, install from PyPI, verify `__version__`, CLI version, and
  package metadata.

### Documentation and release notes

- Update README only for features shipping in that release.
- Update examples when they are the clearest executable documentation.
- Add a complete `CHANGELOG.md` entry with `Added`, `Changed`, `Fixed` when
  applicable, and `Compatibility`.
- In the GitHub release, show one copy-paste example and one sentence explaining
  who benefits.
- Release notes describe only shipped behavior; future work belongs in this plan.

### Rollback criteria

Do not publish, or yank promptly if already published, when any of these occur:

- Existing result keys, defaults, or exception types change unintentionally.
- A wheel entry point fails after installation.
- RSS searches regress in either `en-US` or one non-English locale.
- Sync and async outputs diverge without an explicitly documented reason.
- Optional dependencies become mandatory.
- A new retry, monitoring, or extraction path can create unbounded requests.
- A security-sensitive transport starts on a public interface by default.

## Measurement protocol

Record metrics in this plan immediately before each release and 7 and 28
days after it:

- PyPI last-day, last-week, and last-month downloads from the PyPI Stats API.
- GitHub stars, forks, watchers, unique cloners if available, and open issues.
- README-to-PyPI referral data if GitHub traffic data is available.
- Release page views and source of new stars when observable.
- Support load: regressions, installation failures, and repeated questions.

Primary success metric: 28-day download trend without increased regression rate.
Secondary success metric: stars from users who can reproduce a documented use
case.
Initial maintainer milestone after `0.1.0`: at least 5,000 monthly downloads and 50
stars, subject to revision after three releases of data.

Do not optimize by releasing empty version bumps. A release must have a user
benefit or a security/reliability reason.

---

## Release 1: 0.0.15, trustworthy artifacts and practical file output

Status: `Released`

```text
Implementation started: 2026-07-29
Starting commit: 08addf47ca5780a7697d10c8395a45cfb6d21a6e
Starting PyPI version: 0.0.14
Baseline downloads day/week/month: 39 / 345 / 1,965
Baseline stars/forks/watchers: 15 / 2 / 1
Assumptions verified: PyPI 0.0.14; 22 existing network tests; base article shape;
  MCP 2.0 incompatibility discovered by artifact smoke and constrained to <2.0.0
Files changed: CLI, CLI/client/contract tests, test configuration, CI and publish
  workflows, root and MCP package metadata, lockfile, README, changelog
Compatibility tests added: exports, constructors, search, batch, top, decode,
  base article keys, existing stdout and overwrite behavior
Live probes run: 22/22 marked integration tests passed on 2026-07-29
Artifact smoke environments: Python 3.13.12 wheel, sdist, MCP 1.29.0 extra;
  GitHub Actions passed Python 3.9 install and Python 3.10-3.13 test jobs
Known limitations: no local Python 3.9 interpreter
Deferred items: none
Release commit: 4d7b142, merged to main as b4b1045
Tag: v0.0.15 -> b4b10457bf150392d8b366b1960366610c7ecf02
PyPI upload verified: 2026-07-29; wheel and sdist published through trusted
  publishing; clean PyPI wheel install, version, CLI, py.typed, and pip check passed
7-day metrics:
28-day metrics:
Status: Released
```

### Goal

Make every later release safer while adding the most obvious CLI workflow:
writing JSON or CSV directly to a file.

### User-facing scope

- Add `--output PATH` to `search`, `batch`, and `top`.
- Preserve stdout behavior when `--output` is omitted or `PATH` is `-`.
- Encode files as UTF-8 and use newline handling that produces valid CSV on
  Windows.
- Refuse to overwrite an existing file unless `--force` is supplied.
- Add `--force` to all three commands. It has no effect when output is stdout.
- Continue sending errors to stderr and return exit code 1.

Examples:

```bash
google-news search "AI regulation" --format json --output ai-news.json
google-news batch "OpenAI" "Anthropic" --format csv --output companies.csv
google-news top --topic TECHNOLOGY --format json --output -
```

### Exact contract

- New CLI options only. Do not add file-writing methods to the clients.
- `--output` accepts a filesystem path or `-`.
- If the path exists without `--force`, print
  `google-news: output file already exists: <path>` and return 1.
- Create only the final file, not parent directories.
- Open CSV with `newline=""`; open JSON and table output with `newline=None`.
- Do not catch raw filesystem errors as `GoogleNewsError`. Catch `OSError` in
  `main`, render `google-news: <message>`, and return 1.

### Implementation map

- `google_news_api/cli.py`: parser options, output-opening helper, ownership and
  closing logic.
- `tests/test_cli.py`: stdout compatibility, JSON/CSV files, `-`, existing file,
  `--force`, Unicode, filesystem error, and no partially written file.
- `.github/workflows/ci.yml`: remove hardcoded version assertions; derive the
  expected version from installed metadata or project metadata.
- `.github/workflows/ci_publish.yml`: build first, then test installed artifacts
  before publish.
- Add a small release-check script only if the workflow would otherwise duplicate
  more than a few opaque shell lines. Keep it internal and deterministic.
- `README.md`, `CHANGELOG.md`, `pyproject.toml`.

### Regression foundation

- Replace test-name-based integration selection with explicit
  `@pytest.mark.integration` decorators on every live test.
- Add a test that fails if a live-test marker is missing from known network test
  modules or, preferably, make live access impossible in offline tests by mocking
  transport boundaries.
- Add installed-wheel smoke checks for public exports, CLI entry points, MCP
  module import, and `py.typed`.
- Add signature and base article-key characterization tests. Assert current
  behavior, not implementation details.

### Acceptance criteria

- Existing commands produce byte-for-byte equivalent stdout for existing test
  fixtures.
- Refusing overwrite leaves the existing file untouched.
- A failed command does not truncate an existing file.
- Offline tests perform no live HTTP requests.
- CI tests the built wheel, not only the source checkout.
- Version checks no longer require editing a hardcoded workflow assertion.
- Base article keys and current public signatures are captured by tests.

### Out of scope

- No client export methods.
- No directory creation.
- No append mode.
- No new output formats.

### Discoverability asset

Add a short “Save Google News to JSON or CSV” README section with copy-paste
commands. The GitHub release title should lead with file export, while notes also
explain artifact validation.

---

## Release 2: 0.0.16, geographic headlines

Status: `Released` (as part of 0.0.17)

### Goal

Close the largest basic feature gap: fetching news about a city, region, or
country without asking users to know Google News URL syntax.

### Verification gate

Before coding, verify the current Google News RSS geographic route with live
requests in at least:

- `language="en", country="US", location="New York"`
- `language="ro", country="RO", location="Bucharest"`

Expected candidate route is `headlines/section/geo/<encoded location>`, but do not
implement from memory. Confirm status, feed validity, and locale parameters.

### Exact public API

Add matching methods:

```python
GoogleNewsClient.location_news(
    location: str,
    *,
    max_results: Optional[int] = None,
) -> List[Article]

await AsyncGoogleNewsClient.location_news(
    location: str,
    *,
    max_results: Optional[int] = None,
) -> List[Article]
```

- Validate `location` as a non-empty string after stripping.
- Preserve internal whitespace in the value.
- Raise `ValidationError(field="location", value=...)` for invalid input.
- Return the same six-key base article shape.
- Do not add `mode` until SearchAPI location semantics are verified and can match
  the method's meaning.

Add CLI:

```bash
google-news location "Bucharest" --max-results 10 --format json
```

It receives the common locale, result, format, decode, and output options, but no
date, domain, or SearchAPI mode options.

Add MCP tool:

```python
location_news(
    location,
    max_results=None,
    language="en",
    country="US",
    decode_links=True,
    extract_text=True,
)
```

### Implementation map

- Reuse `_build_url`; add a dedicated location-path builder with correct percent
  encoding and no double encoding.
- Add the methods in `client.py`.
- Register the CLI subcommand in `cli.py`.
- Add the MCP function and register it in `create_mcp_app`.
- Update the source-tree MCP wrapper exports.
- Update public docs and both MCP READMEs.

### Tests

- Exact URL encoding for spaces, diacritics, slash, ampersand, plus, and `q=`.
- Empty, whitespace-only, and non-string validation.
- Sync/async parity against identical feed fixtures.
- Cache key isolation between locations and locales.
- CLI forwarding, output, decoding, and error behavior.
- MCP registration, forwarding, enrichment on/off, and error response.
- Two live integration probes from the verification gate.

### Acceptance criteria

- Existing search/top/batch URLs and results are unchanged.
- Location results work in two locale combinations.
- Special characters are encoded exactly once.
- Sync, async, CLI, and MCP return equivalent base data before enrichment.

### Out of scope

- No geocoding, coordinates, or country-name lookup.
- No claim that every arbitrary neighborhood has a feed.
- No fallback from location feeds to keyword search.

### Discoverability asset

README section and release example titled “Local Google News headlines in
Python.” Add relevant existing PyPI keywords only if the metadata vocabulary is
accurate; do not stuff keywords.

---

## Release 3: 0.0.17, safe advanced query construction

Status: `Released` (as 0.0.17)

### Goal

Help research and OSINT users build Google News queries without manual quoting or
operator mistakes, while leaving raw string queries fully supported.

### Exact public API

Add a public immutable `NewsQuery` value object in `google_news_api/query.py`:

```python
NewsQuery(
    text: str = "",
    *,
    exact_phrase: Optional[str] = None,
    any_words: Optional[List[str]] = None,
    exclude_words: Optional[List[str]] = None,
    in_title: Optional[str] = None,
)

query = NewsQuery(...).build()
str(query) == query.build()
```

Rules:

- At least one positive term among `text`, `exact_phrase`, `any_words`, or
  `in_title` is required.
- Strip surrounding whitespace; reject empty list entries.
- Escape embedded double quotes and backslashes deterministically.
- Render:
  - text as entered after trim;
  - exact phrase as `"..."`;
  - any words as `(word1 OR word2)`, quoting multi-word entries;
  - excluded terms with `-`, quoting multi-word entries;
  - title match as `intitle:"..."`.
- Preserve insertion order and remove exact duplicate list entries.
- `build()` returns a string accepted by existing `search`.
- Do not make existing `search` accept `NewsQuery`; users pass `str(query)`.
  This avoids widening and complicating the existing runtime contract.

Export `NewsQuery` from `google_news_api`.

Add CLI search/batch options:

- `--exact-phrase TEXT`
- repeatable `--any-word TEXT`
- repeatable `--exclude-word TEXT`
- `--in-title TEXT`
- `--show-query`

The positional query remains required for this release. Advanced options augment
it. `--show-query` prints the final Google News query to stderr before executing,
so JSON/CSV stdout remains valid.

### Implementation map

- New `google_news_api/query.py`.
- Public export and typing coverage.
- CLI constructs `NewsQuery`, then forwards its built string to existing client
  methods.
- Keep date and domain operators owned by the client so they cannot be emitted
  twice by the builder.

### Tests

- Every field independently and in combination.
- Embedded quotes, backslashes, Unicode, ampersands, plus signs, and `q=`.
- Stable order and exact duplicate removal.
- Invalid all-empty queries and empty list values.
- Result composed with existing date/domain filters without double encoding.
- CLI JSON stdout remains parseable with `--show-query`.
- Raw string search behavior remains identical.

### Acceptance criteria

- Existing raw queries produce identical URLs.
- Builder output is deterministic and documented.
- No user input is interpreted as a date or domain filter by the builder.
- Query preview never contaminates machine-readable stdout.

### Out of scope

- No general-purpose Google search DSL parser.
- No automatic correction of arbitrary raw operators.
- No mutable fluent builder.

### Discoverability asset

Publish a concise advanced-search example for exact phrase, title, source domain,
and date range. Use phrases users actually search for, such as “Google News exact
phrase Python.”

---

## Release 4: 0.0.18, result normalization and deduplication

Status: `Released`

```text
Implementation started: 2026-08-26
Starting PyPI version: 0.0.17
Files changed: result helpers and types, CLI flags, tests, README, changelog,
  package metadata, and lockfile
Release commit: 5fde04a269e4907295ff17c94b23df86283a2cbc
Tag: v0.0.18 -> 5fde04a269e4907295ff17c94b23df86283a2cbc
PyPI upload verified: 2026-08-26; wheel and sdist published through trusted
  publishing
Post-release fix: 1363325c02d65471cd19005fee6ba5ab1490b8c6 reformatted
  comments only; main CI passed
Status: Released
```

### Goal

Make results immediately useful for datasets and monitoring without changing the
existing article dictionary.

### Exact public API

Add pure helpers in `google_news_api/results.py`:

```python
parse_published(value: Optional[str]) -> Optional[datetime]
source_domain(article: Mapping[str, Any]) -> Optional[str]
deduplicate_articles(
    articles: Iterable[Article],
    *,
    by: str = "id",
) -> List[Article]
sort_articles(
    articles: Iterable[Article],
    *,
    newest_first: bool = True,
) -> List[Article]
normalize_article(article: Article) -> NormalizedArticle
normalize_articles(articles: Iterable[Article]) -> List[NormalizedArticle]
```

Add `NormalizedArticle` as an `EnrichedArticle`-style typed dictionary with the
base six keys plus optional:

- `published_datetime`: timezone-aware UTC `datetime`
- `source_domain`: normalized lowercase hostname when derivable

Rules:

- Helpers never mutate input dictionaries.
- RFC 2822 parsing uses the standard library.
- Naive parsed dates are treated as UTC only when the source format lacks a zone;
  document this.
- Invalid or missing dates return `None`, not an exception.
- `source_domain` prefers a decoded/non-Google `link`; it returns `None` for a
  Google News link rather than pretending the publisher name is a domain.
- Deduplication keeps first occurrence and supports `by="id"`, `"link"`, or
  `"title"`.
- For missing selected keys, fall back in order `id`, `link`, normalized title;
  articles with no usable identity remain distinct.
- Invalid `by` raises `ValidationError`.
- Sorting is stable. Undated articles are always last.

Add CLI flags to search, batch, top, and location:

- `--deduplicate`
- `--sort newest|oldest`
- `--normalize`

All are off by default. JSON gains normalized fields only with `--normalize`.
For CSV, append `published_datetime` and `source_domain` columns only when
normalization is requested. Table output stays at its existing four columns.

### Tests

- RFC 2822 zones, invalid dates, missing dates, and UTC normalization.
- IDs, links, case/whitespace-normalized titles, and missing identities.
- Stable order and no mutation.
- Google links versus publisher links for domains.
- Combined decode, normalize, dedupe, and sort ordering.
- Batch groups processed independently.
- JSON datetime serialization uses ISO 8601 with `+00:00`.

### Acceptance criteria

- With all flags omitted, output matches prior releases.
- Pure helpers accept generators and return new lists.
- Enriched datetime values are real `datetime` objects in Python and ISO strings
  only at serialization boundaries.
- Duplicate handling is deterministic across sync/async-derived results.

### Out of scope

- No fuzzy or semantic duplicate detection.
- No pandas dependency.
- No global sorting across batch query groups.

### Discoverability asset

Add a “Build a clean Google News dataset” example showing decode, dedupe,
chronological sort, and JSON export.

---

## Release 5: 0.0.19, first-class article enrichment

Status: `Released`

```text
Implementation started: 2026-08-30
Starting commit: 5724da58d8f1e787bd23e9126908230597418c4b
Starting PyPI version: 0.0.18
Baseline downloads day/week/month: 25 / 378 / 1,686
Baseline stars/forks/watchers: 17 / 3 / 1
Assumptions verified: PyPI 0.0.18; Trafilatura 2.2 documentation retains
  extract(raw_document) plain-text behavior; existing MCP extraction uses
  aiohttp plus trafilatura; SearchAPI attribution and pytest-temp ignore changes
  are preserved in the same local candidate
Local validation: 181 offline tests and 205 full live tests passed; black,
  isort, flake8, poetry check, wheel/sdist build, twine checks, artifact
  inspection, and isolated base/extract/MCP wheel installs passed; a live
  one-article decode and extraction returned a publisher URL and 3,541 text
  characters
Release commit: 542b160
Tag: v0.0.19 -> 542b160
PyPI upload verified: 2026-09-04; wheel and sdist published through trusted publishing
7-day metrics:
28-day metrics:
Status: Released
```

### Goal

Unify direct-link decoding and optional full-text extraction across Python, CLI,
and MCP instead of keeping extraction embedded in the MCP server.

### Packaging

- Add optional extra `extract` containing the current extraction dependencies
  required by reusable enrichment.
- Keep `[mcp]` installing everything it currently installs, including extraction.
  Existing `pip install "google-news-api[mcp]"` must continue to work.
- Core RSS/search/decode usage must not import extraction dependencies.

### Exact public API

Add `google_news_api/enrichment.py` with:

```python
class ArticleEnricher:
    def __init__(
        self,
        client: GoogleNewsClient,
        *,
        max_concurrent: int = 5,
        timeout: float = 30.0,
        delay: float = 1.0,
    )

    def enrich(
        self,
        articles: Iterable[Article],
        *,
        decode_links: bool = True,
        extract_text: bool = False,
    ) -> List[EnrichedArticle]

class AsyncArticleEnricher:
    # matching constructor with AsyncGoogleNewsClient
    async def enrich(...same keyword behavior...) -> List[EnrichedArticle]
```

Rules:

- Never mutate input dictionaries.
- Preserve input ordering and list length.
- When decoding succeeds, move the original URL to `google_link` and put the
  decoded URL in `link`.
- When decoding fails, leave the article unchanged.
- `extract_text=True` implies link decoding because extraction needs a publisher
  URL.
- Successful extraction sets `text`, including an empty string when a reachable
  article has no extractable body.
- A decode or extraction failure for one article does not fail the whole list.
- Invalid configuration raises existing validation exceptions before work starts.
- Missing `[extract]` dependencies raise one actionable runtime error containing
  `pip install "google-news-api[extract]"`.

Refactor MCP `_enrich_articles` to delegate to `AsyncArticleEnricher` without
changing tool defaults or result behavior.

Add CLI `--extract-text`. It implies `--decode-links` and requires the extra.

### Tests

- Sync and async parity.
- Input immutability and result alignment with mixed success/failure.
- Dependency absent message without importing optional modules at package import.
- Concurrency limit, delay, and timeout forwarding.
- Redirected publisher URLs and empty extraction.
- MCP characterization tests remain green before and after refactor.
- CLI missing-extra exit behavior and successful JSON/CSV output.
- No extraction for `extract_text=False`.

### Acceptance criteria

- Existing MCP output fixtures are unchanged.
- `import google_news_api` works without optional dependencies.
- One failed article never shifts text onto another article.
- No more duplicate extraction implementation in the MCP module.
- Core wheel size and mandatory dependency set do not materially increase.

### Out of scope

- No paywall bypass.
- No browser automation.
- No promise that every site is extractable.
- No images, author extraction, or summarization.

### Discoverability asset

Add a “Google News full article text in Python” example with a clear limitation
note. This is a high-value release and should include executable sync and async
snippets.

---

## Release 6: 0.0.20, production HTTP and retry controls

Status: `Released`

### Goal

Let production users configure networking without monkeypatching internals, while
retaining exactly the current defaults.

### Exact constructor additions

Append keyword-only options to both clients:

```python
GoogleNewsClient(
    language="en",
    country="US",
    requests_per_minute=60,
    cache_ttl=300,
    *,
    timeout=30.0,
    max_retries=3,
    retry_backoff=2.0,
    proxy=None,
    headers=None,
    transport=None,
)
```

Async receives the same logical options; `transport` uses the matching httpx
transport type.

Rules:

- Existing positional construction remains valid.
- Existing effective defaults remain unchanged.
- `headers` overlays package defaults without mutating `CHROME_HEADERS`.
- `proxy`, `transport`, and timeout are passed using the installed httpx API
  verified from its documentation and current version. Do not guess parameter
  names.
- `proxy` and `transport` may be used together only if httpx explicitly supports
  the combination; otherwise validate and reject it.
- Validate positive timeout and retry backoff, and non-negative retry count.
- Retry only current retryable errors plus HTTP 429 and selected transient 5xx
  statuses explicitly listed in code and docs.
- Honor numeric `Retry-After` for 429, capped by a documented maximum. Add jitter
  without changing the first-attempt behavior.
- Do not retry validation, parsing, or non-transient 4xx errors.
- SearchAPI requests use the same configured timeout/proxy/transport through the
  client's shared httpx instance.

Integrate the public `ClientConfig` rather than abandoning it:

```python
GoogleNewsClient.from_config(config: ClientConfig) -> GoogleNewsClient
AsyncGoogleNewsClient.from_config(config: ClientConfig) -> AsyncGoogleNewsClient
```

Extend `ClientConfig` with new fields using current defaults. Direct constructors
remain primary and unchanged.

### Implementation notes

- Replace import-time retry decorators on fetch methods with instance-aware retry
  loops or an instance-aware helper.
- Keep retry helpers public and backward compatible; do not rewrite their
  semantics as collateral work.
- Use injected httpx transports for deterministic tests.
- Ensure close/aclose ownership is clear: clients always own the httpx client they
  construct, but not a caller-provided transport beyond httpx's documented
  lifecycle.

### Tests

- Exact default constructor characterization.
- Timeout, headers, proxy, and transport forwarding in sync and async.
- No mutation of global headers.
- Retry counts, backoff sequence, jitter bounds, and `Retry-After`.
- No retry for parsing, validation, and permanent HTTP errors.
- Close/aclose behavior and context managers.
- `from_config` parity with equivalent direct construction.
- SearchAPI provider reuses configured client settings.

### Acceptance criteria

- Existing tests pass without changing their call sites.
- Default request count and delays match previous behavior except that
  `Retry-After` is correctly honored.
- Custom transport enables a complete search test with no monkeypatching.
- No new mandatory dependency.

### Out of scope

- No proxy pool or automatic proxy rotation.
- No provider-specific credential object.
- No public mutable session property.

### Discoverability asset

Document “Using google-news-api behind a proxy” and “Testing with
httpx.MockTransport” as concise recipes.

---

## Release 0.0.21, remote pipeline hotfix

Status: `Released`

```text
Implementation started: 2026-09-12
Release commit: c47c615fa402b37083182f2b39f7e6659638065a
Tag: v0.0.21
Status: Released
```

### Goal

Hotfix to resolve remote pipeline formatting errors for `black` and `isort`.

---

## Release 7: 0.0.22, incremental monitoring

Status: `Released`

```text
Implementation started: 2026-09-16
Release commit: 2c11ba61fa1dfa3042a529bf002b624013d331e7
Tag: v0.0.22
Status: Released
```

### Goal

Turn existing search, normalization, deduplication, and file output into a safe
news-monitoring workflow for cron jobs and long-running terminals.

### Exact CLI

Add:

```bash
google-news watch "semiconductor supply chain" \
  --when 24h \
  --interval 300 \
  --state .news-state.json \
  --format jsonl \
  --output new-articles.jsonl
```

Options:

- Search/date/domain/locale/mode options matching `search`.
- `--interval SECONDS`, default 300, minimum 10.
- `--state PATH`, required unless `--once`.
- `--once` performs one poll and exits.
- `--emit-existing` emits first-poll results; default seeds state silently.
- `--max-seen`, default 10,000, bounds state growth.
- Output format is `jsonl` or `table`; default `jsonl`.
- Reuse decode, normalize, and extract options.

### State contract

- State is a private implementation JSON document with a schema version, query
  fingerprint, and bounded ordered set of article identities.
- Identity order: `id`, decoded publisher link, original link, normalized title
  plus published value.
- Write state atomically through a temporary sibling file and replace.
- Refuse a state file whose query fingerprint differs unless `--reset-state` is
  explicitly supplied.
- `--reset-state` replaces only the named state file after validating its path.
- Graceful Ctrl+C flushes completed-poll state and exits 130.
- A failed poll must not erase state or emit partial corrupted JSON.
- Never start parallel polls. The interval begins after the previous poll ends.

### Library scope

Keep monitoring orchestration in `google_news_api/monitor.py` so it can be tested,
but do not add a long-running method to either client. Public API:

```python
class ArticleTracker:
    def __init__(self, state_path, *, max_seen=10_000)
    def filter_new(
        self,
        articles: Iterable[Article],
        *,
        fingerprint: str,
        emit_existing: bool = False,
    ) -> List[Article]
```

Only `ArticleTracker` is public. Poll scheduling remains CLI code.

### Tests

- First run seed versus emit behavior.
- Second run emits only unseen articles.
- All identity fallback paths.
- Bounded state eviction preserves most recent identities.
- Fingerprint mismatch and explicit reset.
- Atomic state write failure leaves prior state readable.
- Ctrl+C exit and completed poll persistence.
- No overlapping polls with a slow fake client.
- JSONL emits exactly one valid JSON object per line.
- Search and enrichment failures do not corrupt state.

### Acceptance criteria

- Watch can run twice against fixtures and emit only the added article.
- State remains bounded and recoverable.
- Existing CLI commands and formats are unchanged.
- No daemon, database, or scheduling dependency.

### Out of scope

- No email, Slack, webhook, or desktop notifications.
- No background service installation.
- No semantic duplicate detection.
- No guarantees of complete historical coverage.

### Discoverability asset

Add cron and terminal examples under “Monitor a topic for new coverage.” Make
clear that users control polling frequency and should avoid abusive intervals.

---

## Release 8: 0.0.23, related coverage clusters

Status: `Released`

### Goal

Expose related publisher coverage present in Google News feed summaries without
changing normal article results. This differentiates the package for media
research.

### Verification gate

Capture sanitized RSS fixtures from at least two topic feeds and two locales.
Confirm that related links and titles are present in stable feed data before
implementing. If Google News no longer supplies usable related coverage, mark
this release `Deferred` and move Release 9 forward without inventing a scraper.

### Exact public API

Add types:

```python
class RelatedArticle(TypedDict):
    title: Optional[str]
    link: Optional[str]
    source: Optional[str]

class ArticleCluster(TypedDict):
    primary: Article
    related: List[RelatedArticle]
```

Add matching methods:

```python
GoogleNewsClient.top_news_clusters(
    topic="WORLD",
    *,
    max_results=None,
) -> List[ArticleCluster]

await AsyncGoogleNewsClient.top_news_clusters(
    topic="WORLD",
    *,
    max_results=None,
) -> List[ArticleCluster]
```

- `max_results` limits primary clusters, not related articles.
- Primary article uses the existing six-key shape.
- Related parsing failure returns an empty `related` list for that primary item.
- Deduplicate related entries by link, then normalized title.
- Do not decode related links automatically.

Add CLI:

```bash
google-news clusters --topic TECHNOLOGY --format json
```

Only JSON and table formats initially. Table renders a primary row followed by
indented related rows. No CSV until a stable flattening contract is justified.

Add MCP `top_news_clusters` with optional decoding but no text extraction for
related entries in this release. Default `decode_links=False` to avoid request
amplification.

### Implementation map

- Parse only stored RSS summary markup with `selectolax`; never request Google
  News HTML pages for clusters.
- Keep normal `_parse_articles` unchanged.
- Add a separate cluster parser with fixture-based tests.
- Sanitize fixtures so they contain no irrelevant tracking data.

### Tests

- Multiple known summary layouts, absent summary, malformed HTML, duplicates,
  missing source, and missing link.
- Primary result equality with normal `top_news`.
- `max_results` applies to primaries.
- Sync/async parity.
- CLI JSON schema and table rendering.
- MCP request amplification guard and decoding opt-in.
- Fixture drift live probe before release.

### Acceptance criteria

- `top_news` output is byte-for-byte unchanged.
- Cluster parsing needs no extra network request.
- Malformed related markup never drops the primary article.
- A documented request-count test prevents accidental N+1 behavior.

### Out of scope

- No clustering of arbitrary keyword search results.
- No machine-learning similarity.
- No full-text extraction for every related item.

### Discoverability asset

Publish an example comparing how several publishers cover one top story. Avoid
claims about bias detection or completeness.

---

## Release 9: 0.0.24, deployable and documented MCP server

Status: `Released`

```text
Implementation started: 2026-09-27
Release commit: 051612a446a4f0ee350be001338ee8371ef4128f
Tag: v0.0.24
PyPI upload verified: 2026-09-27; clean MCP extra install, pip check, and app creation passed
Status: Released
```

### Goal

Make the existing MCP capability easy to configure locally and safe to deploy,
without changing stdio defaults.

### Verification gate

Read the installed `mcp` version and its official FastMCP documentation before
choosing transport names, CLI flags, and host/port APIs. Do not infer these from
older examples. Pin only as narrowly as compatibility evidence requires.

### Exact CLI contract

Keep:

```bash
google-news-mcp
```

equivalent to stdio.

Add:

```bash
google-news-mcp --transport stdio
google-news-mcp --transport streamable-http --host 127.0.0.1 --port 8000
```

Rules:

- Default transport remains `stdio`.
- Default HTTP host is `127.0.0.1`, never `0.0.0.0`.
- `--host` and `--port` are invalid with stdio.
- Validate port range.
- Do not add authentication. State clearly that operators must provide a trusted
  reverse proxy before exposing the server beyond localhost.
- Add `google-news-mcp --version`.

### Server improvements

- Add a lightweight `server_info` tool returning package version, supported
  modes, topics, and feature availability. It makes no network request.
- Add location and cluster tools from prior releases if their release shipped.
- Delegate all enrichment to the shared enrichment module.
- Add explicit shutdown that closes cached async clients.
- Bound cached locale clients with an LRU limit to avoid unbounded growth.
- Keep existing tool names, parameter defaults, and in-band error dictionaries.

### Documentation

Add tested configuration snippets for the currently supported mainstream MCP
clients, but verify each snippet against that client's official documentation at
implementation time. Do not publish a configuration that has not been launched
successfully.

Add:

- stdio installation and configuration;
- local streamable HTTP setup;
- headline-only performance configuration;
- extraction dependency and limitations;
- security warning for network transport;
- troubleshooting for missing extras and API keys.

### Tests

- Default no-argument stdio invocation.
- Argument validation and localhost defaults.
- App registration and stable existing tool schemas.
- `server_info` without network/dependencies beyond MCP.
- Cached-client LRU and shutdown/aclose.
- Missing optional dependency message.
- End-to-end stdio smoke with an MCP client if supported by installed tooling.
- HTTP transport starts on an ephemeral local port, responds, and shuts down.

### Acceptance criteria

- Existing MCP configurations continue working unchanged.
- Server never binds publicly by default.
- Repeated locale combinations cannot grow the client cache without bound.
- Shutdown closes every cached client.
- Every published configuration snippet is manually smoke-tested.

### Out of scope

- No hosted public service.
- No authentication implementation.
- No Docker image unless required for a verified client workflow; a Docker image
  is a separate operational commitment.
- No non-MCP REST API.

### Discoverability asset

Add a short “Google News MCP server” setup section near the top of the README and
link to the detailed MCP README. Use the GitHub release to demonstrate one actual
tool call, not merely installation.

---

## Release 10: 0.1.0, compatibility and documentation milestone

Status: `Released`
Release commit: `20e3fde`
Tag: `v0.1.0`
PyPI upload verified: 2026-10-04; wheel and sdist published through trusted publishing
Post-release dependencies: PR #32 and #33 merged cleanly into main (beb393a)

### Goal

Declare the accumulated additive API dependable enough for wider use, with
complete reference documentation, tested examples, and no breaking changes from
`0.0.24`.

### Release principle

`0.1.0` is a confidence milestone, not a rewrite. Do not rename APIs, rearrange
result keys, remove deprecated behavior, change defaults, or replace dictionaries
with models.

### Scope

- Audit and document every public export in `google_news_api.__all__`.
- Define public versus internal modules. Anything not exported remains internal
  unless already documented as public.
- Add a concise compatibility policy:
  - additive changes in minor releases;
  - bug fixes in patch releases;
  - deprecation warning for at least two minor releases before removal;
  - breaking changes only in a future explicitly planned major release.
- Generate an API reference site from source signatures and curated prose using a
  lightweight documentation tool chosen after checking current maintenance and
  Python support.
- Host documentation through GitHub Pages only after its build is reproducible
  in CI.
- Add runnable guides for:
  - first search;
  - async batch research;
  - geographic headlines;
  - advanced queries;
  - clean dataset export;
  - full-text enrichment;
  - proxy/custom transport;
  - incremental monitoring;
  - MCP setup.
- Turn code snippets into tested examples or doctest-style checks where practical.
- Keep the existing contribution, security, and issue guidance current rather
  than duplicating it in a new documentation system.
- Add CI status and documentation badges only after their targets are stable.

### Quality targets

- Preserve or improve the current 85% total branch-aware coverage.
- Raise `client.py` branch-aware coverage from its current 76% through focused
  decoding and retry characterization; do not add synthetic tests just to meet
  a percentage.
- Full offline coverage of async URL decoding and retry paths.
- Zero unmarked live tests.
- Public sync/async parity test table.
- Built wheel and sdist smoke-tested on minimum and latest Python.
- All examples run in CI without live requests by using recorded fixtures or
  injected transports.
- No known high-severity dependency vulnerabilities in runtime dependencies,
  evaluated with a current advisory source. Do not claim “secure” based only on
  one scanner.

### Performance and request-budget checks

Add stable fixture-based benchmarks as regression checks, not marketing claims:

- one cached versus uncached RSS search;
- sync and async batch request counts;
- decode concurrency bound;
- enrichment request count;
- cluster parsing with no additional request;
- monitor poll with no new results.

Fail CI on request-count regressions. Record timing but avoid brittle wall-clock
thresholds on shared runners.

### Packaging and metadata

- Review PyPI description, classifiers, keywords, and project URLs against
  shipped capabilities.
- Add a documentation URL.
- Verify README renders correctly on PyPI.
- Keep MIT license and Trusted Publishing.
- Confirm support for each advertised Python version; add a newer Python only
  after CI passes, and never drop 3.9 in this plan.

### Acceptance criteria

- Upgrading from `0.0.24` to `0.1.0` requires no code changes.
- Every documented snippet is executable and tested.
- Public API and compatibility policy are visible without reading source.
- Documentation deploys from a tagged, reproducible build.
- Package artifacts pass the universal release gate.
- All open regressions are resolved or the release is delayed.

### Out of scope

- No v1.0 promise.
- No breaking cleanup.
- No framework-specific integrations.
- No roadmap or growth-goal changes in the 0.1.0 release.

### Discoverability asset

The release page should be a compact overview of shipped, tested workflows with
links to guides. Announce only after PyPI installation and documentation links
are verified.

### Fresh-chat implementation order

1. Inventory `google_news_api.__all__`; document each export's stable contract
   and mark non-exported modules internal.
2. Select a maintained docs tool only after verifying local and CI builds. Put
   guides under `docs/` and make snippets run against fixtures or injected
   transports, never live feeds in CI.
3. Add sync/async parity and decoding/retry characterization tests before
   raising coverage targets. Record request counts, not elapsed-time limits.
4. Add the documentation URL to project metadata only after Pages deployment is
   reproducible. Expected changes are docs, README, examples/tests, metadata,
   and documentation workflow, not client behavior.

---

## Release 11: 0.1.1, custom Google News sections

Status: `Released`
Release commit: `d6bc637`
Tag: `v0.1.1`
PyPI upload verified: 2026-10-07; wheel and sdist published through trusted publishing
Post-release dependencies: PR #34 merged cleanly into main (a1c1f30)
Implementation decisions:
- Probed and characterized Google News RSS routing across en-US, it-IT, ro-RO, and de-DE; confirmed custom section tokens route via `https://news.google.com/rss/topics/<TOKEN>` (200 OK) rather than legacy `headlines/section/topic/` (which redirects 301 to homepage).
- Supported `topic_token` keyword-only parameter across `GoogleNewsClient.top_news`, `GoogleNewsClient.top_news_clusters`, `AsyncGoogleNewsClient.top_news`, and `AsyncGoogleNewsClient.top_news_clusters`.
- Added `--topic-token` to CLI `top` and `clusters` subcommands; forwarded `topic_token` in MCP tools `top_news` and `top_news_clusters`.
- Enforced single encoding pass with `safe=""`, rejecting URLs, empty/whitespace strings, non-strings, and custom named topic pairings.
- Retained 100% backward compatibility for named topics and existing defaults. Added 35 test cases (320 passed) and 2 frozen locale fixtures (en-US and it-IT).

### Goal

Expose Google News section tokens safely for users who need sections beyond the
eight named defaults.

### Scope

- Add an explicit `topic_token` keyword-only argument to sync and async top
  headline methods, the `top` CLI command, and the MCP tool.
- Reject empty tokens and prevent use with a named topic in the same call.
- Preserve all current named-topic behavior, URLs, and defaults.
- Verify token routing with frozen fixtures and a minimal live probe in two
  locales before release.

### Fresh-chat implementation order

1. Add `topic_token: Optional[str] = None` after `*`; retain the current
   `topic="WORLD"` default. Reject non-strings, empty tokens, and a token with
   a non-default named topic.
2. Route through the existing topic URL helper with exactly one encoding pass.
   Never accept arbitrary URLs.
3. Cover sync/async exact URLs, default-topic regressions, invalid arguments,
   CLI and MCP forwarding, cache-key isolation, and two saved locale fixtures.
4. Document token acquisition, upstream instability, and why named topics are
   preferred for portable programs.

## Release 12: 0.1.2, opt-in article provenance

Status: `Planned`

### Goal

Make publisher attribution and machine-readable timestamps available without
changing the six-key base article contract.

### Scope

- Extend only `NormalizedArticle` and normalization helpers with optional
  `published_iso` and `source_url` fields when the feed supplies them.
- Keep undecoded Google URLs and absent feed metadata as `None`; never invent a
  publisher URL from a display name.
- Add CLI normalization output and MCP enrichment parity only behind existing
  opt-in switches.
- Add malformed, absent, and locale-varied fixture coverage.

### Fresh-chat implementation order

1. Extend `NormalizedArticle`, not `Article`; preserve non-mutation and current
   normalized fields.
2. Emit `published_iso` only from a successfully parsed UTC date. Preserve
   absent/invalid input as `None`.
3. Preserve a feed-provided publisher URL only after validation. Never derive a
   URL from a publisher display name or an undecoded Google URL.
4. Test malformed dates/URLs, JSON and CSV serialization, CLI normalization,
   MCP opt-in parity, and sync/async output parity.

## Release 13: 0.1.3, decoding reliability and typing

Status: `Planned`

### Goal

Reduce duplicated URL-decoding risk and make the published type surface CI
checked.

### Scope

- Extract pure Google News decoding parsing into internal shared helpers while
  retaining sync/async public methods and exceptions unchanged.
- Characterize retry, malformed payload, and async/sync parity behavior before
  refactoring.
- Add mypy to CI for public modules and `py.typed`, with a narrowly documented
  baseline if upstream dependency stubs require it.
- Add fixture-based request-count tests for decode concurrency.

### Fresh-chat implementation order

1. Add characterization tests for current sync/async decoding, errors, retry
   counts, ordering, timeouts, and malformed payloads before moving code.
2. Extract only pure parsing/validation into an internal helper; leave HTTP I/O
   in the clients and preserve public exceptions exactly.
3. Add mypy incrementally for exported modules and `py.typed`; do not suppress
   broad error classes to force a passing job.
4. Add request-count and concurrency-cap tests using injected transports.

## Release 14: 0.1.4, monitor portability and observability

Status: `Planned`

### Goal

Make the existing monitor easier to operate in scheduled environments without
adding a hosted service or notification system.

### Scope

- Add a read-only state inspection command and a dry-run mode that reports
  prospective new items without writing state or output files.
- Add explicit state schema diagnostics and recovery guidance.
- Preserve state format, polling defaults, and duplicate identity semantics.
- Test interrupted writes, read-only state paths, and dry-run non-mutation.

### Fresh-chat implementation order

1. Add `watch --dry-run` to poll once and render prospective new articles
   without creating, mutating, resetting, or truncating state/output files.
2. Add a read-only state inspection command reporting schema version,
   fingerprint, count, and validity without printing private article data.
3. Reuse `ArticleTracker`; do not add a daemon, database, notifier, lockfile,
   or background scheduler.
4. Test corrupt/missing/read-only state, atomic-write interruption, JSONL/table
   rendering, Ctrl+C, dry-run non-mutation, and unchanged default watch behavior.

---

## Release dependency order

The sequence is intentional:

1. `0.0.15` makes artifact and compatibility checks trustworthy.
2. `0.0.16` adds a proven core retrieval use case.
3. `0.0.17` makes research queries safer.
4. `0.0.18` supplies deterministic result processing.
5. `0.0.19` consolidates enrichment before more workflows depend on it.
6. `0.0.20` makes request behavior configurable and testable.
7. `0.0.22` builds monitoring on dedupe, output, enrichment, and retries.
8. `0.0.23` adds research-focused related coverage without touching base results.
9. `0.0.24` exposes the mature capabilities safely through MCP.
10. `0.1.0` documents and freezes the compatibility expectations.
11. `0.1.1` adds custom sections before further result enrichment.
12. `0.1.2` adds provenance only through opt-in normalized results.
13. `0.1.3` hardens shared decoding and published typing.
14. `0.1.4` improves monitor operation without expanding into notifications.

Do not reorder enrichment after monitoring or production HTTP controls after
network transport work. Release `0.0.23` may be deferred if its live verification
gate fails; that is the only planned conditional release.

## Decision log

### Accepted

- Maintainer releases go directly through `main`; do not open release PRs.
- Track roadmaps, growth goals, and adoption metrics in this plan, as approved on 2026-10-09.
- Keep dictionary results rather than introducing dataclass/Pydantic models.
- Keep raw query strings and add a separate query builder.
- Keep file export in the CLI rather than adding I/O to retrieval clients.
- Use optional extras for extraction.
- Keep monitoring notifications out of scope.
- End the sequence at `0.1.0` as a non-breaking confidence milestone.

### Rejected for this sequence

- Multi-provider aggregation: conflicts with the focused Google News identity.
- Semantic analysis, sentiment, and LLM summaries: large dependency and product
  expansion, not core retrieval.
- Browser automation for paywalls: operationally heavy and legally sensitive.
- Hosted API service: changes the project from a package into an operated service.
- Mutable result model migration: breaking and unnecessary.
- Automatic telemetry: incompatible with a lightweight privacy-respecting client.
- Treating future roadmap work as already shipped behavior.

## Per-release maintainer record template

Copy this block under the selected release when work starts:

```text
Implementation started:
Starting commit:
Starting PyPI version:
Baseline downloads day/week/month:
Baseline stars/forks/watchers:
Assumptions verified:
Files changed:
Compatibility tests added:
Live probes run:
Artifact smoke environments:
Known limitations:
Deferred items:
Release commit:
Tag:
PyPI upload verified:
7-day metrics:
28-day metrics:
Status:
```
