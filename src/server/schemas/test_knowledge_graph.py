import pytest
from pydantic import ValidationError

from knowledge_memory.server.schemas.knowledge_graph import (
    ResponseStatus,
    EmbeddingConfig,
    Concept,
    Relation,
    KnowledgeGraphStoreRequest,
    KnowledgeGraphStoreResponse,
    KnowledgeGraphDeleteRequest,
    KnowledgeGraphDeleteResponse,
    KnowledgeGraphQueryCriteria,
    KnowledgeGraphQueryRequest,
    KnowledgeGraphQueryResponse,
    KnowledgeGraphQueryResponseRecord,
    QUERY_TYPE_NEIGHBOUR,
    QUERY_TYPE_PATH,
)


class TestResponseStatus:
    """Test suite for ResponseStatus enum."""

    def test_response_status_values(self):
        """Test that ResponseStatus enum has correct values."""
        assert ResponseStatus.SUCCESS == "success"
        assert ResponseStatus.FAILURE == "failure"
        assert ResponseStatus.VALIDATION_ERROR == "validation error"
        assert ResponseStatus.NOT_FOUND == "not found"

    def test_response_status_string_inheritance(self):
        """Test that ResponseStatus inherits from str."""
        assert isinstance(ResponseStatus.SUCCESS, str)
        assert ResponseStatus.SUCCESS == "success"


class TestEmbeddingConfig:
    """Test suite for EmbeddingConfig model."""

    def test_embedding_config_creation(self):
        """Test creation of EmbeddingConfig with valid data."""
        embedding = EmbeddingConfig(name="test-model", data=[0.1, 0.2, 0.3])
        assert embedding.name == "test-model"
        assert embedding.data == [0.1, 0.2, 0.3]

    def test_embedding_config_defaults(self):
        """Test EmbeddingConfig with default values."""
        embedding = EmbeddingConfig(name="test-model")
        assert embedding.name == "test-model"
        assert embedding.data == []

    def test_embedding_config_required_name(self):
        """Test that name is required for EmbeddingConfig."""
        with pytest.raises(ValidationError, match="Field required"):
            EmbeddingConfig()


class TestConcept:
    """Test suite for Concept model."""

    def test_concept_creation(self):
        """Test creation of Concept with all fields."""
        concept = Concept(
            id="test-id",
            name="Test Concept",
            description="A test concept",
            attributes={"key": "value"},
            embeddings={"name": "test-model", "data": [0.1, 0.2, 0.3]},
            tags=["tag1", "tag2"],
        )
        assert concept.id == "test-id"
        assert concept.name == "Test Concept"
        assert concept.description == "A test concept"
        assert concept.attributes == {"key": "value"}
        assert concept.embeddings.name == "test-model"
        assert concept.embeddings.data == [0.1, 0.2, 0.3]
        assert concept.tags == ["tag1", "tag2"]

    def test_concept_minimal(self):
        """Test creation of Concept with minimal required fields."""
        concept = Concept(id="test-id", name="Test Concept")
        assert concept.id == "test-id"
        assert concept.name == "Test Concept"
        assert concept.description is None
        assert concept.attributes == {}
        assert concept.embeddings is None
        assert concept.tags == []

    def test_concept_required_fields(self):
        """Test that id and name are required for Concept."""
        with pytest.raises(ValidationError, match="Field required"):
            Concept()

        with pytest.raises(ValidationError, match="Field required"):
            Concept(id="test-id")

        with pytest.raises(ValidationError, match="Field required"):
            Concept(name="Test Concept")


