# ioc-knowledge-memory-svc

ioc-knowledge-memory-svc - APIs for knowledge management

## Usage Options

This service can be accessed in two ways:

1. **HTTP API** (for external clients, microservices) - Port 9003
2. **Direct Library** (for Python in-process, 10x faster) - See [knowledge_memory](src/knowledge_memory/README.md)

## Prerequisites

- Python 3.8+
- Poetry: `curl -sSL https://install.python-poetry.org | python3 -`
- Task:
  - **macOS**: `brew install go-task`
  - **Linux**: `apt install task`, `dnf install go-task`, or `snap install task --classic`
  - **Cross-platform**: `npm install -g @go-task/cli`
  - **Go users**: `go install github.com/go-task/task/v3/cmd/task@latest`
  - **Manual install**: `sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b ~/.local/bin`
  - **All-in-one setup**: `./install.sh` (installs Poetry and Task globally, and dependencies)

## Quick Start

### Deployment Options

```bash
task docker-compose-up       # Start complete stack (application + databases)
```

### Alternative Quick Start Methods

**Dev setup (installs Poetry and Task globally)**

```bash
./install.sh
task dev
```

**Manual setup (if you have Poetry/Task already)**

```bash
poetry install
task dev
```

**API Documentation:**
http://localhost:9003/docs
http://localhost:9003/openapi.json

## Development

**Using Task**

```bash
task dev              # Start development server
task test             # Run all tests
task docker-build     # Build Docker image
task docker-run       # Run Docker container
```

**Using Poetry directly**

```bash
cd src/server
poetry run python main.py
```

**Using Docker**

```bash
docker-compose up --build
```

## Python Library (New!)

For **in-process, high-performance access** without HTTP overhead:

```python
from knowledge_memory import upsert_knowledge_graph, query_knowledge_graph
from knowledge_memory import onboard_vector_store, upsert_vector_store

# Direct function calls - no HTTP!
response = upsert_knowledge_graph(
    mas_id="agent-1",
    wksp_id="workspace-1",
    concepts=[{"id": "c1", "name": "Python"}]
)
```

**Benefits:**
- 🚀 **10x faster** than HTTP API (no network overhead)
- 🐍 **Type-safe** Python exceptions
- 🔧 **Same features** as HTTP API
- ✅ **No regression** - HTTP API still works

**Documentation:** See [src/knowledge_memory/README.md](src/knowledge_memory/README.md)

**Quick test:**
```bash
python src/knowledge_memory/examples.py     # Run examples
pytest tests/test_knowledge_memory.py -v    # Run tests
python3 validate_knowledge_memory.py        # Validate structure
```