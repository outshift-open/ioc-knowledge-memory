"""
Tests for Knowledge Graph endpoints.
"""

from unittest.mock import patch

from fastapi import FastAPI
from fastapi import status
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from server.api.endpoints.knowledge_graph import router, internal_router
from server.api.endpoints.knowledge_graph import validation_exception_handler
from server.schemas.knowledge_graph import (
    KnowledgeGraphStoreResponse,
    KnowledgeGraphDeleteResponse,
    KnowledgeGraphQueryResponse,
)

# Create a test FastAPI app
app = FastAPI()
app.include_router(router, prefix="/knowledge/graph")
app.include_router(internal_router, prefix="/internal/knowledge/graph")

# Add the knowledge graph specific validation exception handler
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Test client
test_client = TestClient(app)

# Test data
TEST_STORE_REQUEST = {
    "request_id": "test-request-id",
    "mas_id": "test-mas",
    "wksp_id": "test-wksp",
    "memory_type": "Semantic",
    "force_replace": False,
    "records": {
        "concepts": [
            {
                "id": "c1",
                "name": "Test Concept",
                "description": "A test concept for unit testing",
                "tags": ["test", "concept"],
                "attributes": {"category": "test", "importance": "high"},
                "embeddings": {"name": "text-embedding-ada-002", "data": [0.1, 0.2, 0.3, -0.1, 0.5]},
            },
            {"id": "n1", "name": "Node 1"},
            {"id": "n2", "name": "Node 2"},
        ],
        "relations": [
            {
                "id": "r1",
                "relation": "RELATED_TO",
                "node_ids": ["n1", "n2"],
                "attributes": {"strength": 0.8, "type": "semantic"},
            }
        ],
    },
}

TEST_DELETE_REQUEST = {
    "request_id": "test-request-id",
    "mas_id": "test-mas",
    "wksp_id": "test-wksp",
    "records": {"concepts": [{"id": "c1"}]},
}

TEST_QUERY_REQUEST = {
    "request_id": "test-request-id",
    "mas_id": "test-mas",
    "wksp_id": "test-wksp",
    "query_criteria": {"query_type": "neighbour"},
    "records": {"concepts": [{"id": "c1"}]},
}