class TestRelation:
    """Test suite for Relation model."""

    def test_relation_creation(self):
        """Test creation of Relation with all fields."""
        relation = Relation(
            id="rel1",
            relation="RELATED_TO",
            node_ids=["node1", "node2"],
            attributes={"strength": 0.8},
            embeddings={"name": "test-model", "data": [0.1, 0.2, 0.3]},
        )
        assert relation.id == "rel1"
        assert relation.relation == "RELATED_TO"
        assert relation.node_ids == ["node1", "node2"]
        assert relation.attributes == {"strength": 0.8}
        assert relation.embeddings.name == "test-model"
        assert relation.embeddings.data == [0.1, 0.2, 0.3]

    def test_relation_minimal(self):
        """Test creation of Relation with minimal required fields."""
        relation = Relation(id="rel1", relation="RELATED_TO", node_ids=["node1", "node2"])
        assert relation.id == "rel1"
        assert relation.relation == "RELATED_TO"
        assert relation.node_ids == ["node1", "node2"]
        assert relation.attributes == {}
        assert relation.embeddings is None

    def test_relation_node_validation(self):
        """Test that Relation validates minimum number of nodes."""
        # Should raise error with less than 2 nodes
        with pytest.raises(ValidationError, match="List should have at least 2 items"):
            Relation(id="rel1", relation="REL", node_ids=["node1"])  # Only 1 node

        # Should not raise with exactly 2 nodes
        relation = Relation(id="rel1", relation="REL", node_ids=["node1", "node2"])
        assert len(relation.node_ids) == 2

        # Should not raise with more than 2 nodes
        relation = Relation(id="rel2", relation="REL", node_ids=["node1", "node2", "node3"])
        assert len(relation.node_ids) == 3

    def test_relation_required_fields(self):
        """Test that required fields are validated."""
        with pytest.raises(ValidationError, match="Field required"):
            Relation()

        with pytest.raises(ValidationError, match="Field required"):
            Relation(id="rel1")

        with pytest.raises(ValidationError, match="Field required"):
            Relation(id="rel1", relation="REL")


class TestKnowledgeGraphStoreRequest:
    """Test suite for KnowledgeGraphStoreRequest model."""

    def test_store_request_creation(self):
        """Test creation of KnowledgeGraphStoreRequest with valid data."""
        request = KnowledgeGraphStoreRequest(
            mas_id="test-mas",
            wksp_id="test-wksp",
            memory_type="Semantic",
            records={
                "concepts": [
                    {"id": "n1", "name": "Node 1"},
                    {"id": "n2", "name": "Node 2"},
                    {"id": "c1", "name": "Test"},
                ],
                "relations": [
                    {"id": "r1", "relation": "REL", "node_ids": ["n1", "n2"]}  # Both nodes exist in concepts
                ],
            },
        )
        assert request.mas_id == "test-mas"
        assert request.wksp_id == "test-wksp"
        assert request.memory_type == "Semantic"
        assert len(request.records["concepts"]) == 3
        assert len(request.records["relations"]) == 1
        assert isinstance(request.request_id, str)

    def test_store_request_optional_fields(self):
        """Test creation with optional fields."""
        request = KnowledgeGraphStoreRequest(mas_id="test-mas")
        assert request.mas_id == "test-mas"
        assert request.wksp_id is None
        assert request.memory_type is None
        assert request.records is None
        assert request.force_replace is False
        assert isinstance(request.request_id, str)

    def test_store_request_validation_mas_or_wksp_required(self):
        """Test that either mas_id or wksp_id is required."""
        with pytest.raises(ValidationError, match="Either 'mas_id' or 'wksp_id' or both must be provided"):
            KnowledgeGraphStoreRequest()

    def test_store_request_relation_node_references(self):
        """Test that relations can only reference nodes that exist in concepts."""
        # Should raise error when relation references non-existent node
        with pytest.raises(
            ValidationError, match="references non-existent node ID 'nonexistent'.*Available concept IDs: c1, c2"
        ):
            KnowledgeGraphStoreRequest(
                mas_id="test-mas",
                records={
                    "concepts": [{"id": "c1", "name": "Concept 1"}, {"id": "c2", "name": "Concept 2"}],
                    "relations": [
                        {
                            "id": "r1",
                            "relation": "REL",
                            "node_ids": ["c1", "nonexistent"],  # 'nonexistent' is not in concepts
                        }
                    ],
                },
            )

        # Should not raise when all node references are valid
        request = KnowledgeGraphStoreRequest(
            mas_id="test-mas",
            records={
                "concepts": [{"id": "c1", "name": "Concept 1"}, {"id": "c2", "name": "Concept 2"}],
                "relations": [
                    {"id": "r1", "relation": "REL", "node_ids": ["c1", "c2"]}  # Both nodes exist in concepts
                ],
            },
        )
        assert len(request.records["concepts"]) == 2
        assert len(request.records["relations"]) == 1


class TestKnowledgeGraphStoreResponse:
    """Test suite for KnowledgeGraphStoreResponse model."""

    def test_store_response_creation(self):
        """Test creation of KnowledgeGraphStoreResponse with valid data."""
        response = KnowledgeGraphStoreResponse(
            request_id="req-123", status=ResponseStatus.SUCCESS, message="Operation completed"
        )
        assert response.request_id == "req-123"
        assert response.status == ResponseStatus.SUCCESS
        assert response.message == "Operation completed"

    def test_store_response_minimal(self):
        """Test creation with minimal required fields."""
        response = KnowledgeGraphStoreResponse(status=ResponseStatus.SUCCESS)
        assert response.status == ResponseStatus.SUCCESS
        assert response.request_id is None
        assert response.message is None

    def test_store_response_model_dump_excludes_none(self):
        """Test that model_dump excludes None request_id."""
        response = KnowledgeGraphStoreResponse(status=ResponseStatus.SUCCESS)
        data = response.model_dump()
        assert "request_id" not in data
        assert data["status"] == "success"


