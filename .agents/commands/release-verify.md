# Verify a release candidate

Read `AGENTS.md`, the entire `.agents/PRIVATE_RELEASE_PLAN.md`,
`.agents/FAILURE_RETROSPECTIVE.md`, and `docs/releasing.md`. Inspect the
worktree and version-bearing files first.

Confirm `pyproject.toml`, `CHANGELOG.md`, README examples, the selected private
plan release, the latest published PyPI version, and Git tags agree. Confirm the
target version has not already been used.

Run all safe offline tests, collection checks, pre-commit checks, Poetry
validation, builds, distribution metadata checks, and base plus MCP wheel smoke
checks possible in the environment. Do not modify release content merely to
make a check pass.

Do not publish, tag, push, create a GitHub release, or run live integration
tests unless the maintainer explicitly requests those actions.

Report failures first, then successful checks and the exact remaining manual or
CI-gated release steps.
