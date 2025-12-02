"""
Tests for workspace endpoints in ci-tkf-data-logic-svc.
"""
import pytest


class TestWorkspaceEndpoints:
    """Test cases for workspace management endpoints."""

    def test_create_workspace_success(self, client, sample_workspace_data):
        """Test successful workspace creation."""
        response = client.post("/api/workspaces", json=sample_workspace_data)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert isinstance(data["id"], str)
        import uuid

        uuid.UUID(data["id"])

    def test_create_workspace_invalid_data(self, client):
        """Test workspace creation with invalid data."""
        response = client.post("/api/workspaces", json={})
        assert response.status_code == 422

        response = client.post("/api/workspaces", json={"name": ""})
        assert response.status_code == 422

    def test_create_workspace_invalid_json(self, client):
        """Test workspace creation with invalid JSON."""
        response = client.post("/api/workspaces", content="invalid json", headers={"Content-Type": "application/json"})
        assert response.status_code == 422

    def test_list_workspaces_empty(self, client):
        """Test listing workspaces when none exist."""
        response = client.get("/api/workspaces")

        assert response.status_code == 200
        data = response.json()
        assert "workspaces" in data
        assert data["workspaces"] == []

    def test_list_workspaces_with_data(self, client, sample_workspace_data):
        """Test listing workspaces after creating some."""
        create_response = client.post("/api/workspaces", json=sample_workspace_data)
        assert create_response.status_code == 201
        workspace_id = create_response.json()["id"]

        list_response = client.get("/api/workspaces")
        assert list_response.status_code == 200

        data = list_response.json()
        assert "workspaces" in data
        assert len(data["workspaces"]) == 1

        workspace = data["workspaces"][0]
        assert workspace["id"] == workspace_id
        assert workspace["name"] == sample_workspace_data["name"]
        assert "created_at" in workspace

    def test_list_workspaces_multiple(self, client):
        """Test listing multiple workspaces."""
        workspaces_data = [{"name": "Workspace 1"}, {"name": "Workspace 2"}, {"name": "Workspace 3"}]

        created_ids = []
        for ws_data in workspaces_data:
            response = client.post("/api/workspaces", json=ws_data)
            assert response.status_code == 201
            created_ids.append(response.json()["id"])

        response = client.get("/api/workspaces")
        assert response.status_code == 200

        data = response.json()
        assert len(data["workspaces"]) == 3

        returned_ids = [ws["id"] for ws in data["workspaces"]]
        for created_id in created_ids:
            assert created_id in returned_ids

    def test_get_workspace_by_id(self, client, created_workspace, sample_workspace_data):
        """Test getting a specific workspace by ID."""
        response = client.get(f"/api/workspaces/{created_workspace}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_workspace
        assert data["name"] == sample_workspace_data["name"]
        assert "created_at" in data

    def test_get_workspace_not_found(self, client):
        """Test getting a workspace that doesn't exist."""
        fake_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/workspaces/{fake_id}")

        assert response.status_code == 404

    def test_get_workspace_invalid_id(self, client):
        """Test getting a workspace with invalid ID format."""
        response = client.get("/api/workspaces/invalid-id")

        assert response.status_code == 404