class TestKnowledgeGraphDeleteRequest:
    """Test suite for KnowledgeGraphDeleteRequest model."""

    def test_delete_request_creation(self):
        """Test creation of KnowledgeGraphDeleteRequest with valid data."""
        request = KnowledgeGraphDeleteRequest(
            mas_id="test-mas", wksp_id="test-wksp", records={"concepts": [{"id": "c1"}, {"id": "c2"}]}
        )
        assert request.mas_id == "test-mas"
        assert request.wksp_id == "test-wksp"
        assert len(request.records["concepts"]) == 2
        assert isinstance(request.request_id, str)

    def test_delete_request_optional_records(self):
        """Test creation with optional records."""
        request = KnowledgeGraphDeleteRequest(mas_id="test-mas")
        assert request.mas_id == "test-mas"
        assert request.records is None

    def test_delete_request_validation_mas_or_wksp_required(self):
        """Test that either mas_id or wksp_id is required."""
        with pytest.raises(ValidationError, match="Either 'mas_id' or 'wksp_id' or both must be provided"):
            KnowledgeGraphDeleteRequest()


class TestKnowledgeGraphDeleteResponse:
    """Test suite for KnowledgeGraphDeleteResponse model."""

    def test_delete_response_creation(self):
        """Test creation of KnowledgeGraphDeleteResponse with valid data."""
        response = KnowledgeGraphDeleteResponse(
            request_id="req-123", status=ResponseStatus.SUCCESS, message="Deleted successfully"
        )
        assert response.request_id == "req-123"
        assert response.status == ResponseStatus.SUCCESS
        assert response.message == "Deleted successfully"


class TestKnowledgeGraphQueryCriteria:
    """Test suite for KnowledgeGraphQueryCriteria model."""

    def test_query_criteria_defaults(self):
        """Test that KnowledgeGraphQueryCriteria has correct default values."""
        criteria = KnowledgeGraphQueryCriteria()
        assert criteria.depth is None
        assert criteria.use_direction is True
        assert criteria.query_type == QUERY_TYPE_NEIGHBOUR

    def test_query_criteria_custom_values(self):
        """Test KnowledgeGraphQueryCriteria with custom values."""
        criteria = KnowledgeGraphQueryCriteria(depth=3, query_type=QUERY_TYPE_PATH)
        assert criteria.depth == 3
        assert criteria.query_type == QUERY_TYPE_PATH


