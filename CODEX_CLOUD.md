# Cloud development handover

Repository: public `ma2za/google-news-api`, branch `main`. The package remains
at the already-published version `0.1.1`. This handover adds development setup,
not a package release.

## Environment setup

Use Linux with Python 3.10 or newer, Git, Bash, and Python's `venv` module.
Python 3.12 is the development validation target. Enable network access during
setup for PyPI dependencies and pre-commit hook repositories.

Configure the cloud setup command as:

```bash
bash scripts/codex-cloud-setup.sh
```

The script installs Poetry 2.3.2, Twine 6.2.0, and the same MkDocs Material 9.6
series used by CI in `.tools/poetry`. It installs locked development, extraction,
and MCP dependencies into `.venv`, then installs the Git pre-commit hook.
Repeating setup preserves source files and existing environments. No database,
Redis, Docker service, workstation path, or environment file is needed.

For each subsequent shell, expose the isolated tools:

```bash
export PATH="$PWD/.tools/poetry/bin:$PATH"
```

Cloud environment access and setup are configured as described in the
[official cloud environment guide](https://learn.chatgpt.com/docs/environments/cloud-environments).

## Validation

```bash
poetry run pytest -q -m "not integration" --strict-markers
poetry run pre-commit run --all-files
poetry check
poetry build
.tools/poetry/bin/python -m twine check dist/*
.tools/poetry/bin/python -m mkdocs build --strict
```

Live integration tests remain opt-in and require an explicitly authorized
release execution. The handover does not request Google News or SearchAPI data.
CI retains the Python 3.9 installation smoke and Python 3.10 through 3.14 test
matrix. Offline tests use committed fixtures and injected transports.

## Credentials

RSS is keyless by default. Optional SearchAPI modes read `SEARCHAPI_API_KEY`
directly from the environment. Supply that key through cloud configuration
only when using those modes. The previous development key is intentionally
discarded at the maintainer's request. The existing PyPI secret and Trusted
Publishing configuration are retained; no publishing credential is needed for
development.

## Maintainer context

The maintainer approved tracking the full release plan in `RELEASE_PLAN.md` on
2026-10-09. Every cloud checkout includes it. Read the complete plan, `AGENTS.md`,
and the existing release checklist before choosing release or roadmap work.
Confirm published versions against PyPI and version tags using
`git tag --list 'v*' --sort=-version:refname`. Planned work remains distinct from
already-shipped package behavior. No external context archive is needed.

## Continuity

The local and remote baseline file trees were identical despite rewritten
commit IDs. Development continues from the current remote history without a
force push or restoring superseded history. Verify a fresh clone and its tracked
release plan before removing the previous checkout and temporary environments.

Documentation is available in `docs/`; README links use that checked-in source.
No GitHub Pages site was configured at the handover checkpoint. Publishing a
documentation website is a separate action.

## Verified on 2026-10-09

A clean Linux Python 3.12 environment passed setup twice, all 320 offline tests
(28 live tests deselected), all nine pre-commit checks, Bash syntax, ShellCheck,
Poetry validation, wheel/sdist builds, Twine checks, and the strict documentation
build. Fresh base and MCP wheel installs and a fresh source-package install
passed metadata, import, entry-point, app-creation, and dependency checks.
No live news tests or package publication were performed.
