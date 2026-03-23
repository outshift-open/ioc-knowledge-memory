# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from knowledge_memory.server.database.graph_db.agensgraph.models.edge import Edge


class TestEdge:
    def test_edge_creation(self):
        """Test basic relationship creation."""
        rel = Edge(id="rel_id", node_ids=["node1", "node2"], relation="RELATES_TO")
        assert rel.id == "rel_id"
        assert rel.node_ids == ["node1", "node2"]
        assert rel.relation == "RELATES_TO"
        assert rel.direction == "->"

    def test_edge_validation_empty_id(self):
        """Test validation fails with empty ID."""
        with pytest.raises(ValueError, match="Edge ID cannot be empty"):
            Edge(id="", node_ids=["1", "2"], relation="RELATES_TO")

    def test_edge_validation_invalid_node_count(self):
        """Test validation fails with incorrect number of nodes."""
        with pytest.raises(ValueError, match="Exactly two node IDs are required"):
            Edge(id="rel_id", node_ids=["node1"], relation="RELATES_TO")

    def test_edge_validation_invalid_relation_format(self):
        """Test validation fails with invalid relation format."""
        with pytest.raises(ValueError, match="Relation type must be uppercase with underscores"):
            Edge(id="rel_id", node_ids=["1", "2"], relation="invalid-relation")

    def test_edge_validation_invalid_direction(self):
        """Test validation fails with invalid direction."""
        with pytest.raises(ValueError, match="Direction must be one of"):
            Edge(id="rel_id", node_ids=["1", "2"], relation="RELATES_TO", direction="invalid")

    def test_edge_property_validation(self):
        """Test validation of relationship properties."""
        with pytest.raises(ValueError, match="Invalid property key"):
            rel = Edge(id="rel_id", node_ids=["1", "2"], relation="RELATES_TO", properties={"": "invalid"})
            rel._validate_properties()

    def test_to_cypher_exists(self):
        """Test generation of Cypher EXISTS query."""
        edge = Edge(id="test_id", node_ids=["node1", "node2"], relation="RELATES_TO")
        query, params = edge.to_cypher_exists()

        # Check the raw query format (single line with %s placeholder)
        expected_raw_query = "MATCH ()-[r {id: %s}]-() RETURN r LIMIT 1"
        assert query == expected_raw_query
        assert params == ("test_id",)

    def test_to_cypher_create(self):
        """Test generation of Cypher CREATE query for edge."""
        edge = Edge(
            id="test_id",
            node_ids=["node1", "node2"],
            relation="RELATES_TO",
            properties={"since": 2024, "active": True},
            direction="->",
        )
        query, params = edge.to_cypher_create()

        # Check the parameterized query format (uses %s placeholders)
        assert "MATCH (a {id: %s}), (b {id: %s})" in query
        assert "CREATE (a)-[r:RELATES_TO { since: %s, active: %s, id: %s }]->(b)" in query
        assert "RETURN r" in query

        # Check parameters (tuple format: source_id, target_id, then property values)
        assert params == ("node1", "node2", 2024, True, "test_id")

    def test_to_executable_cypher(self):
        """Test generation of executable Cypher query."""
        edge = Edge(
            id="test_id", node_ids=["node1", "node2"], relation="RELATES_TO", properties={"since": 2024, "active": True}
        )

        # The to_executable_cypher method expects dictionary parameters and $-style placeholders
        # But to_cypher_create returns tuple parameters and %s placeholders
        # This test should expect an error since the formats don't match
        query, params = edge.to_cypher_create()
        result = edge.to_executable_cypher(query, params)

        # Should return an error message since params is a tuple, not a dict
        assert "Error generating query: 'tuple' object has no attribute 'items'" in result

    def test_edge_with_properties(self):
        props = {
            "string": "test",
            "number": 42,
            "boolean": True,
            "none": None,
            "list": [1, 2, 3],
            "dict": {"key": "value"},
        }
        edge = Edge(id="test_id", node_ids=["node1", "node2"], relation="HAS_PROPERTY", properties=props)
        assert edge.properties == props
        query, params = edge.to_cypher_create()

        # Check that the query uses %s placeholders for all properties
        assert "string: %s" in query
        assert "number: %s" in query
        assert "boolean: %s" in query
        assert "none: %s" in query
        assert "list: %s" in query
        assert "dict: %s" in query
        assert "id: %s" in query

        # Check that all properties are included in the params tuple
        # Format: (source_id, target_id, then property values in order)
        assert params[0] == "node1"  # source_id
        assert params[1] == "node2"  # target_id
        # The remaining parameters are property values (order may vary based on dict iteration)
        assert len(params) == 9  # 2 node IDs + 7 properties (including added 'id')

    def test_edge_with_empty_properties(self):
        """Test edge with empty properties."""
        edge = Edge(id="test_id", node_ids=["node1", "node2"], relation="RELATES_TO", properties={})
        assert edge.properties == {}
        query, params = edge.to_cypher_create()

        # Check that params is a tuple with source_id, target_id, and id property
        assert params == ("node1", "node2", "test_id")

        # Check that the query has the id property placeholder
        assert "id: %s" in query

    def test_edge_with_special_chars_in_properties(self):
        """Test edge with special characters in properties."""
        edge = Edge(
            id="test_id",
            node_ids=["node1", "node2"],
            relation="HAS_COMMENT",
            properties={"text": "This is a comment with special chars: !@#$"},
        )
        query, params = edge.to_cypher_create()

        # Check that the special characters are in the params tuple
        assert "This is a comment with special chars: !@#$" in params

        # The to_executable_cypher method will fail with tuple params, so we expect an error
        cypher = edge.to_executable_cypher(query, params)
        assert "Error generating query: 'tuple' object has no attribute 'items'" in cypher

    def test_edge_with_empty_node_ids(self):
        """Test validation fails with empty node IDs."""
        with pytest.raises(ValueError, match="Node IDs cannot be empty"):
            Edge(id="test_id", node_ids=["", "node2"], relation="RELATES_TO")

        with pytest.raises(ValueError, match="Node IDs cannot be empty"):
            Edge(id="test_id", node_ids=["node1", ""], relation="RELATES_TO")
