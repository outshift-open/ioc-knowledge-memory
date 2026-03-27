# Knowledge Memory - Python Library

Direct, in-process access to knowledge memory operations without HTTP overhead.

## Installation

```python
import sys
sys.path.insert(0, '/path/to/ioc-knowledge-memory-svc/src')

from knowledge_memory import upsert_knowledge_graph, query_knowledge_graph
from knowledge_memory import onboard_vector_store, upsert_vector_store
```

## Quick Start

### Knowledge Graph

```python
from knowledge_memory import upsert_knowledge_graph, query_knowledge_graph

# Create concepts and relations
response = upsert_knowledge_graph(
    mas_id="agent-1",
    wksp_id="workspace-1",
    memory_type="Semantic",
    concepts=[
        {"id": "python", "name": "Python", "description": "Programming language"},
        {"id": "fastapi", "name": "FastAPI", "description": "Web framework"}
    ],
    relations=[
        {"id": "r1", "relation": "BUILT_WITH", "node_ids": ["fastapi", "python"]}
    ]
)

# Query neighbors
response = query_knowledge_graph(
    mas_id="agent-1",
    wksp_id="workspace-1",
    concepts=[{"id": "python"}],
    query_type="neighbour"
)

# Query path between concepts
response = query_knowledge_graph(
    mas_id="agent-1",
    wksp_id="workspace-1",
    concepts=[{"id": "python"}, {"id": "fastapi"}],
    query_type="path",
    depth=5
)
```

### Knowledge Vector

```python
from knowledge_memory import (
    onboard_vector_store,
    upsert_vector_store,
    query_vector_store
)

# 1. Onboard store (one-time setup)
onboard_vector_store(store_id="workspace-1")

# 2. Upsert vectors (384 dimensions)
upsert_vector_store(
    wksp_id="workspace-1",
    mas_id="agent-1",
    records=[
        {
            "id": "doc1",
            "content": "Python is a programming language",
            "embedding": {"data": [0.1, 0.2, ..., 0.384]}
        }
    ]
)

# 3. Query by ID
response = query_vector_store(
    wksp_id="workspace-1",
    mas_id="agent-1",
    query_type="get_by_id",
    vector_id="doc1"
)

# 4. Similarity search (cosine)
response = query_vector_store(
    wksp_id="workspace-1",
    mas_id="agent-1",
    query_type="distance_cosine",
    embedding=[0.15, 0.25, ..., 0.384],
    limit=5
)

# 5. List all vectors
response = query_vector_store(
    wksp_id="workspace-1",
    mas_id="agent-1",
    query_type="list_by_wksp_id",
    limit=10
)
```

## Error Handling

```python
from knowledge_memory import upsert_knowledge_graph
from knowledge_memory import ValidationError, NotFoundError, OperationFailedError

try:
    response = upsert_knowledge_graph(...)
except ValidationError as e:
    # Invalid request (e.g., missing required fields)
    print(f"Validation error: {e}")
except NotFoundError as e:
    # Resource not found (e.g., workspace doesn't exist)
    print(f"Not found: {e}")
except OperationFailedError as e:
    # Operation failed (e.g., database error)
    print(f"Operation failed: {e}")
```

## Examples

Run the examples file to see all operations in action:

```bash
# Ensure database is running
task docker-compose-up

# Run examples
python src/knowledge_memory/examples.py
```

## API Reference

See inline documentation or run:
```python
from knowledge_memory import upsert_knowledge_graph
help(upsert_knowledge_graph)
```

## Configuration

```bash
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export POSTGRES_USER=postgres
export POSTGRES_PASSWORD=password
export POSTGRES_DB=knowledge_db
export EMBEDDING_VECTOR_SIZE=384  # Optional, default: 384
```

## Performance

Library is **~10x faster** than HTTP API (no network overhead).

## When to Use

**Use Library:** Same Python process, maximum performance  
**Use HTTP API:** External clients, non-Python services

## Testing

### Prerequisites

```bash
# 1. Install dependencies
poetry install

# 2. Start database
task docker-compose-up
```

### Run Tests

```bash
# Run all tests
pytest tests/test_knowledge_memory.py -v

# Run specific test
pytest tests/test_knowledge_memory.py::test_graph_create_concepts -v

# Run with output
pytest tests/test_knowledge_memory.py -v -s

# Run graph tests only
pytest tests/test_knowledge_memory.py -k "graph" -v

# Run vector tests only
pytest tests/test_knowledge_memory.py -k "vector" -v
```

### Test Coverage

```bash
# Run with coverage report
pytest tests/test_knowledge_memory.py --cov=knowledge_memory --cov-report=html

# View coverage
open htmlcov/index.html
```

### What's Tested

- ✅ Knowledge graph CRUD operations
- ✅ Knowledge vector CRUD operations
- ✅ Query operations (concept, neighbor, path, similarity)
- ✅ Exception handling (ValidationError, NotFoundError)
- ✅ Import structure
- ✅ Type safety

### Quick Validation

```bash
# Validate library structure (no database needed)
python3 validate_knowledge_memory.py
```
