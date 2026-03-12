# Knowledge Memory Package - Namespace Strategy

## Overview

This document explains how the `knowledge-memory` package avoids namespace collisions with projects that have their own `server` module.

## The Problem

If a user's project has its own `server/` package and we published `server` as a top-level module, there would be a **namespace collision** - only one `server` would be accessible.

## The Solution

### For Installed Packages (Production)

When users install the wheel from Artifactory:
```bash
pip install knowledge-memory
```

The package structure is:
```
site-packages/
└── knowledge_memory/
    ├── __init__.py
    ├── knowledge_graph.py
    ├── knowledge_vector.py
    ├── server/           # Namespaced under knowledge_memory!
    │   ├── services/
    │   ├── schemas/
    │   └── database/
    └── app_logging/
```

**Key Point**: `server` is NOT a top-level module - it's `knowledge_memory.server`!

### How It Works

The source code uses a **try/except import pattern**:

```python
try:
    # Try namespaced import (works when installed as wheel)
    from knowledge_memory.server.services.knowledge_graph import knowledge_graph_service
except (ImportError, ModuleNotFoundError):
    # Fallback for development (when src/ is in PYTHONPATH)
    from server.services.knowledge_graph import knowledge_graph_service
```

**When Installed**:
- First import succeeds: `knowledge_memory.server.*` ✅
- No conflict with user's `server` module ✅

**During Development**:
- First import fails (knowledge_memory.server doesn't exist in source)
- Falls back to: `from server.*` (finds `src/server/`) ✅

### Setup.py Magic

The `setup.py` uses `package_dir` mapping to namespace `server` during build:

```python
package_dir = {
    "knowledge_memory": "src/knowledge_memory",
    "knowledge_memory.server": "src/server",      # Maps src/server → knowledge_memory.server
    "knowledge_memory.app_logging": "src/app_logging",
}
```

When the wheel is built:
- Files from `src/server/` are placed in `knowledge_memory/server/`
- Only `knowledge_memory` is listed as a top-level package
- No `server` at top level = no collision!

## For Developers

### Development Setup

1. **Add src/ to PYTHONPATH** (current approach):
   ```bash
   # In tests or dev scripts
   import sys
   sys.path.insert(0, 'src')
   ```

   This makes both `knowledge_memory` and `server` available during development.

2. **OR use editable install** (alternative):
   ```bash
   pip install -e .
   ```

   Note: The editable install adds `src/` to path, which works the same as option 1.

### Running Tests

Tests already use the path manipulation approach:
```python
# tests/test_knowledge_memory.py
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
```

## Verification

### Test 1: Check Package Structure
```bash
unzip -l dist/*.whl | grep "knowledge_memory/server"
# Should show files under knowledge_memory/server/, not top-level server/
```

### Test 2: Check Top-Level Packages
```bash
unzip -p dist/*.whl ioc_knowledge_memory_svc-0.1.0.dist-info/top_level.txt
# Should output: knowledge_memory
# NOT: server
```

### Test 3: Run Integration Tests
```bash
pytest tests/test_knowledge_memory.py -v
# All 16 tests should pass
```

## Benefits

✅ **No namespace collision**: User's `server` module and our `knowledge_memory.server` coexist peacefully
✅ **Clean public API**: Users only import `from knowledge_memory import ...`
✅ **Development-friendly**: Developers can work in `src/` with path manipulation
✅ **Production-ready**: Installed package uses proper namespacing

## Summary

| Scenario | Import Path | Result |
|----------|-------------|--------|
| Installed wheel | `from knowledge_memory.server.*` | ✅ Works |
| Development (src/ in path) | Falls back to `from server.*` | ✅ Works |
| User has own `server/` | `knowledge_memory.server` vs user's `server` | ✅ No conflict |

The package is ready for Artifactory publishing! 🚀