class TestKnowledgeGraphQueryRequest:
    """Test suite for KnowledgeGraphQueryRequest model."""

    def test_query_request_minimal(self):
        """Test minimal valid request with only required fields."""
        request = KnowledgeGraphQueryRequest(mas_id="test-mas", records={"concepts": [{"id": "test-id"}]})
        assert request.records == {"concepts": [{"id": "test-id"}]}
        assert request.mas_id == "test-mas"
        assert request.wksp_id is None
        assert isinstance(request.request_id, str)
        assert isinstance(request.query_criteria, KnowledgeGraphQueryCriteria)

    def test_query_request_full(self):
        """Test request with all fields provided."""
        request = KnowledgeGraphQueryRequest(
            request_id="test-request-id",
            records={"concepts": [{"id": "test-id-1"}, {"id": "test-id-2"}]},
            mas_id="test-mas",
            wksp_id="test-wksp",
            query_criteria=KnowledgeGraphQueryCriteria(depth=2, query_type=QUERY_TYPE_PATH),
        )
        assert request.request_id == "test-request-id"
        assert request.mas_id == "test-mas"
        assert request.wksp_id == "test-wksp"
        assert request.query_criteria.depth == 2
        assert request.query_criteria.query_type == QUERY_TYPE_PATH

    def test_query_request_concept_count_validation_neighbor(self):
        """Test neighbor query concept count validation."""
        # Should raise error with wrong number of concepts for neighbor query
        with pytest.raises(ValidationError, match="Neighbor queries require exactly 1 concept"):
            KnowledgeGraphQueryRequest(
                mas_id="test-mas",
                records={"concepts": [{"id": "c1"}, {"id": "c2"}]},  # 2 concepts for neighbor query
                query_criteria=KnowledgeGraphQueryCriteria(query_type=QUERY_TYPE_NEIGHBOUR),
            )

        # Should not raise with exactly 1 concept for neighbor query
        request = KnowledgeGraphQueryRequest(
            mas_id="test-mas",
            records={"concepts": [{"id": "c1"}]},
            query_criteria=KnowledgeGraphQueryCriteria(query_type=QUERY_TYPE_NEIGHBOUR),
        )
        assert len(request.records["concepts"]) == 1

    def test_query_request_concept_count_validation_path(self):
        """Test path query concept count validation."""
        # Should raise error with wrong number of concepts for path query
        with pytest.raises(ValidationError, match="Path queries require exactly 2 concepts"):
            KnowledgeGraphQueryRequest(
                mas_id="test-mas",
                records={"concepts": [{"id": "c1"}]},  # 1 concept for path query
                query_criteria=KnowledgeGraphQueryCriteria(query_type=QUERY_TYPE_PATH),
            )

        # Should not raise with exactly 2 concepts for path query
        request = KnowledgeGraphQueryRequest(
            mas_id="test-mas",
            records={"concepts": [{"id": "c1"}, {"id": "c2"}]},
            query_criteria=KnowledgeGraphQueryCriteria(query_type=QUERY_TYPE_PATH),
        )
        assert len(request.records["concepts"]) == 2

    def test_query_request_records_validation(self):
        """Test records validation."""
        with pytest.raises(ValidationError, match="Records must exist with 'concepts' key"):
            KnowledgeGraphQueryRequest(mas_id="test-mas", records={})

        with pytest.raises(ValidationError, match="concepts must be a list"):
            KnowledgeGraphQueryRequest(mas_id="test-mas", records={"concepts": "not_a_list"})


class TestKnowledgeGraphQueryResponseRecord:
    """Test suite for KnowledgeGraphQueryResponseRecord model."""

    def test_query_response_record_empty(self):
        """Test record with no data."""
        record = KnowledgeGraphQueryResponseRecord()
        assert record.relationships == []
        assert record.concepts == []

    def test_query_response_record_with_data(self):
        """Test record with all fields populated."""
        concept = Concept(id="c1", name="Test Concept")
        relation = Relation(id="r1", relation="HAS", node_ids=["c1", "c2"])

        record = KnowledgeGraphQueryResponseRecord(relationships=[relation], concepts=[concept])

        assert record.relationships == [relation]
        assert record.concepts == [concept]


class TestKnowledgeGraphQueryResponse:
    """Test suite for KnowledgeGraphQueryResponse model."""

    def test_query_response_minimal(self):
        """Test minimal response with only required fields."""
        response = KnowledgeGraphQueryResponse(status=ResponseStatus.SUCCESS)
        assert response.status == ResponseStatus.SUCCESS
        assert response.request_id is None
        assert response.message is None
        assert response.records is None

    def test_query_response_full(self):
        """Test response with all fields populated."""
        concept = Concept(id="c1", name="Test Concept")
        record = KnowledgeGraphQueryResponseRecord(concepts=[concept])

        response = KnowledgeGraphQueryResponse(
            request_id="test-request",
            status=ResponseStatus.SUCCESS,
            message="Query executed successfully",
            records=[record],
        )

        assert response.request_id == "test-request"
        assert response.status == ResponseStatus.SUCCESS
        assert response.message == "Query executed successfully"
        assert len(response.records) == 1

    def test_query_response_model_dump_excludes_empty_records(self):
        """Test that model_dump excludes None or empty records."""
        # Test with None records
        response = KnowledgeGraphQueryResponse(status=ResponseStatus.SUCCESS, records=None)
        data = response.model_dump()
        assert "records" not in data

        # Test with empty records
        response = KnowledgeGraphQueryResponse(status=ResponseStatus.SUCCESS, records=[])
        data = response.model_dump()
        assert "records" not in data

        # Test with actual records
        record = KnowledgeGraphQueryResponseRecord()
        response = KnowledgeGraphQueryResponse(status=ResponseStatus.SUCCESS, records=[record])
        data = response.model_dump()
        assert "records" in data
        assert len(data["records"]) == 1

    def test_query_response_model_dump_excludes_none_request_id(self):
        """Test that model_dump excludes None request_id."""
        response = KnowledgeGraphQueryResponse(status=ResponseStatus.SUCCESS)
        data = response.model_dump()
        assert "request_id" not in data
        assert data["status"] == "success"
