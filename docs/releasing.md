# Release checklist

Maintainer releases go directly through `main`. Do not open a release pull
request.

1. Synchronize local `main` with `origin/main` and confirm the tracked working
   tree is clean.
2. Keep `pyproject.toml` on the previous published version while implementing
   code, tests, workflows, and documentation.
3. Run:

   ```bash
   poetry install --with dev --all-extras
   poetry run pytest -q -m "not integration" --strict-markers
   poetry run pytest -q
   poetry run black --check google_news_api tests examples mcp_server
   poetry run isort --check-only google_news_api tests examples mcp_server
   poetry run flake8 google_news_api tests examples mcp_server
   ```

4. Run the live integration suite before release:

   ```bash
   poetry run pytest -q -m integration --run-integration --strict-markers
   ```

5. Update `pyproject.toml`, `CHANGELOG.md`, README examples, and release notes to
   the target version only after the implementation is complete.
6. Install the pinned release tools and validate the final tree:

   ```bash
   python -m pip install poetry==2.3.2 twine==6.2.0
   poetry check
   poetry build
   python -m twine check dist/*
   ```

7. Install the wheel in fresh base and `[mcp]` virtual environments. Run
   `pip check`, verify both console entry points, import the base and MCP
   modules, and confirm `py.typed` is present.
8. Commit the complete release directly on `main` and push `main`.
9. Wait for every required CI job to pass. If CI fails, fix forward on `main`
   and repeat validation. Do not tag a failing commit.
10. Create `vX.Y.Z` from the exact successful `origin/main` commit. Publish a
    non-draft GitHub release for that tag to trigger PyPI Trusted Publishing.
11. Monitor the publishing workflow. After publication, install
    `google-news-api==X.Y.Z` from PyPI in a clean environment and repeat version,
    entry-point, artifact, and `pip check` smoke tests.
12. Record release metrics and outcomes only in the private local maintainer
    plan.

If an artifact is defective, yank it rather than attempting to replace the same
version.
