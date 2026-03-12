# Tests

Integration tests for the `knowledge_memory` library.

## Prerequisites

1. **Install dependencies:**
   ```bash
   poetry install
   ```

2. **Start database:**
   ```bash
   task docker-compose-up
   ```

## Running Tests

```bash
# Run all tests
pytest tests/test_knowledge_memory.py -v

# Run specific test
pytest tests/test_knowledge_memory.py::test_graph_create_concepts -v

# Run graph tests only
pytest tests/test_knowledge_memory.py -k "graph" -v

# Run vector tests only
pytest tests/test_knowledge_memory.py -k "vector" -v

# Run with output
pytest tests/test_knowledge_memory.py -v -s

# Run with coverage
pytest tests/test_knowledge_memory.py --cov=knowledge_memory --cov-report=html
```

## Test Structure

### `test_knowledge_memory.py`
Integration tests covering:
- **Knowledge Graph:** Create, query, delete operations
- **Knowledge Vector:** Onboard, upsert, query, delete operations
- **Error Handling:** ValidationError, NotFoundError
- **Imports:** Verify all exports work

### `conftest.py`
Pytest configuration for path setup and fixtures

## Test Fixtures

- `test_ids()` - Generates unique IDs for test isolation
- `vector_store_id()` - Generates unique vector store ID

Each test uses unique IDs to prevent interference between tests.

## What's Tested

✅ Knowledge graph CRUD operations
✅ Knowledge vector CRUD operations
✅ Query operations (concept, neighbor, path, similarity)
✅ Exception handling
✅ Import structure
✅ Type safety

## Quick Validation

Validate library structure without database:
```bash
python3 validate_knowledge_memory.py
```
