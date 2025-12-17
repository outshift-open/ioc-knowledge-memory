#!/bin/bash
set -e

echo "Running unit tests with pytest..."
poetry run pytest tests/ -v
poetry run pytest -v

echo "UNIT-TEST DONE"