#!/bin/bash
set -e

echo "Running unit tests with pytest..."
poetry run pytest src/ -v
poetry run pytest -v

echo "UNIT-TEST DONE"