# ioc-knowledge-memory-svc

ioc-knowledge-memory-svc - APIs for knowledge management

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
http://localhost:8001/docs
http://localhost:8001/openapi.json

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