import pytest
import json
from unittest.mock import AsyncMock, patch
from fastapi import status
from fastapi.testclient import TestClient
from server.api.endpoints.tkf import router
from server.schemas.tkf import (
    TkfStoreResponse,
    TkfDeleteResponse,
    TkfQueryResponse,
)
from fastapi import FastAPI

# Create a test FastAPI app
app = FastAPI()
app.include_router(router)

# Test client
test_client = TestClient(app)

# Test data
TEST_STORE_REQUEST = {
    "mas_id": "test-mas",
    "wksp_id": "test-wksp",
    "memory_type": "Semantic",
    "records": {
        "concepts": [
            {"id": "c1", "name": "Test Concept"},
            {"id": "n1", "name": "Node 1"},
            {"id": "n2", "name": "Node 2"},
        ],
        "relations": [{"id": "r1", "relation": "RELATED_TO", "node_ids": ["n1", "n2"]}],
    },
}

TEST_DELETE_REQUEST = {
    "mas_id": "test-mas",
    "wksp_id": "test-wksp",
    "memory_type": "Semantic",
    "records": {"concepts": ["c1"]},
}


@pytest.mark.asyncio
class TestTkfEndpoints:
    """Test suite for TKF API endpoints."""

    @pytest.mark.asyncio
    @patch("server.api.endpoints.tkf.tkf_service.create_tkf_store")
    async def test_create_tkf_store_success(self, mock_create):
        """Test successful creation of TKF store."""
        # Setup mock
        mock_response = TkfStoreResponse(
            request_id="test-request-id", status="success", message="Successfully created TKF store"
        )
        mock_create.return_value = mock_response

        # Make request
        response = test_client.post("/", json=TEST_STORE_REQUEST, headers={"Content-Type": "application/json"})

        # Assertions
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["request_id"] == "test-request-id"
        assert response.json()["status"] == "success"

    @pytest.mark.asyncio
    @patch("server.api.endpoints.tkf.tkf_service.create_tkf_store")
    async def test_create_tkf_store_failure(self, mock_create):
        """Test failure case for TKF store creation."""
        # Setup mock
        mock_response = TkfStoreResponse(
            request_id="test-request-id", status="failure", message="Failed to save TKF store data"
        )
        mock_create.return_value = mock_response

        # Make request
        response = test_client.post("/", json=TEST_STORE_REQUEST, headers={"Content-Type": "application/json"})

        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["request_id"] == "test-request-id"
        assert response.json()["status"] == "failure"

    @pytest.mark.asyncio
    @patch("server.api.endpoints.tkf.tkf_service.delete_tkf_store")
    async def test_delete_tkf_store_success(self, mock_delete):
        """Test successful deletion of TKF store."""
        # Setup mock
        mock_response = TkfDeleteResponse(
            request_id="test-request-id", status="success", message="Successfully deleted TKF store"
        )
        mock_delete.return_value = mock_response

        # Make request with proper JSON format
        response = test_client.request(
            "DELETE", "/", json=TEST_DELETE_REQUEST, headers={"Content-Type": "application/json"}
        )

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["request_id"] == "test-request-id"
        assert response.json()["status"] == "success"

    @pytest.mark.asyncio
    @patch("server.api.endpoints.tkf.tkf_service.delete_tkf_store")
    async def test_delete_tkf_store_failure(self, mock_delete):
        """Test failure case for TKF store deletion."""
        # Setup mock
        mock_response = TkfDeleteResponse(
            request_id="test-request-id", status="failure", message="Failed to delete TKF store data"
        )
        mock_delete.return_value = mock_response

        # Make request with proper JSON format
        response = test_client.request(
            "DELETE", "/", json=TEST_DELETE_REQUEST, headers={"Content-Type": "application/json"}
        )

        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["request_id"] == "test-request-id"
        assert response.json()["status"] == "failure"

    @pytest.mark.asyncio
    async def test_create_tkf_store_validation_error(self):
        """Test validation error for TKF store creation."""
        # Invalid request (missing required fields)
        invalid_request = {
            "mas_id": "test-mas",
            "wksp_id": "test-wksp",
            "memory_type": "Semantic"
            # Missing records
        }

        # Make request
        response = test_client.post("/", json=invalid_request, headers={"Content-Type": "application/json"})

        # Assertions
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_data = response.json()
        assert response_data["detail"] is not None

    @pytest.mark.asyncio
    async def test_delete_tkf_store_validation_error(self):
        """Test validation error for TKF store deletion."""
        # Invalid request (missing required fields)
        invalid_request = {}  # Missing records

        # Make request with proper JSON format
        response = test_client.request(
            "DELETE", "/", json=invalid_request, headers={"Content-Type": "application/json"}
        )

        # Assertions
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        response_data = response.json()
        assert response_data["detail"] is not None

    @pytest.mark.asyncio
    @patch("server.api.endpoints.tkf.tkf_service.query_tkf_store")
    async def test_query_tkf_store_success(self, mock_query):
        """Test successful query of TKF store."""
        # Setup mock
        mock_response = TkfQueryResponse(
            request_id="test-query-id", status="success", message="Successfully queried TKF store", records=[]
        )
        mock_query.return_value = mock_response

        # Test query data
        test_query = {
            "records": {"concepts": [{"id": "c1"}]},
            "memory_type": "semantic",
            "mas_id": "test-mas",
            "wksp_id": "test-wksp",
        }

        # Make request
        response = test_client.post("/query", json=test_query)

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"
        assert response.json()["message"] == "Successfully queried TKF store"
        assert response.json()["request_id"] == "test-query-id"
        assert "records" in response.json()

    @pytest.mark.asyncio
    @patch("server.api.endpoints.tkf.tkf_service.query_tkf_store")
    async def test_query_tkf_store_minimal_request(self, mock_query):
        """Test query with minimal required fields."""
        # Setup mock response
        mock_response = TkfQueryResponse(
            request_id="test-query-id", status="success", message="Successfully queried TKF store", records=[]
        )
        mock_query.return_value = mock_response

        # Minimal test query data
        test_query = {"records": {"concepts": [{"id": "c1"}]}}

        # Make request
        response = test_client.post("/query", json=test_query)

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"

    @pytest.mark.asyncio
    @patch("server.api.endpoints.tkf.tkf_service.query_tkf_store")
    async def test_query_tkf_store_with_query_criteria(self, mock_query):
        """Test query with custom query criteria."""
        # Setup mock response
        mock_response = TkfQueryResponse(
            request_id="test-query-id", status="success", message="Successfully queried TKF store", records=[]
        )
        mock_query.return_value = mock_response

        # Test query data with query criteria
        test_query = {
            "records": {"concepts": [{"id": "c1"}]},
            "query_criteria": {"depth": 2, "limit": 10, "query_type": "neighbour"},
        }

        # Make request
        response = test_client.post("/query", json=test_query)

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"

    @pytest.mark.asyncio
    async def test_query_tkf_store_validation_error(self):
        """Test validation error for invalid query request."""
        # Invalid query (missing required 'records' field)
        test_query = {"memory_type": "semantic"}

        # Make request
        response = test_client.post("/query", json=test_query)

        # Verify response
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert "field required" in str(response.json()["detail"][0]["msg"]).lower()
