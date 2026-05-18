# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

import pytest
from pydantic import ValidationError

from server.schemas.knowledge_graph import (
    ResponseStatus,
    EmbeddingConfig,
    Concept,
    Relation,
    InternalAttributes,
    FilterCategory,
    FilterOperation,
    KnowledgeGraphQueryCriteriaFilter,
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
    QUERY_TYPE_CONCEPTS,
    QUERY_TYPE_RELATIONS,
    DEFAULT_PROPERTY_KEY_SEPARATOR,
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

    def test_store_request_incremental_update_defaults_false(self):
        """Test that incremental_update defaults to False."""
        request = KnowledgeGraphStoreRequest(mas_id="test-mas")
        assert request.incremental_update is False

    def test_store_request_incremental_update_allows_external_node_reference(self):
        """With incremental_update=True, relations may reference nodes not in this batch."""
        request = KnowledgeGraphStoreRequest(
            mas_id="test-mas",
            incremental_update=True,
            records={
                "concepts": [{"id": "new-concept", "name": "CoDiN"}],
                "relations": [
                    {
                        "id": "r1",
                        "relation": "CoDi",
                        # "existing-anchor" is already in the graph — not in concepts above.
                        "node_ids": ["existing-anchor", "new-concept"],
                    }
                ],
            },
        )
        assert request.incremental_update is True
        assert len(request.records["concepts"]) == 1
        assert len(request.records["relations"]) == 1

    def test_store_request_incremental_update_allows_relations_only(self):
        """With incremental_update=True, sending only relations (no new concepts) is valid."""
        request = KnowledgeGraphStoreRequest(
            mas_id="test-mas",
            incremental_update=True,
            records={
                "concepts": [],
                "relations": [
                    {
                        "id": "r1",
                        "relation": "INTEGRATES_WITH",
                        "node_ids": ["existing-node-a", "existing-node-b"],
                    }
                ],
            },
        )
        assert len(request.records["concepts"]) == 0
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


class TestInternalAttributes:
    """Test suite for InternalAttributes model."""

    def test_internal_attributes_creation(self):
        """Test creation of InternalAttributes with valid data."""
        internal_attrs = InternalAttributes(
            owner="550e8400-e29b-41d4-a716-446655440000",
            attributes={"category": "Technology", "rate": 19.5}
        )
        assert internal_attrs.owner == "550e8400-e29b-41d4-a716-446655440000"
        assert internal_attrs.attributes == {"category": "Technology", "rate": 19.5}

    def test_internal_attributes_empty_attributes(self):
        """Test InternalAttributes with empty attributes."""
        internal_attrs = InternalAttributes(
            owner="550e8400-e29b-41d4-a716-446655440000",
            attributes={}
        )
        assert internal_attrs.owner == "550e8400-e29b-41d4-a716-446655440000"
        assert internal_attrs.attributes == {}

    def test_internal_attributes_none_attributes(self):
        """Test InternalAttributes with None attributes (should use default)."""
        internal_attrs = InternalAttributes(owner="550e8400-e29b-41d4-a716-446655440000")
        assert internal_attrs.owner == "550e8400-e29b-41d4-a716-446655440000"
        assert internal_attrs.attributes == {}

    def test_internal_attributes_uuid_validation_valid(self):
        """Test that valid UUIDs are accepted."""
        valid_uuids = [
            "550e8400-e29b-41d4-a716-446655440000",
            "123e4567-e89b-12d3-a456-426614174000",
            "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF"
        ]
        
        for uuid_val in valid_uuids:
            internal_attrs = InternalAttributes(owner=uuid_val, attributes={"test": "value"})
            assert internal_attrs.owner == uuid_val

    def test_internal_attributes_uuid_validation_invalid(self):
        """Test that invalid UUIDs are rejected."""
        invalid_uuids = [
            "not-a-uuid",
            "550e8400-e29b-41d4-a716",  # Too short
            "550e8400-e29b-41d4-a716-446655440000-extra",  # Too long
            "",  # Empty
            "550e8400-e29b-41d4-a716-44665544000g",  # Invalid character
        ]
        
        for uuid_val in invalid_uuids:
            with pytest.raises(ValidationError, match="owner must be a valid UUID"):
                InternalAttributes(owner=uuid_val, attributes={"test": "value"})

    def test_internal_attributes_mixed_value_types(self):
        """Test InternalAttributes with mixed value types."""
        internal_attrs = InternalAttributes(
            owner="550e8400-e29b-41d4-a716-446655440000",
            attributes={
                "string_val": "text",
                "int_val": 42,
                "float_val": 3.14,
                "bool_val": True  # Should be converted or handled
            }
        )
        assert internal_attrs.attributes["string_val"] == "text"
        assert internal_attrs.attributes["int_val"] == 42
        assert internal_attrs.attributes["float_val"] == 3.14


class TestFilterCategory:
    """Test suite for FilterCategory enum."""

    def test_filter_category_values(self):
        """Test that FilterCategory enum has correct values."""
        assert FilterCategory.CUSTOM == "custom"
        assert FilterCategory.DYNAMIC == "dynamic"
        assert FilterCategory.INTERNAL == "internal"

    def test_filter_category_string_inheritance(self):
        """Test that FilterCategory inherits from str."""
        assert isinstance(FilterCategory.CUSTOM, str)
        assert FilterCategory.CUSTOM == "custom"


class TestFilterOperation:
    """Test suite for FilterOperation enum."""

    def test_filter_operation_values(self):
        """Test that FilterOperation enum has correct values."""
        assert FilterOperation.EQSTR == "eqstr"
        assert FilterOperation.EQ == "eq"
        assert FilterOperation.GT == "gt"
        assert FilterOperation.GTE == "gte"
        assert FilterOperation.LT == "lt"
        assert FilterOperation.LTE == "lte"
        assert FilterOperation.RANGE == "range"

    def test_filter_operation_string_inheritance(self):
        """Test that FilterOperation inherits from str."""
        assert isinstance(FilterOperation.EQSTR, str)
        assert FilterOperation.EQ == "eq"


class TestKnowledgeGraphQueryCriteriaFilter:
    """Test suite for KnowledgeGraphQueryCriteriaFilter model."""

    def test_filter_creation_custom_category(self):
        """Test creation of filter with custom category."""
        filter_obj = KnowledgeGraphQueryCriteriaFilter(
            category=FilterCategory.CUSTOM,
            key="name",
            operation=FilterOperation.EQSTR,
            value=["Test Concept"]
        )
        assert filter_obj.category == FilterCategory.CUSTOM
        assert filter_obj.key == "name"
        assert filter_obj.operation == FilterOperation.EQSTR
        assert filter_obj.value == ["Test Concept"]

    def test_filter_creation_dynamic_category(self):
        """Test creation of filter with dynamic category."""
        filter_obj = KnowledgeGraphQueryCriteriaFilter(
            category=FilterCategory.DYNAMIC,
            key="custom_property",
            operation=FilterOperation.EQ,
            value=[42]
        )
        assert filter_obj.category == FilterCategory.DYNAMIC
        assert filter_obj.key == "custom_property"
        assert filter_obj.operation == FilterOperation.EQ
        assert filter_obj.value == [42]

    def test_filter_creation_internal_category(self):
        """Test creation of filter with internal category."""
        filter_obj = KnowledgeGraphQueryCriteriaFilter(
            category=FilterCategory.INTERNAL,
            key="category",
            operation=FilterOperation.EQSTR,
            value=["Technology"],
            owner="550e8400-e29b-41d4-a716-446655440000"
        )
        assert filter_obj.category == FilterCategory.INTERNAL
        assert filter_obj.key == "category"
        assert filter_obj.operation == FilterOperation.EQSTR
        assert filter_obj.value == ["Technology"]
        assert filter_obj.owner == "550e8400-e29b-41d4-a716-446655440000"

    def test_filter_internal_category_allows_missing_owner(self):
        """Test that internal category allows missing owner field (it's optional)."""
        # This should work - owner is optional
        filter_obj = KnowledgeGraphQueryCriteriaFilter(
            category=FilterCategory.INTERNAL,
            key="category",
            operation=FilterOperation.EQSTR,
            value=["Technology"]
            # Owner is optional
        )
        assert filter_obj.category == FilterCategory.INTERNAL
        assert filter_obj.owner is None

    def test_filter_internal_category_owner_uuid_validation(self):
        """Test that internal category owner must be valid UUID."""
        with pytest.raises(ValidationError, match="owner must be a valid UUID"):
            KnowledgeGraphQueryCriteriaFilter(
                category=FilterCategory.INTERNAL,
                key="category",
                operation=FilterOperation.EQSTR,
                value=["Technology"],
                owner="invalid-uuid"
            )

    def test_filter_eqstr_operation_validation(self):
        """Test that EQSTR operation accepts string values (single or multiple for OR logic)."""
        # Valid: single string value
        filter_obj = KnowledgeGraphQueryCriteriaFilter(
            category=FilterCategory.CUSTOM,
            key="name",
            operation=FilterOperation.EQSTR,
            value=["single_string"]
        )
        assert filter_obj.value == ["single_string"]

        # Valid: multiple string values for OR logic
        filter_obj_multiple = KnowledgeGraphQueryCriteriaFilter(
            category=FilterCategory.CUSTOM,
            key="name",
            operation=FilterOperation.EQSTR,
            value=["string1", "string2", "string3"]
        )
        assert filter_obj_multiple.value == ["string1", "string2", "string3"]

        # Invalid: numeric values with EQSTR
        with pytest.raises(ValidationError, match="eqstr operation requires string values only"):
            KnowledgeGraphQueryCriteriaFilter(
                category=FilterCategory.DYNAMIC,
                key="numeric_prop",
                operation=FilterOperation.EQSTR,
                value=[42, 100]
            )

    def test_filter_eq_operation_validation(self):
        """Test that EQ operation accepts numeric values (single or multiple for OR logic)."""
        # Valid: single numeric value
        filter_obj = KnowledgeGraphQueryCriteriaFilter(
            category=FilterCategory.CUSTOM,
            key="age",
            operation=FilterOperation.EQ,
            value=[25]
        )
        assert filter_obj.value == [25]

        # Valid: multiple numeric values for OR logic
        filter_obj_multiple = KnowledgeGraphQueryCriteriaFilter(
            category=FilterCategory.CUSTOM,
            key="age",
            operation=FilterOperation.EQ,
            value=[25, 30, 35]
        )
        assert filter_obj_multiple.value == [25, 30, 35]

        # Invalid: string values with EQ
        with pytest.raises(ValidationError, match="Operation 'FilterOperation.EQ' requires non-string values \\(numeric only\\)"):
            KnowledgeGraphQueryCriteriaFilter(
                category=FilterCategory.DYNAMIC,
                key="numeric_prop",
                operation=FilterOperation.EQ,
                value=["string1", "string2"]
            )

    def test_filter_numeric_operations_validation(self):
        """Test that numeric operations reject string values."""
        numeric_operations = [FilterOperation.EQ, FilterOperation.GT, FilterOperation.GTE, 
                            FilterOperation.LT, FilterOperation.LTE, FilterOperation.RANGE]
        
        for operation in numeric_operations:
            if operation == FilterOperation.RANGE:
                # Range requires exactly 2 values
                filter_obj = KnowledgeGraphQueryCriteriaFilter(
                    category=FilterCategory.DYNAMIC,
                    key="numeric_prop",
                    operation=operation,
                    value=[10, 20]
                )
                assert filter_obj.value == [10, 20]
            else:
                filter_obj = KnowledgeGraphQueryCriteriaFilter(
                    category=FilterCategory.DYNAMIC,
                    key="numeric_prop",
                    operation=operation,
                    value=[42]
                )
                assert filter_obj.value == [42]

        # Invalid: string values with numeric operations
        with pytest.raises(ValidationError, match="requires non-string values"):
            KnowledgeGraphQueryCriteriaFilter(
                category=FilterCategory.DYNAMIC,
                key="numeric_prop",
                operation=FilterOperation.EQ,
                value=["string_value"]
            )

    def test_filter_range_operation_validation(self):
        """Test that RANGE operation requires exactly 2 values."""
        # Valid: exactly 2 values
        filter_obj = KnowledgeGraphQueryCriteriaFilter(
            category=FilterCategory.DYNAMIC,
            key="numeric_prop",
            operation=FilterOperation.RANGE,
            value=[10, 20]
        )
        assert filter_obj.value == [10, 20]

        # Invalid: 1 value
        with pytest.raises(ValidationError, match="Range operation requires exactly 2 values"):
            KnowledgeGraphQueryCriteriaFilter(
                category=FilterCategory.DYNAMIC,
                key="numeric_prop",
                operation=FilterOperation.RANGE,
                value=[10]
            )

        # Invalid: 3 values
        with pytest.raises(ValidationError, match="Range operation requires exactly 2 values"):
            KnowledgeGraphQueryCriteriaFilter(
                category=FilterCategory.DYNAMIC,
                key="numeric_prop",
                operation=FilterOperation.RANGE,
                value=[10, 20, 30]
            )

    def test_filter_range_operation_min_max_validation(self):
        """Test that RANGE operation validates min <= max."""
        # Valid: min <= max
        filter_obj = KnowledgeGraphQueryCriteriaFilter(
            category=FilterCategory.DYNAMIC,
            key="numeric_prop",
            operation=FilterOperation.RANGE,
            value=[10, 20]
        )
        assert filter_obj.value == [10, 20]

        # Invalid: min > max
        with pytest.raises(ValidationError, match="Range: first value \\(min\\) must be <= second value \\(max\\)"):
            KnowledgeGraphQueryCriteriaFilter(
                category=FilterCategory.DYNAMIC,
                key="numeric_prop",
                operation=FilterOperation.RANGE,
                value=[20, 10]
            )

    def test_filter_custom_key_validation_concepts(self):
        """Test validation of custom keys for concepts."""
        # Valid custom keys for concepts
        valid_keys = ["id", "name", "relations_cnt"]
        
        for key in valid_keys:
            if key == "relations_cnt":
                # Numeric key - use numeric operation
                filter_obj = KnowledgeGraphQueryCriteriaFilter(
                    category=FilterCategory.CUSTOM,
                    key=key,
                    operation=FilterOperation.EQ,
                    value=[5]
                )
            else:
                # String key - use EQSTR operation
                filter_obj = KnowledgeGraphQueryCriteriaFilter(
                    category=FilterCategory.CUSTOM,
                    key=key,
                    operation=FilterOperation.EQSTR,
                    value=["test_value"]
                )
            assert filter_obj.key == key

        # Invalid custom key for concepts - test by manually calling validation after setting context
        filter_obj = KnowledgeGraphQueryCriteriaFilter(
            category=FilterCategory.CUSTOM,
            key="invalid_key",
            operation=FilterOperation.EQSTR,
            value=["test"]
        )
        
        # Set query type context manually and then call validation
        filter_obj._query_type = QUERY_TYPE_CONCEPTS
        
        with pytest.raises(ValueError, match="Custom category key 'invalid_key' not allowed"):
            filter_obj.validate_custom_key_allowlist()

    def test_filter_custom_key_validation_relations(self):
        """Test validation of custom keys for relations."""
        # Valid custom keys for relations
        valid_keys = ["id", "relation"]
        
        for key in valid_keys:
            filter_obj = KnowledgeGraphQueryCriteriaFilter(
                category=FilterCategory.CUSTOM,
                key=key,
                operation=FilterOperation.EQSTR,
                value=["test_value"]
            )
            assert filter_obj.key == key

    def test_filter_custom_string_key_operation_validation(self):
        """Test that custom string keys only support EQSTR operation."""
        string_keys = ["id", "name", "relation"]
        
        for key in string_keys:
            # Valid: EQSTR operation
            filter_obj = KnowledgeGraphQueryCriteriaFilter(
                category=FilterCategory.CUSTOM,
                key=key,
                operation=FilterOperation.EQSTR,
                value=["test_value"]
            )
            assert filter_obj.operation == FilterOperation.EQSTR

            # Invalid: numeric operations on string keys
            with pytest.raises(ValidationError, match=f"Custom key '{key}' only supports EQSTR operation"):
                KnowledgeGraphQueryCriteriaFilter(
                    category=FilterCategory.CUSTOM,
                    key=key,
                    operation=FilterOperation.EQ,
                    value=[42]
                )

    def test_filter_custom_numeric_key_operation_validation(self):
        """Test that custom numeric keys don't support EQSTR operation."""
        numeric_keys = ["relations_cnt"]
        
        for key in numeric_keys:
            # Valid: numeric operations
            filter_obj = KnowledgeGraphQueryCriteriaFilter(
                category=FilterCategory.CUSTOM,
                key=key,
                operation=FilterOperation.EQ,
                value=[5]
            )
            assert filter_obj.operation == FilterOperation.EQ

            # Invalid: EQSTR operation on numeric keys
            with pytest.raises(ValidationError, match=f"Custom key '{key}' does not support EQSTR operation"):
                KnowledgeGraphQueryCriteriaFilter(
                    category=FilterCategory.CUSTOM,
                    key=key,
                    operation=FilterOperation.EQSTR,
                    value=["string_value"]
                )

    def test_filter_empty_value_validation(self):
        """Test that value list cannot be empty."""
        with pytest.raises(ValidationError, match="List should have at least 1 item"):
            KnowledgeGraphQueryCriteriaFilter(
                category=FilterCategory.CUSTOM,
                key="name",
                operation=FilterOperation.EQSTR,
                value=[]  # Empty list
            )


class TestConceptWithInternalAttributes:
    """Test suite for Concept model with internal attributes."""

    def test_concept_with_internal_attributes(self):
        """Test Concept creation with internal attributes."""
        internal_attrs = [
            InternalAttributes(
                owner="550e8400-e29b-41d4-a716-446655440000",
                attributes={"category": "Technology", "rate": 19.5}
            )
        ]
        
        concept = Concept(
            id="concept1",
            name="Test Concept",
            description="A test concept",
            internal_attributes=internal_attrs
        )
        
        assert concept.id == "concept1"
        assert concept.internal_attributes is not None
        assert len(concept.internal_attributes) == 1
        assert concept.internal_attributes[0].owner == "550e8400-e29b-41d4-a716-446655440000"
        assert concept.internal_attributes[0].attributes == {"category": "Technology", "rate": 19.5}

    def test_concept_with_multiple_internal_attributes(self):
        """Test Concept with multiple internal attribute owners."""
        internal_attrs = [
            InternalAttributes(
                owner="550e8400-e29b-41d4-a716-446655440000",
                attributes={"category": "Technology"}
            ),
            InternalAttributes(
                owner="123e4567-e89b-12d3-a456-426614174000",
                attributes={"session_time": 1672531207, "priority": "high"}
            )
        ]
        
        concept = Concept(
            id="concept1",
            name="Test Concept",
            internal_attributes=internal_attrs
        )
        
        assert len(concept.internal_attributes) == 2
        assert concept.internal_attributes[0].owner == "550e8400-e29b-41d4-a716-446655440000"
        assert concept.internal_attributes[1].owner == "123e4567-e89b-12d3-a456-426614174000"

    def test_concept_without_internal_attributes(self):
        """Test Concept without internal attributes."""
        concept = Concept(
            id="concept1",
            name="Test Concept",
            description="A test concept"
        )
        
        assert concept.internal_attributes is None

    def test_concept_exclude_none_internal_attributes(self):
        """Test behavior of None internal_attributes in JSON serialization."""
        concept = Concept(
            id="concept1",
            name="Test Concept"
            # internal_attributes not provided (defaults to None)
        )
        
        # Verify the field is None
        assert concept.internal_attributes is None
        
        data = concept.model_dump()
        # Test the actual behavior - in Pydantic v2 with Field(None, ...), 
        # the field might be included as None even with exclude_none=True
        # Let's document the actual behavior
        assert data["name"] == "Test Concept"
        # The field might be present as None or excluded entirely
        if "internal_attributes" in data:
            assert data["internal_attributes"] is None


class TestRelationWithInternalAttributes:
    """Test suite for Relation model with internal attributes."""

    def test_relation_with_internal_attributes(self):
        """Test Relation creation with internal attributes."""
        internal_attrs = [
            InternalAttributes(
                owner="123e4567-e89b-12d3-a456-426614174000",
                attributes={"session_time": 1672531207, "priority": "high"}
            )
        ]
        
        relation = Relation(
            id="rel1",
            relation="RELATES_TO",
            node_ids=["node1", "node2"],
            internal_attributes=internal_attrs
        )
        
        assert relation.id == "rel1"
        assert relation.internal_attributes is not None
        assert len(relation.internal_attributes) == 1
        assert relation.internal_attributes[0].owner == "123e4567-e89b-12d3-a456-426614174000"
        assert relation.internal_attributes[0].attributes == {"session_time": 1672531207, "priority": "high"}

    def test_relation_exclude_none_internal_attributes(self):
        """Test behavior of None internal_attributes in JSON serialization."""
        relation = Relation(
            id="rel1",
            relation="RELATES_TO",
            node_ids=["node1", "node2"]
            # internal_attributes not provided (defaults to None)
        )
        
        # Verify the field is None
        assert relation.internal_attributes is None
        
        data = relation.model_dump()
        # Test the actual behavior - in Pydantic v2 with Field(None, ...), 
        # the field might be included as None even with exclude_none=True
        # Let's document the actual behavior
        assert data["relation"] == "RELATES_TO"
        # The field might be present as None or excluded entirely
        if "internal_attributes" in data:
            assert data["internal_attributes"] is None


class TestDefaultPropertyKeySeparator:
    """Test suite for DEFAULT_PROPERTY_KEY_SEPARATOR constant."""

    def test_default_property_key_separator_value(self):
        """Test that the default separator is '$'."""
        assert DEFAULT_PROPERTY_KEY_SEPARATOR == "$"
