# Prepare a release candidate

Require one explicit semantic version argument. Refuse an existing published
version or Git tag.

Prepare `google-news-api` end to end, stopping before commit, tag, push, GitHub
release creation, PyPI publication, or announcement.

Read `AGENTS.md`, the entire `.agents/PRIVATE_RELEASE_PLAN.md`,
`.agents/FAILURE_RETROSPECTIVE.md`, `docs/releasing.md`, `CHANGELOG.md`,
`pyproject.toml`, relevant Git history, and the current worktree first. Preserve
unrelated worktree changes.

Implement only the selected release from the private plan. Keep the published
version unchanged until implementation is complete. Then synchronize
`pyproject.toml`, prepend the `CHANGELOG.md` entry, and update README examples
only for verified shipped behavior. Do not invent features or claims.

Run the safe offline validation and package checks from `docs/releasing.md`. Do
not run live integration tests unless the maintainer explicitly authorizes
them.

Report changed files, exact validation results, blockers, and remaining
maintainer actions.
