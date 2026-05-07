# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from server.adapters.adapter_graphdb_agensgraph import AdapterGraphdbAgensgraph


class TestAdapterGraphdbAgensgraph:
    """Test suite for AdapterGraphdbAgensgraph class."""

    @pytest.fixture
    def adapter(self):
        """Fixture to create a fresh adapter instance for each test."""
        return AdapterGraphdbAgensgraph()

    def test_convert_to_models_with_missing_mas_id(self, adapter):
        """Test convert_to_models with missing mas_id."""
        test_data = {
            "wksp_id": "test_wksp",
            "memory_type": "Semantic",
            "records": {
                "concepts": [{"id": "c1", "name": "Concept 1"}],
                "relations": [{"id": "r1", "relation": "REL", "node_ids": ["c1", "c2"]}],
            },
        }
        nodes, edges = adapter.convert_to_models(test_data)

        # Check nodes
        for node in nodes:
            assert "mas_id" not in node.properties, "mas_id key should not be in node properties"

        # Check edges
        for edge in edges:
            assert "mas_id" not in edge.properties, "mas_id key should not be in edge properties"

    def test_convert_models_to_query_response_records(self, adapter):
        """Test convert_models_to_query_response_records with various scenarios."""
        # Test data with node, relationships, and neighbors
        test_data = [
            {
                "edges": [
                    {
                        "id": "r1",
                        "relation": "RELATED_TO",
                        "node_ids": ["1", "2"],
                        "embedding_vector": [0.4, 0.5, 0.6],
                        "embedding_model": "test-model-2",
                        "custom_rel_attr": "rel_value1",
                    }
                ],
                "nodes": [
                    {"id": "2", "name": "Neighbor Node", "description": "Neighbor Description", "custom_attr": "value2"}
                ],
            }
        ]

        # Call the method
        result = adapter.convert_models_to_query_response_records(test_data)

        # Verify the result structure
        assert len(result) == 1
        record = result[0]

        # Check relationships
        assert len(record.relationships) == 1
        rel = record.relationships[0]
        assert rel.id == "r1"
        assert rel.relation == "RELATED_TO"
        assert rel.embeddings is not None
        assert rel.embeddings.data == [0.4, 0.5, 0.6]
        assert rel.embeddings.name == "test-model-2"
        assert rel.attributes == {"custom_rel_attr": "rel_value1"}

        # Check neighbors
        assert len(record.concepts) == 1
        neighbor = record.concepts[0]
        assert neighbor.id == "2"
        assert neighbor.name == "Neighbor Node"
        assert neighbor.embeddings is None  # No embeddings provided for neighbor
        assert neighbor.attributes == {"custom_attr": "value2"}

    def test_convert_models_to_query_response_records_empty_embeddings(self, adapter):
        """Test convert_models_to_query_response_records with nodes without embeddings."""
        test_data = [
            {
                "nodes": [{"id": "1", "name": "Test Node", "description": "Test Description", "custom_attr": "value1"}],
                "edges": [
                    {"id": "r1", "relation": "RELATED_TO", "node_ids": ["1", "2"], "custom_rel_attr": "rel_value1"}
                ],
            }
        ]

        result = adapter.convert_models_to_query_response_records(test_data)
        record = result[0]

        # Check that embeddings is None when not provided
        assert record.relationships[0].embeddings is None

    def test_convert_models_to_query_response_records_empty_input(self, adapter):
        """Test convert_models_to_query_response_records with empty input."""
        result = adapter.convert_models_to_query_response_records([])
        assert result == []

    def test_convert_models_to_query_response_records_missing_node(self, adapter):
        """Test convert_models_to_query_response_records with missing node data."""
        test_data = [{"relationships": [], "neighbors": []}]
        result = adapter.convert_models_to_query_response_records(test_data)
        # The method returns a KnowledgeGraphQueryResponseRecord with empty relationships and concepts
        # when node data is missing
        assert len(result) == 1
        record = result[0]
        assert record.relationships == []
        assert record.concepts == []

    def test_convert_to_models_with_concepts(self, adapter):
        """Test convert_to_models with concept data."""
        test_data = {
            "mas_id": "test_mas",
            "wksp_id": "test_wksp",
            "memory_type": "test_memory",
            "records": {
                "concepts": [
                    {
                        "id": "concept1",
                        "name": "Test Concept",
                        "description": "A test concept",
                        "tags": ["tag1", "tag2"],
                        "attributes": {"key1": "value1"},
                        "embeddings": {"data": [0.1, 0.2, 0.3], "name": "test_model"},
                    }
                ]
            },
        }

        nodes, edges = adapter.convert_to_models(test_data)

        assert len(nodes) == 1
        assert len(edges) == 0

        node = nodes[0]
        assert node.id == "concept1"
        assert set(node.labels) == {
            "Concept",
        }
        assert node.properties["name"] == "Test Concept"
        assert node.properties["description"] == "A test concept"
        assert node.properties["key1"] == "value1"
        assert node.properties["embedding_vector"] == [0.1, 0.2, 0.3]
        assert node.properties["embedding_model"] == "test_model"

    def test_convert_to_models_with_relations(self, adapter):
        """Test convert_to_models with relation data."""
        test_data = {
            "mas_id": "test_mas",
            "wksp_id": "test_wksp",
            "memory_type": "test_memory",
            "records": {
                "relations": [
                    {
                        "id": "rel1",
                        "node_ids": ["node1", "node2"],
                        "relation": "RELATED_TO",
                        "attributes": {"strength": 0.8},
                        "embeddings": {"data": [0.4, 0.5, 0.6], "name": "rel_model"},
                    }
                ]
            },
        }

        nodes, edges = adapter.convert_to_models(test_data)

        assert len(nodes) == 0
        assert len(edges) == 1

        edge = edges[0]
        assert edge.id == "rel1"
        assert edge.node_ids == ["node1", "node2"]
        assert edge.relation == "RELATED_TO"
        assert edge.properties["node_ids"] == ["node1", "node2"]
        assert edge.properties["strength"] == 0.8
        assert edge.properties["embedding_vector"] == [0.4, 0.5, 0.6]
        assert edge.properties["embedding_model"] == "rel_model"
        assert edge.properties["mas_id"] == "test_mas"
        assert edge.properties["wksp_id"] == "test_wksp"
        assert edge.properties["memory_type"] == "test_memory"

    def test_convert_to_models_with_relations_no_embeddings(self, adapter):
        """Test convert_to_models with relation data that has no embeddings."""
        test_data = {
            "mas_id": "test_mas",
            "wksp_id": "test_wksp",
            "memory_type": "test_memory",
            "records": {
                "relations": [
                    {
                        "id": "rel1",
                        "node_ids": ["node1", "node2"],
                        "relation": "RELATED_TO",
                        "attributes": {"strength": 0.8},
                        # No embeddings
                    }
                ]
            },
        }

        nodes, edges = adapter.convert_to_models(test_data)

        assert len(edges) == 1
        edge = edges[0]
        assert "embedding_vector" not in edge.properties
        assert "embedding_model" not in edge.properties

    def test_convert_to_models_with_relations_no_attributes(self, adapter):
        """Test convert_to_models with relation data that has no attributes."""
        test_data = {
            "mas_id": "test_mas",
            "wksp_id": "test_wksp",
            "memory_type": "test_memory",
            "records": {
                "relations": [
                    {
                        "id": "rel1",
                        "node_ids": ["node1", "node2"],
                        "relation": "RELATED_TO",
                        # No attributes
                    }
                ]
            },
        }

        nodes, edges = adapter.convert_to_models(test_data)

        assert len(edges) == 1
        edge = edges[0]
        # Should only have node_ids and metadata in properties
        assert set(edge.properties.keys()) == {"node_ids", "mas_id", "wksp_id", "memory_type", "relation"}

    def test_convert_to_models_with_concepts_no_tags(self, adapter):
        """Test convert_to_models with concept data that has no tags."""
        test_data = {
            "mas_id": "test_mas",
            "wksp_id": "test_wksp",
            "memory_type": "test_memory",
            "records": {
                "concepts": [
                    {
                        "id": "concept1",
                        "name": "Test Concept",
                        "description": "A test concept",
                        "attributes": {"key1": "value1"},
                        "embeddings": {"data": [0.1, 0.2, 0.3], "name": "test_model"},
                    }
                ]
            },
        }

        nodes, _ = adapter.convert_to_models(test_data)
        node = nodes[0]

        # Should only have the default and metadata labels, no tag labels
        assert set(node.labels) == {
            "Concept",
        }

    def test_convert_to_models_with_concepts_no_attributes(self, adapter):
        """Test convert_to_models with concept data that has no attributes."""
        test_data = {
            "mas_id": "test_mas",
            "records": {
                "concepts": [
                    {
                        "id": "concept1",
                        "name": "Test Concept",
                        "description": "A test concept",
                        "tags": ["tag1"],
                        "embeddings": {"data": [0.1, 0.2, 0.3], "name": "test_model"},
                    }
                ]
            },
        }

        nodes, _ = adapter.convert_to_models(test_data)
        node = nodes[0]

        # Should have default properties and embeddings, but no additional attributes
        assert set(node.properties.keys()) == {
            "name",
            "description",
            "embedding_vector",
            "embedding_model",
            "mas_id",
            "tags",
        }

    def test_convert_to_models_with_concepts_no_embeddings(self, adapter):
        """Test convert_to_models with concept data that has no embeddings."""
        test_data = {
            "records": {
                "concepts": [
                    {
                        "id": "concept1",
                        "name": "Test Concept",
                        "description": "A test concept",
                        "tags": ["tag1"],
                        "attributes": {"key1": "value1"},
                    }
                ]
            }
        }

        nodes, _ = adapter.convert_to_models(test_data)
        node = nodes[0]

        # Should not have any embedding-related properties
        assert "embedding_vector" not in node.properties
        assert "embedding_model" not in node.properties

    def test_process_embeddings(self, adapter):
        """Test _process_embeddings method."""
        properties = {}
        embedding_data = {"data": [1.0, 2.0, 3.0], "name": "test_model"}

        adapter._process_embeddings(embedding_data, properties)

        assert properties["embedding_vector"] == [1.0, 2.0, 3.0]
        assert properties["embedding_model"] == "test_model"

    def test_process_internal_attributes_basic(self, adapter):
        """Test _process_internal_attributes method with basic input."""
        internal_attributes = {
            "owner": "550e8400-e29b-41d4-a716-446655440000",
            "attributes": {"category": "Technology", "rate": 19.5}
        }
        
        result = adapter._process_internal_attributes(internal_attributes)
        
        expected = {
            "550e8400-e29b-41d4-a716-446655440000$category": "Technology",
            "550e8400-e29b-41d4-a716-446655440000$rate": 19.5
        }
        assert result == expected

    def test_process_internal_attributes_empty_owner(self, adapter):
        """Test _process_internal_attributes method with empty owner."""
        internal_attributes = {
            "owner": "",
            "attributes": {"category": "Technology"}
        }
        
        result = adapter._process_internal_attributes(internal_attributes)
        assert result == {}

    def test_process_internal_attributes_no_attributes(self, adapter):
        """Test _process_internal_attributes method with no attributes."""
        internal_attributes = {
            "owner": "550e8400-e29b-41d4-a716-446655440000",
            "attributes": {}
        }
        
        result = adapter._process_internal_attributes(internal_attributes)
        assert result == {}

    def test_process_internal_attributes_empty_input(self, adapter):
        """Test _process_internal_attributes method with empty input."""
        result = adapter._process_internal_attributes({})
        assert result == {}

    def test_process_internal_attributes_none_input(self, adapter):
        """Test _process_internal_attributes method with None input."""
        result = adapter._process_internal_attributes(None)
        assert result == {}

    def test_extract_internal_attributes_from_properties_basic(self, adapter):
        """Test _extract_internal_attributes_from_properties method with basic input."""
        properties = {
            "name": "Test Node",
            "550e8400-e29b-41d4-a716-446655440000$category": "Technology",
            "550e8400-e29b-41d4-a716-446655440000$rate": 19.5,
            "regular_attribute": "value"
        }
        
        result = adapter._extract_internal_attributes_from_properties(properties)
        
        assert result is not None
        assert len(result) == 1
        assert result[0]["owner"] == "550e8400-e29b-41d4-a716-446655440000"
        assert result[0]["attributes"] == {"category": "Technology", "rate": 19.5}

    def test_extract_internal_attributes_from_properties_multiple_owners(self, adapter):
        """Test _extract_internal_attributes_from_properties method with multiple owners."""
        properties = {
            "name": "Test Node",
            "550e8400-e29b-41d4-a716-446655440000$category": "Technology",
            "550e8400-e29b-41d4-a716-446655440000$rate": 19.5,
            "123e4567-e89b-12d3-a456-426614174000$session_time": 1672531207,
            "123e4567-e89b-12d3-a456-426614174000$priority": "high",
            "regular_attribute": "value"
        }
        
        result = adapter._extract_internal_attributes_from_properties(properties)
        
        assert result is not None
        assert len(result) == 2
        
        # Sort by owner for consistent testing
        result_sorted = sorted(result, key=lambda x: x["owner"])
        
        assert result_sorted[0]["owner"] == "123e4567-e89b-12d3-a456-426614174000"
        assert result_sorted[0]["attributes"] == {"session_time": 1672531207, "priority": "high"}
        
        assert result_sorted[1]["owner"] == "550e8400-e29b-41d4-a716-446655440000"
        assert result_sorted[1]["attributes"] == {"category": "Technology", "rate": 19.5}

    def test_extract_internal_attributes_from_properties_no_internal_attrs(self, adapter):
        """Test _extract_internal_attributes_from_properties method with no internal attributes."""
        properties = {
            "name": "Test Node",
            "regular_attribute": "value",
            "another_attr": 42
        }
        
        result = adapter._extract_internal_attributes_from_properties(properties)
        assert result is None

    def test_extract_internal_attributes_from_properties_empty_properties(self, adapter):
        """Test _extract_internal_attributes_from_properties method with empty properties."""
        result = adapter._extract_internal_attributes_from_properties({})
        assert result is None

    def test_convert_to_models_with_internal_attributes_concepts(self, adapter):
        """Test convert_to_models with concept data containing internal attributes."""
        test_data = {
            "mas_id": "test_mas",
            "wksp_id": "test_wksp",
            "memory_type": "test_memory",
            "records": {
                "concepts": [
                    {
                        "id": "concept1",
                        "name": "Test Concept",
                        "description": "A test concept",
                        "attributes": {"key1": "value1"},
                        "internal_attributes": [
                            {
                                "owner": "550e8400-e29b-41d4-a716-446655440000",
                                "attributes": {"category": "Technology", "rate": 19.5}
                            }
                        ]
                    }
                ]
            },
        }

        nodes, edges = adapter.convert_to_models(test_data)

        assert len(nodes) == 1
        node = nodes[0]
        
        # Check that internal attributes are converted to prefixed property keys
        assert "550e8400-e29b-41d4-a716-446655440000$category" in node.properties
        assert "550e8400-e29b-41d4-a716-446655440000$rate" in node.properties
        assert node.properties["550e8400-e29b-41d4-a716-446655440000$category"] == "Technology"
        assert node.properties["550e8400-e29b-41d4-a716-446655440000$rate"] == 19.5
        
        # Check regular attributes are still present
        assert node.properties["key1"] == "value1"

    def test_convert_to_models_with_internal_attributes_relations(self, adapter):
        """Test convert_to_models with relation data containing internal attributes."""
        test_data = {
            "mas_id": "test_mas",
            "wksp_id": "test_wksp", 
            "memory_type": "test_memory",
            "records": {
                "relations": [
                    {
                        "id": "rel1",
                        "node_ids": ["node1", "node2"],
                        "relation": "RELATED_TO",
                        "attributes": {"strength": 0.8},
                        "internal_attributes": [
                            {
                                "owner": "123e4567-e89b-12d3-a456-426614174000",
                                "attributes": {"session_time": 1672531207, "priority": "high"}
                            }
                        ]
                    }
                ]
            },
        }

        nodes, edges = adapter.convert_to_models(test_data)

        assert len(edges) == 1
        edge = edges[0]
        
        # Check that internal attributes are converted to prefixed property keys
        assert "123e4567-e89b-12d3-a456-426614174000$session_time" in edge.properties
        assert "123e4567-e89b-12d3-a456-426614174000$priority" in edge.properties
        assert edge.properties["123e4567-e89b-12d3-a456-426614174000$session_time"] == 1672531207
        assert edge.properties["123e4567-e89b-12d3-a456-426614174000$priority"] == "high"
        
        # Check regular attributes are still present
        assert edge.properties["strength"] == 0.8

    def test_convert_to_models_with_multiple_internal_attributes(self, adapter):
        """Test convert_to_models with multiple internal attribute owners."""
        test_data = {
            "mas_id": "test_mas",
            "records": {
                "concepts": [
                    {
                        "id": "concept1",
                        "name": "Test Concept",
                        "internal_attributes": [
                            {
                                "owner": "550e8400-e29b-41d4-a716-446655440000",
                                "attributes": {"category": "Technology"}
                            },
                            {
                                "owner": "123e4567-e89b-12d3-a456-426614174000", 
                                "attributes": {"session_time": 1672531207}
                            }
                        ]
                    }
                ]
            },
        }

        nodes, edges = adapter.convert_to_models(test_data)

        assert len(nodes) == 1
        node = nodes[0]
        
        # Check both owners' attributes are present
        assert "550e8400-e29b-41d4-a716-446655440000$category" in node.properties
        assert "123e4567-e89b-12d3-a456-426614174000$session_time" in node.properties
        assert node.properties["550e8400-e29b-41d4-a716-446655440000$category"] == "Technology"
        assert node.properties["123e4567-e89b-12d3-a456-426614174000$session_time"] == 1672531207

    def test_convert_models_to_query_response_records_with_internal_attributes(self, adapter):
        """Test convert_models_to_query_response_records extracts internal attributes correctly."""
        test_data = [
            {
                "nodes": [
                    {
                        "id": "1",
                        "name": "Test Node",
                        "550e8400-e29b-41d4-a716-446655440000$category": "Technology",
                        "550e8400-e29b-41d4-a716-446655440000$rate": 19.5,
                        "regular_attr": "value"
                    }
                ],
                "edges": [
                    {
                        "id": "r1",
                        "relation": "RELATED_TO",
                        "node_ids": ["1", "2"],
                        "123e4567-e89b-12d3-a456-426614174000$session_time": 1672531207,
                        "123e4567-e89b-12d3-a456-426614174000$priority": "high",
                        "strength": 0.8
                    }
                ]
            }
        ]

        result = adapter.convert_models_to_query_response_records(test_data)
        
        assert len(result) == 1
        record = result[0]
        
        # Check concept internal attributes
        assert len(record.concepts) == 1
        concept = record.concepts[0]
        assert concept.internal_attributes is not None
        assert len(concept.internal_attributes) == 1
        assert concept.internal_attributes[0].owner == "550e8400-e29b-41d4-a716-446655440000"
        assert concept.internal_attributes[0].attributes == {"category": "Technology", "rate": 19.5}
        assert concept.attributes == {"regular_attr": "value"}
        
        # Check relation internal attributes
        assert len(record.relationships) == 1
        relation = record.relationships[0]
        assert relation.internal_attributes is not None
        assert len(relation.internal_attributes) == 1
        assert relation.internal_attributes[0].owner == "123e4567-e89b-12d3-a456-426614174000"
        assert relation.internal_attributes[0].attributes == {"session_time": 1672531207, "priority": "high"}
        assert relation.attributes == {"strength": 0.8}

    def test_convert_models_to_query_response_records_multiple_internal_owners(self, adapter):
        """Test convert_models_to_query_response_records with multiple internal attribute owners."""
        test_data = [
            {
                "nodes": [
                    {
                        "id": "1",
                        "name": "Test Node",
                        "550e8400-e29b-41d4-a716-446655440000$category": "Technology",
                        "123e4567-e89b-12d3-a456-426614174000$session_time": 1672531207,
                        "123e4567-e89b-12d3-a456-426614174000$priority": "high"
                    }
                ]
            }
        ]

        result = adapter.convert_models_to_query_response_records(test_data)
        
        concept = result[0].concepts[0]
        assert concept.internal_attributes is not None
        assert len(concept.internal_attributes) == 2
        
        # Sort by owner for consistent testing
        internal_attrs_sorted = sorted(concept.internal_attributes, key=lambda x: x.owner)
        
        assert internal_attrs_sorted[0].owner == "123e4567-e89b-12d3-a456-426614174000"
        assert internal_attrs_sorted[0].attributes == {"session_time": 1672531207, "priority": "high"}
        
        assert internal_attrs_sorted[1].owner == "550e8400-e29b-41d4-a716-446655440000"
        assert internal_attrs_sorted[1].attributes == {"category": "Technology"}

    def test_convert_models_to_query_response_records_no_internal_attributes(self, adapter):
        """Test convert_models_to_query_response_records with no internal attributes."""
        test_data = [
            {
                "nodes": [
                    {
                        "id": "1",
                        "name": "Test Node",
                        "regular_attr": "value"
                    }
                ],
                "edges": [
                    {
                        "id": "r1",
                        "relation": "RELATED_TO",
                        "node_ids": ["1", "2"],
                        "strength": 0.8
                    }
                ]
            }
        ]

        result = adapter.convert_models_to_query_response_records(test_data)
        
        concept = result[0].concepts[0]
        relation = result[0].relationships[0]
        
        # Should be None when no internal attributes
        assert concept.internal_attributes is None
        assert relation.internal_attributes is None
        
        # Regular attributes should still be present
        assert concept.attributes == {"regular_attr": "value"}
        assert relation.attributes == {"strength": 0.8}

    def test_property_key_separator_exclusion_in_attributes(self, adapter):
        """Test that properties with separator are excluded from regular attributes."""
        test_data = [
            {
                "nodes": [
                    {
                        "id": "1",
                        "name": "Test Node",
                        "550e8400-e29b-41d4-a716-446655440000$category": "Technology",  # Should be excluded
                        "regular_attr": "value",  # Should be included
                        "123e4567-e89b-12d3-a456-426614174000$key": "should_be_excluded"  # Should be excluded
                    }
                ]
            }
        ]

        result = adapter.convert_models_to_query_response_records(test_data)
        
        concept = result[0].concepts[0]
        
        # Only regular attributes without separator should be in attributes
        assert concept.attributes == {"regular_attr": "value"}
        
        # Internal attributes should be extracted separately
        assert concept.internal_attributes is not None
        assert len(concept.internal_attributes) == 2  # Two different owners