class TestKnowledgeGraphEndpoints:
    """Test suite for Knowledge Graph API endpoints."""

    @patch("server.api.endpoints.knowledge_graph.knowledge_graph_service.create_graph_store")
    def test_create_graph_store_success(self, mock_create):
        """Test successful creation of knowledge graph store."""
        # Setup mock
        mock_response = KnowledgeGraphStoreResponse(
            request_id="test-request-id", status="success", message="Successfully created knowledge graph store"
        )
        mock_create.return_value = mock_response

        # Make request
        response = test_client.post(
            "/knowledge/graph/", json=TEST_STORE_REQUEST, headers={"Content-Type": "application/json"}
        )

        # Assertions
        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["request_id"] == "test-request-id"
        assert response.json()["status"] == "success"

    @patch("server.api.endpoints.knowledge_graph.knowledge_graph_service.create_graph_store")
    def test_create_graph_store_failure(self, mock_create):
        """Test failure case for knowledge graph store creation."""
        # Setup mock
        mock_response = KnowledgeGraphStoreResponse(
            request_id="test-request-id", status="failure", message="Failed to save knowledge graph store data"
        )
        mock_create.return_value = mock_response

        # Make request
        response = test_client.post(
            "/knowledge/graph/", json=TEST_STORE_REQUEST, headers={"Content-Type": "application/json"}
        )

        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["request_id"] == "test-request-id"
        assert response.json()["status"] == "failure"

    @patch("server.api.endpoints.knowledge_graph.knowledge_graph_service.delete_graph_store")
    def test_delete_graph_store_success(self, mock_delete):
        """Test successful deletion of knowledge graph store."""
        # Setup mock
        mock_response = KnowledgeGraphDeleteResponse(
            request_id="test-request-id", status="success", message="Successfully deleted knowledge graph store"
        )
        mock_delete.return_value = mock_response

        # Make request with proper JSON format
        response = test_client.request(
            "DELETE", "/knowledge/graph/", json=TEST_DELETE_REQUEST, headers={"Content-Type": "application/json"}
        )

        # Assertions
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["request_id"] == "test-request-id"
        assert response.json()["status"] == "success"

    @patch("server.api.endpoints.knowledge_graph.knowledge_graph_service.delete_graph_store")
    def test_delete_graph_store_failure(self, mock_delete):
        """Test failure case for knowledge graph store deletion."""
        # Setup mock
        mock_response = KnowledgeGraphDeleteResponse(
            request_id="test-request-id", status="failure", message="Failed to delete knowledge graph store data"
        )
        mock_delete.return_value = mock_response

        # Make request with proper JSON format
        response = test_client.request(
            "DELETE", "/knowledge/graph/", json=TEST_DELETE_REQUEST, headers={"Content-Type": "application/json"}
        )

        # Assertions
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["request_id"] == "test-request-id"
        assert response.json()["status"] == "failure"

    @patch("server.api.endpoints.knowledge_graph.knowledge_graph_service.query_graph_store")
    def test_query_graph_store_success(self, mock_query):
        """Test successful query of knowledge graph store."""
        # Setup mock
        mock_response = KnowledgeGraphQueryResponse(
            request_id="test-request-id",
            status="success",
            message="Successfully queried knowledge graph store",
            records=[],
        )
        mock_query.return_value = mock_response

        # Make request
        response = test_client.post("/knowledge/graph/query", json=TEST_QUERY_REQUEST)

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"
        assert response.json()["message"] == "Successfully queried knowledge graph store"
        assert response.json()["request_id"] == "test-request-id"

    @patch("server.api.endpoints.knowledge_graph.knowledge_graph_service.query_graph_store")
    def test_query_graph_store_minimal_request(self, mock_query):
        """Test query with minimal required fields."""
        # Setup mock response
        mock_response = KnowledgeGraphQueryResponse(
            request_id="test-request-id",
            status="success",
            message="Successfully queried knowledge graph store",
            records=[],
        )
        mock_query.return_value = mock_response

        # Minimal test query data
        test_query = {"mas_id": "123e4567-e89b-12d3-a456-426614174000", "records": {"concepts": [{"id": "c1"}]}}

        # Make request
        response = test_client.post("/knowledge/graph/query", json=test_query)

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"

    @patch("server.api.endpoints.knowledge_graph.knowledge_graph_service.query_graph_store")
    def test_query_graph_store_path_query(self, mock_query):
        """Test path query with exactly 2 concepts."""
        # Setup mock response
        mock_response = KnowledgeGraphQueryResponse(
            request_id="test-request-id", status="success", message="Successfully executed path query", records=[]
        )
        mock_query.return_value = mock_response

        # Path query test data
        path_query = {
            "request_id": "test-request-id",
            "mas_id": "test-mas",
            "query_criteria": {"query_type": "path", "depth": 2},
            "records": {"concepts": [{"id": "c1"}, {"id": "c2"}]},
        }

        # Make request
        response = test_client.post("/knowledge/graph/query", json=path_query)

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"

    @patch("server.api.endpoints.knowledge_graph.knowledge_graph_service.query_graph_store")
    def test_query_graph_store_with_query_criteria(self, mock_query):
        """Test query with custom query criteria."""
        # Setup mock response
        mock_response = KnowledgeGraphQueryResponse(
            request_id="test-request-id",
            status="success",
            message="Successfully queried knowledge graph store",
            records=[],
        )
        mock_query.return_value = mock_response

        # Test query data with query criteria
        test_query = {
            "request_id": "test-request-id",
            "mas_id": "test-mas",
            "records": {"concepts": [{"id": "c1"}]},
            "query_criteria": {"depth": 2, "limit": 10, "query_type": "neighbour"},
        }

        # Make request
        response = test_client.post("/knowledge/graph/query", json=test_query)

        # Verify response
        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"

    def test_create_graph_store_missing_mas_and_wksp_id(self):
        """Test validation error when both mas_id and wksp_id are missing."""
        # Invalid request (missing both mas_id and wksp_id)
        invalid_request = {"memory_type": "Semantic", "records": {"concepts": [{"id": "c1", "name": "Test Concept"}]}}

        # Make request
        response = test_client.post(
            "/knowledge/graph/", json=invalid_request, headers={"Content-Type": "application/json"}
        )

        # Assertions - This should trigger the custom validation
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data["status"] == "validation error"
        assert "Either 'mas_id' or 'wksp_id' or both must be provided" in response_data["message"]

    def test_delete_graph_store_validation_error(self):
        """Test validation error for knowledge graph store deletion."""
        # Invalid request (missing required fields)
        invalid_request = {}  # Missing records

        # Make request with proper JSON format
        response = test_client.request(
            "DELETE", "/knowledge/graph/", json=invalid_request, headers={"Content-Type": "application/json"}
        )

        # Assertions
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_query_graph_store_validation_error(self):
        """Test validation error for invalid query request."""
        # Invalid query (missing required 'records' field)
        test_query = {"mas_id": "test-mas"}

        # Make request
        response = test_client.post("/knowledge/graph/query", json=test_query)

        # Verify response
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_query_graph_store_neighbor_wrong_concept_count(self):
        """Test neighbor query with wrong number of concepts."""
        # Invalid query (neighbor query with 2 concepts instead of 1)
        invalid_query = {
            "request_id": "test-request-id",
            "mas_id": "test-mas",
            "query_criteria": {"query_type": "neighbour", "depth": 1},
            "records": {"concepts": [{"id": "c1"}, {"id": "c2"}]},
        }

        # Make request
        response = test_client.post("/knowledge/graph/query", json=invalid_query)

        # Assertions - This should trigger the concept count validation
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data["status"] == "validation error"
        assert "Neighbor queries require exactly 1 concept" in response_data["message"]

    def test_query_graph_store_path_wrong_concept_count(self):
        """Test path query with wrong number of concepts."""
        # Invalid query (path query with 1 concept instead of 2)
        invalid_query = {
            "request_id": "test-request-id",
            "mas_id": "test-mas",
            "query_criteria": {"query_type": "path", "depth": 2},
            "records": {"concepts": [{"id": "c1"}]},
        }

        # Make request
        response = test_client.post("/knowledge/graph/query", json=invalid_query)

        # Assertions - This should trigger the concept count validation
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        response_data = response.json()
        assert response_data["status"] == "validation error"
        assert "Path queries require exactly 2 concepts" in response_data["message"]
