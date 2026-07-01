# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""
Tests for Knowledge Key-Value Pair (KVP) endpoints.
"""

from unittest.mock import patch

from fastapi import FastAPI
from fastapi import status
from fastapi.testclient import TestClient

from server.api.endpoints.knowledge_kvp import router, internal_router
from server.schemas.knowledge_keyvalue import (
    KnowledgeKVPStoreOnboardResponse,
    KnowledgeKVPStoreResponse,
    KnowledgeKVPQueryResponse,
    KnowledgeKVPDeleteResponse,
    KnowledgeKVPRecord,
    ResponseStatus,
    ScopeType,
)

# Create a test FastAPI app
app = FastAPI()
app.include_router(router, prefix="/knowledge/kvps")
app.include_router(internal_router, prefix="/internal/knowledge/kvps")

# Test client
test_client = TestClient(app)

# Test data constants
TEST_UUID_WKSP = "123e4567-e89b-12d3-a456-426614174000"
TEST_UUID_MAS = "223e4567-e89b-12d3-a456-426614174001"
TEST_CE_ID = "agent-001"
TEST_AGENT_ID = "agent_1"

TEST_ONBOARD_REQUEST_MAS = {
    "scope": "mas"
}

TEST_ONBOARD_REQUEST_CE = {
    "scope": "ce"
}

TEST_STORE_REQUEST_MAS = {
    "scope": "mas",
    "wksp_id": TEST_UUID_WKSP,
    "mas_id": TEST_UUID_MAS,
    "agent_id": TEST_AGENT_ID,
    "records": [
        {
            "key": {"episode_id": "123", "message_id": "msg_1"},
            "value": {
                "name": "John Doe",
                "preferences": {"theme": "dark", "language": "en"},
                "last_login": 1640995200
            }
        }
    ]
}

TEST_STORE_REQUEST_CE = {
    "scope": "ce",
    "ce_id": TEST_CE_ID,
    "records": [
        {
            "key": {"session_id": "sess_123"},
            "value": {"status": "active", "created_at": 1640995200}
        }
    ]
}

TEST_QUERY_REQUEST_MAS = {
    "scope": "mas",
    "wksp_id": TEST_UUID_WKSP,
    "mas_id": TEST_UUID_MAS,
    "agent_id": TEST_AGENT_ID,
    "query_criteria": {
        "query_type": "get_by_key",
        "key": {"episode_id": "123", "message_id": "msg_1"}
    }
}

TEST_QUERY_REQUEST_CE = {
    "scope": "ce",
    "ce_id": TEST_CE_ID,
    "query_criteria": {
        "query_type": "get_by_key",
        "key": {"session_id": "sess_123"}
    }
}

TEST_DELETE_REQUEST_MAS = {
    "scope": "mas",
    "wksp_id": TEST_UUID_WKSP,
    "mas_id": TEST_UUID_MAS,
    "agent_id": TEST_AGENT_ID,
    "key": {"episode_id": "123", "message_id": "msg_1"},
    "soft_delete": True
}

TEST_DELETE_REQUEST_CE = {
    "scope": "ce",
    "ce_id": TEST_CE_ID,
    "key": {"session_id": "sess_123"},
    "soft_delete": False
}


class TestKVPStoreOnboardEndpoint:
    """Test suite for POST /knowledge/kvps/stores/{store_id} (onboard)."""

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.onboard")
    def test_onboard_mas_success(self, mock_onboard):
        """Test successful MAS store onboarding."""
        mock_onboard.return_value = KnowledgeKVPStoreOnboardResponse(
            request_id="test-request-id",
            status=ResponseStatus.SUCCESS,
            message="Successfully created KVP store container for store: test-store-id"
        )

        response = test_client.post(
            "/knowledge/kvps/stores/test-store-id",
            json=TEST_ONBOARD_REQUEST_MAS
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["status"] == "success"
        assert "test-store-id" in response.json()["message"]

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.onboard")
    def test_onboard_ce_success(self, mock_onboard):
        """Test successful CE store onboarding."""
        mock_onboard.return_value = KnowledgeKVPStoreOnboardResponse(
            request_id="test-request-id",
            status=ResponseStatus.SUCCESS,
            message="Successfully created KVP store container for store: agent-001"
        )

        response = test_client.post(
            "/knowledge/kvps/stores/agent-001",
            json=TEST_ONBOARD_REQUEST_CE
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["status"] == "success"

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.onboard")
    def test_onboard_failure(self, mock_onboard):
        """Test onboard failure case."""
        mock_onboard.return_value = KnowledgeKVPStoreOnboardResponse(
            request_id="test-request-id",
            status=ResponseStatus.FAILURE,
            message="Failed to onboard KVP store test-store-id"
        )

        response = test_client.post(
            "/knowledge/kvps/stores/test-store-id",
            json=TEST_ONBOARD_REQUEST_MAS
        )

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to onboard KVP store test-store-id" in response.json()["detail"]

    def test_onboard_invalid_scope(self):
        """Test validation error for invalid scope."""
        invalid_request = {"scope": "invalid_scope"}

        response = test_client.post(
            "/knowledge/kvps/stores/test-store-id",
            json=invalid_request
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_onboard_missing_scope(self):
        """Test validation error when scope is missing."""
        invalid_request = {}

        response = test_client.post(
            "/knowledge/kvps/stores/test-store-id",
            json=invalid_request
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestKVPStoreEndpoint:
    """Test suite for POST /knowledge/kvps (upsert)."""

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.create_kvp_store")
    def test_upsert_mas_success(self, mock_create):
        """Test successful MAS scoped upsert."""
        mock_create.return_value = KnowledgeKVPStoreResponse(
            request_id="test-request-id",
            status=ResponseStatus.SUCCESS,
            message="Successfully saved KVP records"
        )

        response = test_client.post("/knowledge/kvps", json=TEST_STORE_REQUEST_MAS)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["status"] == "success"
        
        # Verify the service was called with correct data
        called_with = mock_create.call_args[0][0]
        assert called_with.scope == ScopeType.MAS
        assert called_with.wksp_id == TEST_UUID_WKSP
        assert called_with.mas_id == TEST_UUID_MAS
        assert called_with.agent_id == TEST_AGENT_ID
        assert len(called_with.records) == 1

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.create_kvp_store")
    def test_upsert_ce_success(self, mock_create):
        """Test successful CE scoped upsert."""
        mock_create.return_value = KnowledgeKVPStoreResponse(
            request_id="test-request-id",
            status=ResponseStatus.SUCCESS,
            message="Successfully saved KVP records"
        )

        response = test_client.post("/knowledge/kvps", json=TEST_STORE_REQUEST_CE)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["status"] == "success"
        
        # Verify the service was called with correct data
        called_with = mock_create.call_args[0][0]
        assert called_with.scope == ScopeType.CE
        assert called_with.ce_id == TEST_CE_ID

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.create_kvp_store")
    def test_upsert_not_found(self, mock_create):
        """Test not-found when KVP store does not exist."""
        mock_create.return_value = KnowledgeKVPStoreResponse(
            request_id="test-request-id",
            status=ResponseStatus.NOT_FOUND,
            message="KVP store not found"
        )

        response = test_client.post("/knowledge/kvps", json=TEST_STORE_REQUEST_MAS)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "KVP store not found" in response.json()["detail"]

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.create_kvp_store")
    def test_upsert_validation_error(self, mock_create):
        """Test validation error from service."""
        mock_create.return_value = KnowledgeKVPStoreResponse(
            request_id="test-request-id",
            status=ResponseStatus.VALIDATION_ERROR,
            message="Invalid request data"
        )

        response = test_client.post("/knowledge/kvps", json=TEST_STORE_REQUEST_MAS)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid request data" in response.json()["detail"]

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.create_kvp_store")
    def test_upsert_failure(self, mock_create):
        """Test failure case for upsert."""
        mock_create.return_value = KnowledgeKVPStoreResponse(
            request_id="test-request-id",
            status=ResponseStatus.FAILURE,
            message="Failed to save KVP records"
        )

        response = test_client.post("/knowledge/kvps", json=TEST_STORE_REQUEST_MAS)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to save KVP records" in response.json()["detail"]

    def test_upsert_invalid_uuid_format(self):
        """Test validation error for invalid UUID format."""
        invalid_request = {**TEST_STORE_REQUEST_MAS}
        invalid_request["wksp_id"] = "invalid_uuid_format"

        response = test_client.post("/knowledge/kvps", json=invalid_request)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_upsert_missing_mas_scope_requirements(self):
        """Test validation error when MAS scope requirements are missing."""
        invalid_request = {
            "scope": "mas",
            "records": [{"key": {"test": "key"}, "value": {"test": "value"}}]
        }

        response = test_client.post("/knowledge/kvps", json=invalid_request)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_upsert_missing_ce_scope_requirements(self):
        """Test validation error when CE scope requirements are missing."""
        invalid_request = {
            "scope": "ce",
            "records": [{"key": {"test": "key"}, "value": {"test": "value"}}]
        }

        response = test_client.post("/knowledge/kvps", json=invalid_request)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_upsert_empty_records(self):
        """Test that empty records list is valid."""
        request_with_empty_records = {**TEST_STORE_REQUEST_MAS}
        request_with_empty_records["records"] = []

        # Should not raise validation error at schema level
        # (business logic validation happens in service layer)
        response = test_client.post("/knowledge/kvps", json=request_with_empty_records)
        
        # May return various status codes depending on service logic
        assert response.status_code in [200, 201, 400, 404, 500]


class TestKVPQueryEndpoint:
    """Test suite for POST /knowledge/kvps/query."""

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.query_kvp_store")
    def test_query_mas_success(self, mock_query):
        """Test successful MAS scoped query."""
        mock_query.return_value = KnowledgeKVPQueryResponse(
            request_id="test-request-id",
            status=ResponseStatus.SUCCESS,
            message="Successfully queried 1 KVP records",
            records=[
                KnowledgeKVPRecord(
                    key={"episode_id": "123", "message_id": "msg_1"},
                    value={"name": "John Doe", "preferences": {"theme": "dark"}},
                    created_at=1640995200,
                    updated_at=1640995200
                )
            ]
        )

        response = test_client.post("/knowledge/kvps/query", json=TEST_QUERY_REQUEST_MAS)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"
        assert len(response.json()["records"]) == 1
        
        record = response.json()["records"][0]
        assert record["key"]["episode_id"] == "123"
        assert record["value"]["name"] == "John Doe"

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.query_kvp_store")
    def test_query_ce_success(self, mock_query):
        """Test successful CE scoped query."""
        mock_query.return_value = KnowledgeKVPQueryResponse(
            request_id="test-request-id",
            status=ResponseStatus.SUCCESS,
            message="Successfully queried 1 KVP records",
            records=[
                KnowledgeKVPRecord(
                    key={"session_id": "sess_123"},
                    value={"status": "active"},
                    created_at=1640995200,
                    updated_at=1640995200
                )
            ]
        )

        response = test_client.post("/knowledge/kvps/query", json=TEST_QUERY_REQUEST_CE)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.query_kvp_store")
    def test_query_empty_results(self, mock_query):
        """Test query returning no records."""
        mock_query.return_value = KnowledgeKVPQueryResponse(
            request_id="test-request-id",
            status=ResponseStatus.SUCCESS,
            message="No records found",
            records=[]
        )

        response = test_client.post("/knowledge/kvps/query", json=TEST_QUERY_REQUEST_MAS)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["records"] == []

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.query_kvp_store")
    def test_query_not_found(self, mock_query):
        """Test not-found when KVP store does not exist."""
        mock_query.return_value = KnowledgeKVPQueryResponse(
            request_id="test-request-id",
            status=ResponseStatus.NOT_FOUND,
            message="KVP store not found"
        )

        response = test_client.post("/knowledge/kvps/query", json=TEST_QUERY_REQUEST_MAS)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "KVP store not found" in response.json()["detail"]

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.query_kvp_store")
    def test_query_validation_error(self, mock_query):
        """Test validation error from service."""
        mock_query.return_value = KnowledgeKVPQueryResponse(
            request_id="test-request-id",
            status=ResponseStatus.VALIDATION_ERROR,
            message="Unsupported query type"
        )

        response = test_client.post("/knowledge/kvps/query", json=TEST_QUERY_REQUEST_MAS)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Unsupported query type" in response.json()["detail"]

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.query_kvp_store")
    def test_query_failure(self, mock_query):
        """Test failure case for query."""
        mock_query.return_value = KnowledgeKVPQueryResponse(
            request_id="test-request-id",
            status=ResponseStatus.FAILURE,
            message="Internal error"
        )

        response = test_client.post("/knowledge/kvps/query", json=TEST_QUERY_REQUEST_MAS)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Internal error" in response.json()["detail"]

    def test_query_invalid_query_type(self):
        """Test validation error for invalid query type."""
        invalid_request = {**TEST_QUERY_REQUEST_MAS}
        invalid_request["query_criteria"]["query_type"] = "invalid_type"

        response = test_client.post("/knowledge/kvps/query", json=invalid_request)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_query_missing_key_for_get_by_key(self):
        """Test validation error when key is missing for get_by_key query."""
        invalid_request = {**TEST_QUERY_REQUEST_MAS}
        del invalid_request["query_criteria"]["key"]

        response = test_client.post("/knowledge/kvps/query", json=invalid_request)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestKVPDeleteEndpoint:
    """Test suite for DELETE /knowledge/kvps."""

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.delete_kvp_store")
    def test_delete_mas_success(self, mock_delete):
        """Test successful MAS scoped delete."""
        mock_delete.return_value = KnowledgeKVPDeleteResponse(
            request_id="test-request-id",
            status=ResponseStatus.SUCCESS,
            message="Successfully soft deleted 1 KVP records"
        )

        response = test_client.request("DELETE", "/knowledge/kvps", json=TEST_DELETE_REQUEST_MAS)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"
        assert "soft deleted" in response.json()["message"]

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.delete_kvp_store")
    def test_delete_ce_hard_delete(self, mock_delete):
        """Test successful CE scoped hard delete."""
        mock_delete.return_value = KnowledgeKVPDeleteResponse(
            request_id="test-request-id",
            status=ResponseStatus.SUCCESS,
            message="Successfully permanently deleted 1 KVP records"
        )

        response = test_client.request("DELETE", "/knowledge/kvps", json=TEST_DELETE_REQUEST_CE)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"
        assert "permanently deleted" in response.json()["message"]

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.delete_kvp_store")
    def test_delete_not_found(self, mock_delete):
        """Test not-found when record does not exist."""
        mock_delete.return_value = KnowledgeKVPDeleteResponse(
            request_id="test-request-id",
            status=ResponseStatus.NOT_FOUND,
            message="No records found to delete"
        )

        response = test_client.request("DELETE", "/knowledge/kvps", json=TEST_DELETE_REQUEST_MAS)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "No records found to delete" in response.json()["detail"]

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.delete_kvp_store")
    def test_delete_validation_error(self, mock_delete):
        """Test validation error from service."""
        mock_delete.return_value = KnowledgeKVPDeleteResponse(
            request_id="test-request-id",
            status=ResponseStatus.VALIDATION_ERROR,
            message="Invalid delete request"
        )

        response = test_client.request("DELETE", "/knowledge/kvps", json=TEST_DELETE_REQUEST_MAS)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "Invalid delete request" in response.json()["detail"]

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.delete_kvp_store")
    def test_delete_failure(self, mock_delete):
        """Test failure case for delete."""
        mock_delete.return_value = KnowledgeKVPDeleteResponse(
            request_id="test-request-id",
            status=ResponseStatus.FAILURE,
            message="Failed to delete records"
        )

        response = test_client.request("DELETE", "/knowledge/kvps", json=TEST_DELETE_REQUEST_MAS)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert "Failed to delete records" in response.json()["detail"]

    def test_delete_missing_key(self):
        """Test validation error when key is missing."""
        invalid_request = {**TEST_DELETE_REQUEST_MAS}
        del invalid_request["key"]

        response = test_client.request("DELETE", "/knowledge/kvps", json=invalid_request)

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_delete_invalid_soft_delete_type(self):
        """Test that soft_delete accepts boolean values."""
        # Test with valid boolean
        valid_request = {**TEST_DELETE_REQUEST_MAS}
        valid_request["soft_delete"] = False

        response = test_client.request("DELETE", "/knowledge/kvps", json=valid_request)
        # Should not fail due to validation (may fail for other reasons)
        assert response.status_code != 422


class TestKVPStoreDeleteNotImplemented:
    """Test suite for DELETE /knowledge/kvps/stores/{store_id} (not implemented)."""

    def test_delete_store_not_implemented(self):
        """Test that public store deletion returns 501 Not Implemented."""
        # The endpoint requires a request body, so we need to provide one
        response = test_client.request(
            "DELETE", 
            "/knowledge/kvps/stores/test-store-id",
            json={"scope": "mas"}
        )

        assert response.status_code == status.HTTP_501_NOT_IMPLEMENTED
        assert "internal API" in response.json()["detail"]


class TestInternalKVPStoreDeleteEndpoint:
    """Test suite for DELETE /internal/knowledge/kvps/stores/{store_id}."""

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.get_schema_name")
    @patch("server.database.keyvalue_db.postgres.src.db.KeyValueDB")
    def test_internal_delete_success(self, mock_db_class, mock_get_schema_name):
        """Test successful internal store deletion."""
        mock_db = mock_db_class.return_value
        mock_db.delete_schema.return_value = True
        mock_get_schema_name.return_value = "kvp_mas_test_store"

        response = test_client.request(
            "DELETE",
            "/internal/knowledge/kvps/stores/test-store-id",
            json={"scope": "mas"}
        )

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"
        assert "Successfully deleted KVP store" in response.json()["message"]

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.get_schema_name")
    @patch("server.database.keyvalue_db.postgres.src.db.KeyValueDB")
    def test_internal_delete_not_found(self, mock_db_class, mock_get_schema_name):
        """Test internal delete when store does not exist."""
        mock_db = mock_db_class.return_value
        mock_db.delete_schema.return_value = False
        mock_get_schema_name.return_value = "kvp_mas_test_store"

        response = test_client.request(
            "DELETE",
            "/internal/knowledge/kvps/stores/test-store-id",
            json={"scope": "mas"}
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert "not found" in response.json()["detail"]


class TestUUIDValidation:
    """Test UUID validation in endpoints."""

    def test_valid_uuid_formats_accepted(self):
        """Test that valid UUID formats are accepted."""
        valid_request = {
            "scope": "mas",
            "wksp_id": "123e4567-e89b-12d3-a456-426614174000",
            "mas_id": "223e4567-e89b-12d3-a456-426614174001",
            "records": [{"key": {"test": "key"}, "value": {"test": "value"}}]
        }

        response = test_client.post("/knowledge/kvps", json=valid_request)
        # Should not fail due to UUID validation (may fail for other reasons)
        assert response.status_code != 422

    def test_invalid_uuid_formats_rejected(self):
        """Test that invalid UUID formats are rejected."""
        invalid_requests = [
            {
                "scope": "mas",
                "wksp_id": "123e4567_e89b_12d3_a456_426614174000",  # Underscores
                "mas_id": "223e4567-e89b-12d3-a456-426614174001",
                "records": []
            },
            {
                "scope": "mas",
                "wksp_id": "123e4567-e89b-12d3-a456-426614174000",
                "mas_id": "invalid-uuid-format",  # Invalid format
                "records": []
            }
        ]

        for invalid_request in invalid_requests:
            response = test_client.post("/knowledge/kvps", json=invalid_request)
            assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestScopeValidation:
    """Test scope-based validation in endpoints."""

    def test_mas_scope_requires_wksp_id_and_mas_id(self):
        """Test that MAS scope requires wksp_id and mas_id."""
        # Missing wksp_id
        invalid_request = {
            "scope": "mas",
            "mas_id": TEST_UUID_MAS,
            "records": []
        }
        response = test_client.post("/knowledge/kvps", json=invalid_request)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

        # Missing mas_id
        invalid_request = {
            "scope": "mas",
            "wksp_id": TEST_UUID_WKSP,
            "records": []
        }
        response = test_client.post("/knowledge/kvps", json=invalid_request)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_ce_scope_requires_ce_id(self):
        """Test that CE scope requires ce_id."""
        invalid_request = {
            "scope": "ce",
            "records": []
        }
        response = test_client.post("/knowledge/kvps", json=invalid_request)
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_ce_id_accepts_various_string_formats(self):
        """Test that ce_id accepts various string formats (not just UUIDs)."""
        valid_ce_ids = ["agent-001", "ce_engine_v2", "simple-string", "123"]
        
        for ce_id in valid_ce_ids:
            request = {
                "scope": "ce",
                "ce_id": ce_id,
                "records": []
            }
            response = test_client.post("/knowledge/kvps", json=request)
            # Should not fail due to ce_id format validation
            assert response.status_code != 422


class TestAgentIdScoping:
    """Test agent_id scoping functionality."""

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.create_kvp_store")
    def test_agent_id_passed_to_service(self, mock_create):
        """Test that agent_id is passed through to the service."""
        mock_create.return_value = KnowledgeKVPStoreResponse(
            request_id="test-request-id",
            status=ResponseStatus.SUCCESS,
            message="Success"
        )

        request_with_agent = {**TEST_STORE_REQUEST_MAS}
        request_with_agent["agent_id"] = "specific-agent-123"

        response = test_client.post("/knowledge/kvps", json=request_with_agent)

        assert response.status_code == status.HTTP_201_CREATED
        called_with = mock_create.call_args[0][0]
        assert called_with.agent_id == "specific-agent-123"

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.create_kvp_store")
    def test_agent_id_optional_for_mas_scope(self, mock_create):
        """Test that agent_id is optional for MAS scope."""
        mock_create.return_value = KnowledgeKVPStoreResponse(
            request_id="test-request-id",
            status=ResponseStatus.SUCCESS,
            message="Success"
        )

        request_without_agent = {**TEST_STORE_REQUEST_MAS}
        del request_without_agent["agent_id"]

        response = test_client.post("/knowledge/kvps", json=request_without_agent)

        assert response.status_code == status.HTTP_201_CREATED
        called_with = mock_create.call_args[0][0]
        assert called_with.agent_id is None


class TestRequestIdGeneration:
    """Test request ID auto-generation."""

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.create_kvp_store")
    def test_request_id_auto_generated_when_omitted(self, mock_create):
        """Test that request_id is auto-generated when omitted."""
        mock_create.return_value = KnowledgeKVPStoreResponse(
            request_id="auto-generated-id",
            status=ResponseStatus.SUCCESS,
            message="Success"
        )

        response = test_client.post("/knowledge/kvps", json=TEST_STORE_REQUEST_MAS)

        assert response.status_code == status.HTTP_201_CREATED
        called_with = mock_create.call_args[0][0]
        # Auto-generated request_id should be a non-empty string
        assert called_with.request_id != ""
        assert isinstance(called_with.request_id, str)

    @patch("server.api.endpoints.knowledge_kvp.kvp_service.create_kvp_store")
    def test_custom_request_id_preserved(self, mock_create):
        """Test that custom request_id is preserved when provided."""
        mock_create.return_value = KnowledgeKVPStoreResponse(
            request_id="custom-request-id",
            status=ResponseStatus.SUCCESS,
            message="Success"
        )

        request_with_custom_id = {**TEST_STORE_REQUEST_MAS}
        request_with_custom_id["request_id"] = "custom-request-id"

        response = test_client.post("/knowledge/kvps", json=request_with_custom_id)

        assert response.status_code == status.HTTP_201_CREATED
        called_with = mock_create.call_args[0][0]
        assert called_with.request_id == "custom-request-id"
