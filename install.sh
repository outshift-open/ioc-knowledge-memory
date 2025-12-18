#!/bin/bash
set -euo pipefail

TASK_VERSION="${TASK_VERSION:-v3.39.2}"
INSTALL_DIR="${INSTALL_DIR:-$HOME/.local/bin}"

has_cmd() { command -v "$1" >/dev/null 2>&1; }

install_poetry() {
    curl -sSL https://install.python-poetry.org | python3 - ||
    pip3 install poetry --user
}

install_task() {
    # Try package managers first
    if [[ "$(uname -s)" == "Darwin" ]] && has_cmd brew; then
        brew install go-task && return
    elif has_cmd apt; then
        sudo apt install -y task && return
    fi
    
    # Manual install
    mkdir -p "$INSTALL_DIR"
    local arch="amd64"; [[ "$(uname -m)" =~ arm64|aarch64 ]] && arch="arm64"
    local url="https://github.com/go-task/task/releases/download/${TASK_VERSION}/task_$(uname -s | tr '[:upper:]' '[:lower:]')_${arch}.tar.gz"
    curl -sL "$url" | tar -xz -C "$INSTALL_DIR" task
    chmod +x "$INSTALL_DIR/task"
    
    # Add to PATH if needed
    if ! echo "$PATH" | grep -q "$INSTALL_DIR"; then
        echo "export PATH=\"$INSTALL_DIR:\$PATH\"" >> ~/.zshrc
        export PATH="$INSTALL_DIR:$PATH"
    fi
}

# Install Poetry
has_cmd poetry || { echo "Installing Poetry..."; install_poetry; }

if ! echo "$PATH" | tr ':' '\n' | grep -qx "$HOME/.local/bin"; then
        export PATH="$HOME/.local/bin:$PATH"
fi

# Install dependencies  
poetry install

# Install Task
has_cmd task || { echo "Installing Task..."; install_task; }

echo "✓ Ready! Run 'task dev' to start"