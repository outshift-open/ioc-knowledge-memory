# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""
Tests for Knowledge Vector endpoints.
"""

from unittest.mock import patch

from fastapi import FastAPI
from fastapi import status
from fastapi.exceptions import RequestValidationError
from fastapi.testclient import TestClient

from server.api.endpoints.knowledge_vector import router, internal_router
from server.api.endpoints.knowledge_vector import validation_exception_handler
from server.schemas.knowledge_vector import (
    KnowledgeVectorStoreResponse,
    KnowledgeVectorQueryResponse,
    KnowledgeVectorQueryResponseRecord,
    KnowledgeVectorDeleteResponse,
    KnowledgeVectorSimilaritySearchResponse,
    KnowledgeVectorSimilaritySearchResult,
    EmbeddingConfig,
    EMBEDDING_VECTOR_SIZE,
)

# Valid 384-dimension embedding for use across all tests
DUMMY_EMBEDDING = [0.1] * EMBEDDING_VECTOR_SIZE

# Create a test FastAPI app
app = FastAPI()
app.include_router(router, prefix="/knowledge/vector")
app.include_router(internal_router, prefix="/internal/knowledge/vector")

# Add the knowledge vector specific validation exception handler
app.add_exception_handler(RequestValidationError, validation_exception_handler)

# Test client
test_client = TestClient(app)

TEST_STORE_REQUEST = {
    "request_id": "test-request-id",
    "wksp_id": "test-wksp",
    "mas_id": "test-mas",
    "records": [
        {
            "id": "123e4567-e89b-12d3-a456-426614174001",
            "content": "some document text",
            "embedding": {"data": DUMMY_EMBEDDING},
        }
    ],
}

TEST_STORE_REQUEST_WITH_METADATA = {
    "request_id": "test-request-id",
    "wksp_id": "test-wksp",
    "mas_id": "test-mas",
    "records": [
        {
            "id": "123e4567-e89b-12d3-a456-426614174001",
            "content": "some document text",
            "embedding": {"data": DUMMY_EMBEDDING},
            "metadata": {
                "doc_index": 12,
                "chunk_index": 3,
                "data_source": "confluence",
                "recorded_at": "2026-04-13T09:00:01Z",
            },
        }
    ],
}

TEST_QUERY_REQUEST = {
    "request_id": "test-request-id",
    "wksp_id": "test-wksp",
    "mas_id": "test-mas",
    "query_criteria": {"query_type": "list_by_mas_id", "limit": 10},
}

TEST_SIMILARITY_SEARCH_REQUEST = {
    "request_id": "test-request-id",
    "wksp_id": "test-wksp",
    "mas_id": "test-mas",
    "embedding": DUMMY_EMBEDDING,
    "limit": 5,
    "metric": "cosine",
}


class TestKnowledgeVectorStoreEndpoint:
    """Test suite for POST /knowledge/vector (upsert)."""

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.create_vector_store")
    def test_upsert_success(self, mock_create):
        """Test successful upsert of vector records."""
        mock_create.return_value = KnowledgeVectorStoreResponse(
            request_id="test-request-id", status="success", message="Successfully saved 1 records"
        )

        response = test_client.post("/knowledge/vector", json=TEST_STORE_REQUEST)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["status"] == "success"

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.create_vector_store")
    def test_upsert_with_metadata(self, mock_create):
        """Test upsert accepts records with metadata."""
        mock_create.return_value = KnowledgeVectorStoreResponse(
            request_id="test-request-id", status="success", message="Successfully saved 1 records"
        )

        response = test_client.post("/knowledge/vector", json=TEST_STORE_REQUEST_WITH_METADATA)

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["status"] == "success"
        # Verify the metadata was passed through to the service
        called_with = mock_create.call_args[0][0]
        assert called_with.records[0].metadata["doc_index"] == 12
        assert called_with.records[0].metadata["chunk_index"] == 3
        assert called_with.records[0].metadata["data_source"] == "confluence"
        assert called_with.records[0].metadata["recorded_at"] == "2026-04-13T09:00:01Z"

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.create_vector_store")
    def test_upsert_without_metadata_is_valid(self, mock_create):
        """Test that omitting metadata in records is valid."""
        mock_create.return_value = KnowledgeVectorStoreResponse(
            request_id="test-request-id", status="success", message="Successfully saved 1 records"
        )

        response = test_client.post("/knowledge/vector", json=TEST_STORE_REQUEST)

        assert response.status_code == status.HTTP_201_CREATED
        called_with = mock_create.call_args[0][0]
        assert called_with.records[0].metadata is None

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.create_vector_store")
    def test_upsert_not_found(self, mock_create):
        """Test not-found when MAS store does not exist."""
        mock_create.return_value = KnowledgeVectorStoreResponse(
            request_id="test-request-id", status="not found", message="MAS store test-mas not found"
        )

        response = test_client.post("/knowledge/vector", json=TEST_STORE_REQUEST)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["status"] == "not found"

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.create_vector_store")
    def test_upsert_failure(self, mock_create):
        """Test failure case for upsert."""
        mock_create.return_value = KnowledgeVectorStoreResponse(
            request_id="test-request-id", status="failure", message="Failed to save records"
        )

        response = test_client.post("/knowledge/vector", json=TEST_STORE_REQUEST)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["status"] == "failure"

    def test_upsert_missing_mas_id(self):
        """Test validation error when mas_id is missing."""
        invalid = {**TEST_STORE_REQUEST}
        del invalid["mas_id"]

        response = test_client.post("/knowledge/vector", json=invalid)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["status"] == "validation error"

    def test_upsert_missing_wksp_id(self):
        """Test validation error when wksp_id is missing."""
        invalid = {**TEST_STORE_REQUEST}
        del invalid["wksp_id"]

        response = test_client.post("/knowledge/vector", json=invalid)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["status"] == "validation error"


class TestKnowledgeVectorQueryEndpoint:
    """Test suite for POST /knowledge/vector/query."""

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.query_vector_store")
    def test_query_success_without_metadata(self, mock_query):
        """Test successful query returning records without metadata."""
        mock_query.return_value = KnowledgeVectorQueryResponse(
            request_id="test-request-id",
            status="success",
            message="Successfully queried 1 records",
            records=[
                KnowledgeVectorQueryResponseRecord(
                    id="doc-1",
                    content="some document text",
                    embedding=EmbeddingConfig(data=DUMMY_EMBEDDING),
                )
            ],
        )

        response = test_client.post("/knowledge/vector/query", json=TEST_QUERY_REQUEST)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"
        record = response.json()["records"][0]
        assert record["id"] == "doc-1"
        assert record["content"] == "some document text"
        assert record.get("metadata") is None

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.query_vector_store")
    def test_query_success_with_metadata(self, mock_query):
        """Test successful query returning records with metadata."""
        mock_query.return_value = KnowledgeVectorQueryResponse(
            request_id="test-request-id",
            status="success",
            message="Successfully queried 1 records",
            records=[
                KnowledgeVectorQueryResponseRecord(
                    id="doc-1",
                    content="some document text",
                    embedding=EmbeddingConfig(data=DUMMY_EMBEDDING),
                    metadata={
                        "doc_index": 12,
                        "chunk_index": 3,
                        "data_source": "confluence",
                        "recorded_at": "2026-04-13T09:00:01Z",
                    },
                )
            ],
        )

        response = test_client.post("/knowledge/vector/query", json=TEST_QUERY_REQUEST)

        assert response.status_code == status.HTTP_200_OK
        record = response.json()["records"][0]
        assert record["metadata"]["doc_index"] == 12
        assert record["metadata"]["chunk_index"] == 3
        assert record["metadata"]["data_source"] == "confluence"
        assert record["metadata"]["recorded_at"] == "2026-04-13T09:00:01Z"

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.query_vector_store")
    def test_query_empty_results(self, mock_query):
        """Test query returning no records."""
        mock_query.return_value = KnowledgeVectorQueryResponse(
            request_id="test-request-id",
            status="success",
            message="No records found",
            records=[],
        )

        response = test_client.post("/knowledge/vector/query", json=TEST_QUERY_REQUEST)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["records"] == []

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.query_vector_store")
    def test_query_not_found(self, mock_query):
        """Test not-found when MAS store does not exist."""
        mock_query.return_value = KnowledgeVectorQueryResponse(
            request_id="test-request-id",
            status="not found",
            message="MAS store test-mas not found",
        )

        response = test_client.post("/knowledge/vector/query", json=TEST_QUERY_REQUEST)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["status"] == "not found"

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.query_vector_store")
    def test_query_failure(self, mock_query):
        """Test failure case for query."""
        mock_query.return_value = KnowledgeVectorQueryResponse(
            request_id="test-request-id",
            status="failure",
            message="Internal error",
        )

        response = test_client.post("/knowledge/vector/query", json=TEST_QUERY_REQUEST)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["status"] == "failure"

    def test_query_missing_mas_id(self):
        """Test validation error when mas_id is missing."""
        invalid = {**TEST_QUERY_REQUEST}
        del invalid["mas_id"]

        response = test_client.post("/knowledge/vector/query", json=invalid)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["status"] == "validation error"

    def test_query_missing_wksp_id(self):
        """Test validation error when wksp_id is missing."""
        invalid = {**TEST_QUERY_REQUEST}
        del invalid["wksp_id"]

        response = test_client.post("/knowledge/vector/query", json=invalid)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["status"] == "validation error"


class TestKnowledgeVectorSimilaritySearchEndpoint:
    """Test suite for POST /knowledge/vector/query/similarity."""

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.similarity_search")
    def test_similarity_search_success(self, mock_search):
        """Test successful similarity search."""
        mock_response = KnowledgeVectorSimilaritySearchResponse(
            request_id="test-request-id",
            status="success",
            message="Found 2 results",
            results=[],
        )
        mock_search.return_value = mock_response

        response = test_client.post("/knowledge/vector/query/similarity", json=TEST_SIMILARITY_SEARCH_REQUEST)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["request_id"] == "test-request-id"
        assert response.json()["status"] == "success"

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.similarity_search")
    def test_similarity_search_failure(self, mock_search):
        """Test failure case for similarity search."""
        mock_response = KnowledgeVectorSimilaritySearchResponse(
            request_id="test-request-id",
            status="failure",
            message="Similarity search failed: connection error",
        )
        mock_search.return_value = mock_response

        response = test_client.post("/knowledge/vector/query/similarity", json=TEST_SIMILARITY_SEARCH_REQUEST)

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert response.json()["request_id"] == "test-request-id"
        assert response.json()["status"] == "failure"

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.similarity_search")
    def test_similarity_search_not_found(self, mock_search):
        """Test not-found case when MAS store does not exist."""
        mock_response = KnowledgeVectorSimilaritySearchResponse(
            request_id="test-request-id",
            status="not found",
            message="MAS store test-mas not found",
        )
        mock_search.return_value = mock_response

        response = test_client.post("/knowledge/vector/query/similarity", json=TEST_SIMILARITY_SEARCH_REQUEST)

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["status"] == "not found"

    def test_similarity_search_missing_wksp_id(self):
        """Test validation error when wksp_id is missing."""
        invalid_request = {
            "mas_id": "test-mas",
            "embedding": DUMMY_EMBEDDING,
            "limit": 5,
            "metric": "cosine",
        }

        response = test_client.post("/knowledge/vector/query/similarity", json=invalid_request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["status"] == "validation error"

    def test_similarity_search_missing_mas_id(self):
        """Test validation error when mas_id is missing."""
        invalid_request = {
            "wksp_id": "test-wksp",
            "embedding": DUMMY_EMBEDDING,
            "limit": 5,
            "metric": "cosine",
        }

        response = test_client.post("/knowledge/vector/query/similarity", json=invalid_request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["status"] == "validation error"

    def test_similarity_search_missing_embedding(self):
        """Test validation error when embedding field is missing."""
        invalid_request = {
            "wksp_id": "test-wksp",
            "mas_id": "test-mas",
            "limit": 5,
            "metric": "cosine",
        }

        response = test_client.post("/knowledge/vector/query/similarity", json=invalid_request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_similarity_search_invalid_metric(self):
        """Test validation error for invalid metric value."""
        invalid_request = {
            "wksp_id": "test-wksp",
            "mas_id": "test-mas",
            "embedding": DUMMY_EMBEDDING,
            "metric": "inner-product",  # not supported for vector DB
        }

        response = test_client.post("/knowledge/vector/query/similarity", json=invalid_request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_similarity_search_limit_out_of_range(self):
        """Test validation error when limit exceeds allowed range."""
        invalid_request = {
            "wksp_id": "test-wksp",
            "mas_id": "test-mas",
            "embedding": DUMMY_EMBEDDING,
            "limit": 200,  # max is 100
        }

        response = test_client.post("/knowledge/vector/query/similarity", json=invalid_request)

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.similarity_search")
    def test_similarity_search_excludes_embedding_by_default(self, mock_search):
        """Test that embedding_vector is stripped from results by default."""
        mock_response = KnowledgeVectorSimilaritySearchResponse(
            request_id="test-request-id",
            status="success",
            message="Found 1 results",
            results=[
                KnowledgeVectorSimilaritySearchResult(
                    score=0.05,
                    id="doc-1",
                    content="Some document text",
                    embedding_vector=[0.1, 0.2, 0.3],
                )
            ],
        )
        mock_search.return_value = mock_response

        response = test_client.post("/knowledge/vector/query/similarity", json=TEST_SIMILARITY_SEARCH_REQUEST)

        assert response.status_code == status.HTTP_200_OK
        result = response.json()["results"][0]
        assert result.get("embedding_vector") is None
        assert result["id"] == "doc-1"
        assert result["content"] == "Some document text"
        assert result["score"] == 0.05

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.similarity_search")
    def test_similarity_search_includes_embedding_when_flag_set(self, mock_search):
        """Test that embedding_vector is populated when include_embeddings=true."""
        mock_response = KnowledgeVectorSimilaritySearchResponse(
            request_id="test-request-id",
            status="success",
            message="Found 1 results",
            results=[
                KnowledgeVectorSimilaritySearchResult(
                    score=0.05,
                    id="doc-1",
                    content="Some document text",
                    embedding_vector=[0.1, 0.2, 0.3],
                )
            ],
        )
        mock_search.return_value = mock_response

        response = test_client.post(
            "/knowledge/vector/query/similarity?include_embeddings=true", json=TEST_SIMILARITY_SEARCH_REQUEST
        )

        assert response.status_code == status.HTTP_200_OK
        result = response.json()["results"][0]
        assert result["embedding_vector"] == [0.1, 0.2, 0.3]

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.similarity_search")
    def test_similarity_search_l2_metric(self, mock_search):
        """Test similarity search with l2 metric."""
        mock_response = KnowledgeVectorSimilaritySearchResponse(
            request_id="test-request-id",
            status="success",
            message="Found 0 results",
        )
        mock_search.return_value = mock_response

        request = {
            "wksp_id": "test-wksp",
            "mas_id": "test-mas",
            "embedding": DUMMY_EMBEDDING,
            "limit": 10,
            "metric": "l2",
        }

        response = test_client.post("/knowledge/vector/query/similarity", json=request)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.similarity_search")
    def test_similarity_search_result_includes_metadata(self, mock_search):
        """Test that metadata from records is returned in results."""
        mock_response = KnowledgeVectorSimilaritySearchResponse(
            request_id="test-request-id",
            status="success",
            message="Found 1 results",
            results=[
                KnowledgeVectorSimilaritySearchResult(
                    score=0.05,
                    id="doc-1",
                    content="Some document text",
                    metadata={"doc_index": 12, "chunk_index": 3, "data_source": "confluence"},
                )
            ],
        )
        mock_search.return_value = mock_response

        response = test_client.post("/knowledge/vector/query/similarity", json=TEST_SIMILARITY_SEARCH_REQUEST)

        assert response.status_code == status.HTTP_200_OK
        result = response.json()["results"][0]
        assert result["metadata"]["doc_index"] == 12
        assert result["metadata"]["chunk_index"] == 3
        assert result["metadata"]["data_source"] == "confluence"

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.similarity_search")
    def test_similarity_search_with_doc_index_filter(self, mock_search):
        """Test similarity search filtered by doc_index."""
        mock_response = KnowledgeVectorSimilaritySearchResponse(
            request_id="test-request-id",
            status="success",
            message="Found 1 results",
            results=[],
        )
        mock_search.return_value = mock_response

        request = {**TEST_SIMILARITY_SEARCH_REQUEST, "metadata_filter": {"doc_index": 12}}
        response = test_client.post("/knowledge/vector/query/similarity", json=request)

        assert response.status_code == status.HTTP_200_OK
        assert response.json()["status"] == "success"
        called_with = mock_search.call_args[0][0]
        assert called_with.metadata_filter.doc_index == 12

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.similarity_search")
    def test_similarity_search_with_chunk_index_filter(self, mock_search):
        """Test similarity search filtered by chunk_index."""
        mock_response = KnowledgeVectorSimilaritySearchResponse(
            request_id="test-request-id",
            status="success",
            message="Found 1 results",
            results=[],
        )
        mock_search.return_value = mock_response

        request = {**TEST_SIMILARITY_SEARCH_REQUEST, "metadata_filter": {"chunk_index": 3}}
        response = test_client.post("/knowledge/vector/query/similarity", json=request)

        assert response.status_code == status.HTTP_200_OK
        called_with = mock_search.call_args[0][0]
        assert called_with.metadata_filter.chunk_index == 3

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.similarity_search")
    def test_similarity_search_with_data_source_filter(self, mock_search):
        """Test similarity search filtered by data_source."""
        mock_response = KnowledgeVectorSimilaritySearchResponse(
            request_id="test-request-id",
            status="success",
            message="Found 1 results",
            results=[],
        )
        mock_search.return_value = mock_response

        request = {**TEST_SIMILARITY_SEARCH_REQUEST, "metadata_filter": {"data_source": "confluence"}}
        response = test_client.post("/knowledge/vector/query/similarity", json=request)

        assert response.status_code == status.HTTP_200_OK
        called_with = mock_search.call_args[0][0]
        assert called_with.metadata_filter.data_source == "confluence"

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.similarity_search")
    def test_similarity_search_with_recorded_at_range_filter(self, mock_search):
        """Test similarity search filtered by recorded_at range."""
        mock_response = KnowledgeVectorSimilaritySearchResponse(
            request_id="test-request-id",
            status="success",
            message="Found 1 results",
            results=[],
        )
        mock_search.return_value = mock_response

        request = {
            **TEST_SIMILARITY_SEARCH_REQUEST,
            "metadata_filter": {
                "recorded_at_from": "2026-04-01T00:00:00Z",
                "recorded_at_to": "2026-04-14T00:00:00Z",
            },
        }
        response = test_client.post("/knowledge/vector/query/similarity", json=request)

        assert response.status_code == status.HTTP_200_OK
        called_with = mock_search.call_args[0][0]
        assert called_with.metadata_filter.recorded_at_from == "2026-04-01T00:00:00Z"
        assert called_with.metadata_filter.recorded_at_to == "2026-04-14T00:00:00Z"

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.similarity_search")
    def test_similarity_search_with_combined_metadata_filters(self, mock_search):
        """Test similarity search with multiple metadata filters combined."""
        mock_response = KnowledgeVectorSimilaritySearchResponse(
            request_id="test-request-id",
            status="success",
            message="Found 1 results",
            results=[],
        )
        mock_search.return_value = mock_response

        request = {
            **TEST_SIMILARITY_SEARCH_REQUEST,
            "metadata_filter": {
                "doc_index": 12,
                "chunk_index": 3,
                "data_source": "confluence",
                "recorded_at_from": "2026-04-01T00:00:00Z",
                "recorded_at_to": "2026-04-14T00:00:00Z",
            },
        }
        response = test_client.post("/knowledge/vector/query/similarity", json=request)

        assert response.status_code == status.HTTP_200_OK
        called_with = mock_search.call_args[0][0]
        assert called_with.metadata_filter.doc_index == 12
        assert called_with.metadata_filter.chunk_index == 3
        assert called_with.metadata_filter.data_source == "confluence"
        assert called_with.metadata_filter.recorded_at_from == "2026-04-01T00:00:00Z"
        assert called_with.metadata_filter.recorded_at_to == "2026-04-14T00:00:00Z"

    @patch("server.api.endpoints.knowledge_vector.knowledge_vector_service.similarity_search")
    def test_similarity_search_without_metadata_filter(self, mock_search):
        """Test that omitting metadata_filter is valid and passes None to service."""
        mock_response = KnowledgeVectorSimilaritySearchResponse(
            request_id="test-request-id",
            status="success",
            message="Found 0 results",
        )
        mock_search.return_value = mock_response

        response = test_client.post("/knowledge/vector/query/similarity", json=TEST_SIMILARITY_SEARCH_REQUEST)

        assert response.status_code == status.HTTP_200_OK
        called_with = mock_search.call_args[0][0]
        assert called_with.metadata_filter is None
