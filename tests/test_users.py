"""
Tests for user endpoints in ci-tkf-data-logic-svc.
"""
import pytest


class TestUserEndpoints:
    """Test cases for user management endpoints."""

    def test_create_user_success(self, client, created_workspace, sample_user_data):
        """Test successful user creation in a workspace."""
        response = client.post(f"/api/workspaces/{created_workspace}/users", json=sample_user_data)

        assert response.status_code == 201
        data = response.json()
        assert "id" in data
        assert isinstance(data["id"], str)
        import uuid

        uuid.UUID(data["id"])

    def test_create_user_workspace_not_found(self, client, sample_user_data):
        """Test creating user in non-existent workspace."""
        fake_workspace_id = "00000000-0000-0000-0000-000000000000"
        response = client.post(f"/api/workspaces/{fake_workspace_id}/users", json=sample_user_data)

        assert response.status_code == 404

    def test_create_user_invalid_workspace_id(self, client, sample_user_data):
        """Test creating user with invalid workspace ID format."""
        response = client.post("/api/workspaces/invalid-id/users", json=sample_user_data)

        assert response.status_code in [400, 404, 422]

    def test_create_user_invalid_data(self, client, created_workspace):
        """Test user creation with invalid data."""
        response = client.post(f"/api/workspaces/{created_workspace}/users", json={})
        assert response.status_code == 422

        response = client.post(f"/api/workspaces/{created_workspace}/users", json={"name": "John Doe"})
        assert response.status_code == 422

        response = client.post(f"/api/workspaces/{created_workspace}/users", json={"email": "john@example.com"})
        assert response.status_code == 422

        response = client.post(
            f"/api/workspaces/{created_workspace}/users", json={"name": "John Doe", "email": "invalid-email"}
        )
        assert response.status_code == 422

    def test_create_user_empty_fields(self, client, created_workspace):
        """Test user creation with empty fields."""
        response = client.post(
            f"/api/workspaces/{created_workspace}/users", json={"name": "", "email": "john@example.com"}
        )
        assert response.status_code == 422

        response = client.post(f"/api/workspaces/{created_workspace}/users", json={"name": "John Doe", "email": ""})
        assert response.status_code == 422

    def test_list_users_empty(self, client, created_workspace):
        """Test listing users when none exist in workspace."""
        response = client.get(f"/api/workspaces/{created_workspace}/users")

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_list_users_workspace_not_found(self, client):
        """Test listing users in non-existent workspace."""
        fake_workspace_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/workspaces/{fake_workspace_id}/users")

        assert response.status_code == 404

    def test_list_users_with_data(self, client, created_workspace, sample_user_data):
        """Test listing users after creating some."""
        create_response = client.post(f"/api/workspaces/{created_workspace}/users", json=sample_user_data)
        assert create_response.status_code == 201
        user_id = create_response.json()["id"]

        list_response = client.get(f"/api/workspaces/{created_workspace}/users")
        assert list_response.status_code == 200

        data = list_response.json()
        assert len(data) == 1

        user = data[0]
        assert user["id"] == user_id
        assert user["name"] == sample_user_data["name"]
        assert user["email"] == sample_user_data["email"]
        assert user["workspace_id"] == created_workspace
        assert "created_at" in user

    def test_list_users_multiple(self, client, created_workspace):
        """Test listing multiple users in a workspace."""
        users_data = [
            {"name": "John Doe", "email": "john@example.com"},
            {"name": "Jane Smith", "email": "jane@example.com"},
            {"name": "Bob Johnson", "email": "bob@example.com"},
        ]

        created_ids = []
        for user_data in users_data:
            response = client.post(f"/api/workspaces/{created_workspace}/users", json=user_data)
            assert response.status_code == 201
            created_ids.append(response.json()["id"])

        response = client.get(f"/api/workspaces/{created_workspace}/users")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 3

        returned_ids = [user["id"] for user in data]
        for created_id in created_ids:
            assert created_id in returned_ids

    def test_get_user_by_id(self, client, created_workspace, created_user, sample_user_data):
        """Test getting a specific user by ID."""
        response = client.get(f"/api/workspaces/{created_workspace}/users/{created_user}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == created_user
        assert data["name"] == sample_user_data["name"]
        assert data["email"] == sample_user_data["email"]
        assert data["workspace_id"] == created_workspace
        assert "created_at" in data

    def test_get_user_not_found(self, client, created_workspace):
        """Test getting a user that doesn't exist."""
        fake_user_id = "00000000-0000-0000-0000-000000000000"
        response = client.get(f"/api/workspaces/{created_workspace}/users/{fake_user_id}")

        assert response.status_code == 404

    def test_get_user_wrong_workspace(self, client, created_user, sample_workspace_data):
        """Test getting a user from wrong workspace."""
        ws_response = client.post("/api/workspaces", json=sample_workspace_data)
        other_workspace = ws_response.json()["id"]

        response = client.get(f"/api/workspaces/{other_workspace}/users/{created_user}")

        assert response.status_code == 404
