import pytest
from pydantic import ValidationError
from server.schemas.tkf import (
    EmbeddingConfig,
    Concept,
    Relation,
    TkfStoreRequest,
    TkfStoreResponse,
    TkfDeleteRequest,
    TkfDeleteResponse,
)


class TestTkfSchema:
    """Test suite for TKF schema models."""

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

    def test_tkf_store_request_creation(self):
        """Test creation of TkfStoreRequest with valid data."""
        request = TkfStoreRequest(
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

    def test_tkf_store_response_creation(self):
        """Test creation of TkfStoreResponse with valid data."""
        response = TkfStoreResponse(request_id="req-123", status="success", message="Operation completed")
        assert response.request_id == "req-123"
        assert response.status == "success"
        assert response.message == "Operation completed"

    def test_tkf_delete_request_creation(self):
        """Test creation of TkfDeleteRequest with valid data."""
        request = TkfDeleteRequest(mas_id="test-mas", wksp_id="test-wksp", records={"concepts": ["c1", "c2"]})
        assert request.mas_id == "test-mas"
        assert request.wksp_id == "test-wksp"
        assert len(request.records["concepts"]) == 2
        assert "c1" in request.records["concepts"]
        assert "c2" in request.records["concepts"]

    def test_tkf_delete_response_creation(self):
        """Test creation of TkfDeleteResponse with valid data."""
        response = TkfDeleteResponse(request_id="req-123", status="success", message="Deleted successfully")
        assert response.request_id == "req-123"
        assert response.status == "success"
        assert response.message == "Deleted successfully"

    def test_tkf_create_request_without_mas_id(self):
        """Test creation of TkfCreateRequest without mas_id."""
        request = TkfStoreRequest(
            wksp_id="test-wksp",
            memory_type="Semantic",
            records={
                "concepts": [
                    {"id": "c1", "name": "Test"},
                    {"id": "n1", "name": "Node 1"},
                    {"id": "n2", "name": "Node 2"},
                ],
                "relations": [
                    {"id": "r1", "relation": "REL", "node_ids": ["n1", "n2"]}  # Both nodes exist in concepts
                ],
            },
        )
        assert request.mas_id is None
        assert len(request.records["concepts"]) == 3
        assert len(request.records["relations"]) == 1

    def test_tkf_delete_request_without_mas_id(self):
        """Test creation of TkfDeleteRequest without mas_id."""
        request = TkfDeleteRequest(wksp_id="test-wksp", records={"concepts": ["c1", "c2"]})
        assert request.wksp_id == "test-wksp"
        assert request.records["concepts"] == ["c1", "c2"]
        assert request.mas_id is None

    def test_relation_node_references_validation(self):
        """Test that relations can only reference nodes that exist in concepts."""
        # Should raise error when relation references non-existent node
        with pytest.raises(
            ValidationError, match="references non-existent node ID 'nonexistent'.*Available concept IDs: c1, c2"
        ):
            TkfStoreRequest(
                wksp_id="test-wksp",
                memory_type="Semantic",
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
        request = TkfStoreRequest(
            wksp_id="test-wksp",
            memory_type="Semantic",
            records={
                "concepts": [{"id": "c1", "name": "Concept 1"}, {"id": "c2", "name": "Concept 2"}],
                "relations": [
                    {"id": "r1", "relation": "REL", "node_ids": ["c1", "c2"]}  # Both nodes exist in concepts
                ],
            },
        )
        assert len(request.records["concepts"]) == 2
        assert len(request.records["relations"]) == 1
        assert request.mas_id is None
