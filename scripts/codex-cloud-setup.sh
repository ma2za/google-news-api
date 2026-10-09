#!/bin/bash
set -euo pipefail
cd "$(dirname "${BASH_SOURCE[0]}")/.."

python3 -c 'import sys; assert sys.version_info >= (3, 10), "Cloud development requires Python 3.10 or newer"'
python3 -m venv .tools/poetry
.tools/poetry/bin/python -m pip install poetry==2.3.2 twine==6.2.0 'mkdocs-material==9.6.*'
export POETRY_VIRTUALENVS_IN_PROJECT=true
.tools/poetry/bin/python -m poetry install --with dev --all-extras
.tools/poetry/bin/python -m poetry run pre-commit install
