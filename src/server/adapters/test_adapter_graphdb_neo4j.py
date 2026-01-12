import pytest
from unittest.mock import patch, MagicMock
from server.adapters.adapter_graphdb_neo4j import Adapter_GraphDB_Neo4j
from server.database.graph_db.neo4j.models.node import Node
from server.database.graph_db.neo4j.models.edge import Edge
from server.adapters.adapter_graphdb_neo4j import MAS_LABEL_PREFIX, WKSP_LABEL_PREFIX, MEM_TYPE_LABEL_PREFIX


class TestAdapterGraphDBNeo4j:
    """Test suite for Adapter_GraphDB_Neo4j class."""

    @pytest.fixture
    def adapter(self):
        """Fixture to create a fresh adapter instance for each test."""
        return Adapter_GraphDB_Neo4j()

    def test_convert_to_models_empty_input(self, adapter):
        """Test convert_to_models with empty input data."""
        with pytest.raises(ValueError, match="Input data must contain 'records' key"):
            adapter.convert_to_models({})

    def test_convert_to_models_invalid_records_type(self, adapter):
        """Test convert_to_models with invalid records type."""
        with pytest.raises(ValueError, match="'records' must be a dictionary"):
            adapter.convert_to_models({"records": "not_a_dict"})

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
            assert MAS_LABEL_PREFIX not in node.labels, "mas_id value should not be in node labels"

        # Check edges
        for edge in edges:
            assert "mas_id" not in edge.properties, "mas_id key should not be in edge properties"

    def test_convert_models_to_query_response_records(self, adapter):
        """Test convert_models_to_query_response_records with various scenarios."""
        # Test data with node, relationships, and neighbors
        test_data = [
            {
                "node": {
                    "id": "1",
                    "name": "Test Node",
                    "description": "Test Description",
                    "embedding_vector": [0.1, 0.2, 0.3],
                    "embedding_model": "test-model-1",
                    "custom_attr": "value1",
                },
                "relationships": [
                    {
                        "id": "r1",
                        "relation": "RELATED_TO",
                        "node_ids": ["1", "2"],
                        "embedding_vector": [0.4, 0.5, 0.6],
                        "embedding_model": "test-model-2",
                        "custom_rel_attr": "rel_value1",
                    }
                ],
                "neighbors": [
                    {"id": "2", "name": "Neighbor Node", "description": "Neighbor Description", "custom_attr": "value2"}
                ],
            }
        ]

        # Call the method
        result = adapter.convert_models_to_query_response_records(test_data)

        # Verify the result structure
        assert len(result) == 1
        record = result[0]

        # Check queried concept
        assert record.queried_concept is not None
        assert record.queried_concept.id == "1"
        assert record.queried_concept.name == "Test Node"
        assert record.queried_concept.embeddings is not None
        assert record.queried_concept.embeddings.data == [0.1, 0.2, 0.3]
        assert record.queried_concept.embeddings.name == "test-model-1"
        assert record.queried_concept.attributes == {"custom_attr": "value1"}

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
                "node": {"id": "1", "name": "Test Node", "description": "Test Description", "custom_attr": "value1"},
                "relationships": [
                    {"id": "r1", "relation": "RELATED_TO", "node_ids": ["1", "2"], "custom_rel_attr": "rel_value1"}
                ],
                "neighbors": [],
            }
        ]

        result = adapter.convert_models_to_query_response_records(test_data)
        record = result[0]

        # Check that embeddings is None when not provided
        assert record.queried_concept.embeddings is None
        assert record.relationships[0].embeddings is None

    def test_convert_models_to_query_response_records_empty_input(self, adapter):
        """Test convert_models_to_query_response_records with empty input."""
        result = adapter.convert_models_to_query_response_records([])
        assert result == []

    def test_convert_models_to_query_response_records_missing_node(self, adapter):
        """Test convert_models_to_query_response_records with missing node data."""
        test_data = [{"relationships": [], "neighbors": []}]
        result = adapter.convert_models_to_query_response_records(test_data)
        assert result[0].queried_concept is None

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
            f"{MAS_LABEL_PREFIX}test_mas",
            f"{WKSP_LABEL_PREFIX}test_wksp",
            f"{MEM_TYPE_LABEL_PREFIX}test_memory",
            "tag1",
            "tag2",
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
                        "attributes": {"strength": 0.8}
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
                        "relation": "RELATED_TO"
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
            f"{MAS_LABEL_PREFIX}test_mas",
            f"{WKSP_LABEL_PREFIX}test_wksp",
            f"{MEM_TYPE_LABEL_PREFIX}test_memory",
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
        assert set(node.properties.keys()) == {"name", "description", "embedding_vector", "embedding_model", "mas_id"}

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
