"""
Tests for API key endpoints in ci-tkf-data-logic-svc.
"""
import pytest


class TestApiKeyEndpoints:
    """Test cases for API key management endpoints."""

    def test_create_api_key_success(self, client, created_workspace):
        """Test successful API key creation for a workspace."""
        response = client.post(f"/api/workspaces/{created_workspace}/api-keys")

        assert response.status_code == 201
        data = response.json()
        assert "key" in data
        assert isinstance(data["key"], str)
        assert data["key"].startswith("tkf_")

    def test_create_api_key_workspace_not_found(self, client):
        """Test creating API key with non-existent workspace."""
        fake_workspace_id = "00000000-0000-0000-0000-000000000000"
        response = client.post(f"/api/workspaces/{fake_workspace_id}/api-keys")

        assert response.status_code == 404

    def test_create_api_key_invalid_workspace_id(self, client):
        """Test creating API key with invalid workspace ID format."""
        response = client.post("/api/workspaces/invalid-id/api-keys")
        assert response.status_code in [400, 422]

    def test_create_api_key_multiple_success(self, client, created_workspace):
        """Test creating multiple API keys for the same workspace."""
        response1 = client.post(f"/api/workspaces/{created_workspace}/api-keys")
        assert response1.status_code == 201
        key1 = response1.json()["key"]

        response2 = client.post(f"/api/workspaces/{created_workspace}/api-keys")
        assert response2.status_code == 201
        key2 = response2.json()["key"]

        assert key1 != key2
        assert key1.startswith("tkf_")
        assert key2.startswith("tkf_")

    def test_list_api_keys_empty(self, client, created_workspace):
        """Test listing API keys when none exist for workspace."""
        response = client.get(f"/api/workspaces/{created_workspace}/api-keys")

        assert response.status_code == 200
        data = response.json()
        assert "api_keys" in data
        assert "total" in data
        assert isinstance(data["api_keys"], list)
        assert len(data["api_keys"]) == 0
        assert data["total"] == 0

    def test_list_api_keys_workspace_not_found(self, client):
        """Test listing API keys with non-existent workspace."""
        fake_workspace_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/workspaces/{fake_workspace_id}/api-keys")

        assert response.status_code == 404

    def test_list_api_keys_with_data(self, client, created_workspace):
        """Test listing API keys after creating some."""
        # Create an API key
        create_response = client.post(f"/api/workspaces/{created_workspace}/api-keys")
        assert create_response.status_code == 201

        list_response = client.get(f"/api/workspaces/{created_workspace}/api-keys")
        assert list_response.status_code == 200

        data = list_response.json()
        assert "api_keys" in data
        assert "total" in data
        assert len(data["api_keys"]) == 1
        assert data["total"] == 1

        api_key = data["api_keys"][0]
        assert "id" in api_key
        assert "key_preview" in api_key
        assert "created_at" in api_key
        assert api_key["key_preview"].startswith("tkf_")
        assert "..." in api_key["key_preview"]

    def test_list_api_keys_multiple(self, client, created_workspace):
        """Test listing multiple API keys for a workspace."""
        for i in range(3):
            response = client.post(f"/api/workspaces/{created_workspace}/api-keys")
            assert response.status_code == 201

        response = client.get(f"/api/workspaces/{created_workspace}/api-keys")
        assert response.status_code == 200

        data = response.json()
        assert "api_keys" in data
        assert "total" in data
        assert len(data["api_keys"]) == 3
        assert data["total"] == 3

        for api_key in data["api_keys"]:
            assert "id" in api_key
            assert "key_preview" in api_key
            assert "created_at" in api_key

    def test_api_key_isolation_between_workspaces(self, client, sample_workspace_data):
        """Test that API keys are isolated between different workspaces."""
        workspace1_response = client.post("/api/workspaces", json={**sample_workspace_data, "name": "Workspace 1"})
        workspace1_id = workspace1_response.json()["id"]

        workspace2_response = client.post("/api/workspaces", json={**sample_workspace_data, "name": "Workspace 2"})
        workspace2_id = workspace2_response.json()["id"]

        client.post(f"/api/workspaces/{workspace1_id}/api-keys")

        response = client.get(f"/api/workspaces/{workspace2_id}/api-keys")
        assert response.status_code == 200
        data = response.json()
        assert len(data["api_keys"]) == 0

        response = client.get(f"/api/workspaces/{workspace1_id}/api-keys")
        assert response.status_code == 200
        data = response.json()
        assert len(data["api_keys"]) == 1
