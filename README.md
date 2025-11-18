# ci-tkf-data-logic-svc

TKF Data Logic Service - FastAPI workspace, user, and API key management

## Prerequisites

- Python 3.8+
- Poetry: `curl -sSL https://install.python-poetry.org | python3 -`
- Task: `brew install go-task` (macOS) or [install guide](https://taskfile.dev/installation/)

## Quick Start

```bash
poetry install
task dev
```

**API Documentation:** http://localhost:8000/docs

## Development

**Option 1: Using Task**

```bash
task dev              # Start development server
task test             # Run tests
```

**Option 2: Using Poetry directly**

```bash
cd src/server
poetry run python main.py
```

**Option 3: Using Docker**

```bash
docker-compose up -build
```

## API Endpoints

- **Workspaces:** `GET|POST|PUT|DELETE /api/workspaces`
- **Users:** `GET|POST|DELETE /api/workspaces/{workspace_id}/users`
- **API Keys:** `GET|POST|DELETE /api/workspaces/{workspace_id}/api-keys`
