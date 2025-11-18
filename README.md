# ci-tkf-data-logic-svc

TKF Data Logic Service - Platform Demo for Workspace, User, and API Key Management

## Prerequisites

- Python 3.11+
- Poetry installed
- Task runner: [Installation instructions](https://taskfile.dev/installation/)

## Quick Start

1. **Install dependencies:**

   ```bash
   poetry install
   # OR
   task install
   ```

2. **Start development server:**

   ```bash
   task dev
   ```

3. **Visit API documentation:** http://localhost:8000/docs

## Running the Application

### Method 1: Using Task:

```bash
task dev

# See all available tasks
task --list
```

### Method 2: Using Poetry directly

```bash
# Development server
cd src && poetry run uvicorn server.main:app --host 0.0.0.0 --port 8000 --reload

# Production server
cd src/server && poetry run python main.py
```

### Method 3: Using Docker

```bash
# Build and run with docker-compose
docker-compose up --build
```

## Available Tasks

- `task install` - Install dependencies using Poetry
- `task dev` - Start dev server with hot reload
- `task test` - Run unit tests
- `task lint` - Format and lint code
- `task docker-build` - Build Docker image
- `task docker-compose-up` - Start with docker-compose

## API Endpoints

- **API Documentation:** `GET /docs`
- **Workspaces:** `GET|POST /api/workspaces`
- **Users:** `GET|POST /api/workspaces/{workspace_id}/users`
- **API Keys:** `GET|POST /api/workspaces/{workspace_id}/users/{user_id}/api-keys`

### Project Structure

```
src/
└── server/
    ├── main.py              # Main application entry point
    ├── common.py            # Shared constants and configuration
    ├── health_check.py      # Health check functionality
    ├── mock_services.py     # Mock services for testing
    ├── test.py              # Test cases
    ├── api/                 # API layer
    │   ├── api.py          # Router aggregation
    │   └── endpoints/      # Individual endpoint modules
    │       ├── workspaces.py
    │       ├── users.py
    │       └── api_keys.py
    ├── models/             # Data models
    ├── schemas/            # Pydantic validation schemas
    ├── services/           # Business logic
    ├── storage/            # Data persistence layer
    └── utils/              # Helper functions
```

### Testing

```bash
task test
task test-all
```

### Code Quality

```bash
task lint          # Format and lint code
task lint-check    # Check formatting without changes
```
