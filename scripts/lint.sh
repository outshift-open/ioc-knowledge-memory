#!/bin/bash
set -e

echo "Running Black formatter check..."
poetry run black --check src/

echo "Running Flake8 linter..."
poetry run flake8 src/ --max-line-length=120 --extend-ignore=E203,W503,W293,F401

echo "Linting DONE"
