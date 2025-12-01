"""
Shared pytest fixtures and configuration for ci-tkf-data-logic-svc tests.
"""
import pytest
from fastapi.testclient import TestClient

from server.main import app
from server.storage.memory import storage


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture(autouse=True)
def clean_storage():
    """Clean the in-memory storage before each test."""
    storage._workspaces.clear()
    storage._users.clear()
    storage._api_keys.clear()
    yield
    storage._workspaces.clear()
    storage._users.clear()
    storage._api_keys.clear()


@pytest.fixture
def sample_workspace_data():
    """Sample workspace data for testing."""
    return {"name": "Test Workspace"}


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {"name": "John Doe", "email": "john.doe@example.com"}


@pytest.fixture
def created_workspace(client, sample_workspace_data):
    """Create a workspace and return its ID."""
    response = client.post("/api/workspaces", json=sample_workspace_data)
    assert response.status_code == 201
    return response.json()["id"]


@pytest.fixture
def created_user(client, created_workspace, sample_user_data):
    """Create a user in a workspace and return user ID."""
    response = client.post(f"/api/workspaces/{created_workspace}/users", json=sample_user_data)
    assert response.status_code == 201
    return response.json()["id"]
