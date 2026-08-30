I failed to run the full test suite and pre-commit checks locally before
committing and pushing a release tag. Before any future release push, run
`poetry run pre-commit run --all-files` and the full `pytest` suite.

On 2026-08-30, an agent incorrectly reported that no next release existed
because it inspected tracked release documentation and `rg --files` output but
did not open `.agents/PRIVATE_RELEASE_PLAN.md`, which is intentionally excluded
from Git. Every agent must read `AGENTS.md` and directly open the full private
plan for any next-release, roadmap, or release-readiness question. Absence from
Git or search output is not evidence that local maintainer context does not
exist.
