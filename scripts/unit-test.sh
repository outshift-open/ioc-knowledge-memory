#!/bin/bash -e

# Install Poetry
echo "Installing Poetry..."
pip install poetry

echo "Installing dependencies with Poetry..."
poetry install

echo "Installing Taskfile..."
mkdir -p bin && curl -sL https://github.com/go-task/task/releases/download/v3.39.2/task_linux_amd64.tar.gz | tar -xz -C bin

echo "Running comprehensive unit tests..."
./bin/task test

echo "UNIT-TEST DONE"