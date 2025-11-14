#!/bin/bash -e

# Install uv and dependencies
echo "Installing uv..."
pip install uv

echo "Installing dependencies with uv..."
uv sync --no-install-project

echo "Running unit tests..."
cd src/server
uv run python -m pytest test.py -v || python test.py

echo "UNIT-TEST DONE"