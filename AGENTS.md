# Agent instructions

This is the canonical project context for every coding agent. Read it before
assessing, planning, or changing the repository. Gemini-specific context may
exist locally, but no agent may rely on Gemini discovery alone.

## Mandatory context discovery

Read files by their known paths even when Git, ripgrep, or an ignore file hides
them.

- Read `.agents/README.md` when it exists.
- For any question about the next release, release readiness, roadmap, planned
  work, or what to implement next, read all of
  `.agents/PRIVATE_RELEASE_PLAN.md` before answering or editing.
- For release work, also read `.agents/FAILURE_RETROSPECTIVE.md`,
  `docs/releasing.md`, `CHANGELOG.md`, and `pyproject.toml`.
- Verify plan statuses against the latest Git tag and published PyPI version.
  If the private plan is stale, update its local status before selecting the
  first release that is not `Released`.
- Never infer that no plan exists from `rg --files`, `git status`, or tracked
  files alone. Private maintainer context is intentionally excluded from Git.

The private plan, private metrics, future promises, secrets, and credentials
must never be committed or published. Generic operational instructions and
sanitized failure retrospectives belong in `AGENTS.md` or tracked `.agents/`
files so every agent receives them.

## Project

This repository is a Python 3.9+ library, CLI, and optional MCP server for
fetching news from Google News through RSS with sync, async, URL decoding,
caching, and MCP support. Poetry owns dependencies, packaging, scripts, and the
lock file. The public package is `google-news-api`.

Read the relevant implementation, tests, and documentation before editing.
Keep changes focused and preserve existing public interfaces, defaults, JSON
keys, environment variables, console scripts, and MCP tool signatures as
required by `docs/compatibility.md`.

## Development

- Use the existing style and the simplest working implementation.
- Add a regression test for every bug fix and offline tests for new behavior.
- Update user-facing documentation and `CHANGELOG.md` for behavior changes.
- Do not edit `poetry.lock` unless dependency declarations change.
- Never expose or commit `.env` contents, credentials, tokens, cookies,
  captured request headers, or local service-account files.
- Preserve unrelated worktree changes.
- Tests must exercise actual logic. Integration fixtures must be frozen output
  from actual Google News RSS responses, not invented dummy responses.
- Include adversarial parser cases such as malformed XML, unusual encodings,
  and missing tags when relevant.
- On Windows, prefer `python -m <module>` over direct executable shims to avoid
  application-control policy blocks.

Standard validation:

```bash
poetry install --all-extras
poetry run pytest -q -m "not integration" --strict-markers
poetry run pre-commit run --all-files
```

Integration tests make live network calls. Run them only when the maintainer
has explicitly requested or authorized release execution.

## Releases

Follow `.agents/PRIVATE_RELEASE_PLAN.md` and `docs/releasing.md`. Portable
release preparation and verification prompts live in `.agents/commands/`.

- Keep the published version unchanged during implementation.
- Synchronize version metadata and public release notes only after the planned
  implementation is complete.
- Never reuse a published version or tag.
- Never bypass a failing check.
- Publish only from the exact commit that passed CI, using tag `vX.Y.Z`.
- At handoff, state files changed, checks run, checks not run, and remaining
  external actions.
