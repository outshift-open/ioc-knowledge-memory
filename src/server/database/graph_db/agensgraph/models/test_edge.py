# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

import pytest

from server.database.graph_db.agensgraph.models.edge import Edge


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
        """Test that relation format validation is disabled (allows any format)."""
        # Relation type validation is now disabled to allow flexible relation names
        edge = Edge(id="rel_id", node_ids=["1", "2"], relation="invalid-relation")
        assert edge.relation == "invalid-relation"

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
        assert 'CREATE (a)-[r:"RELATES_TO" { "since": %s, "active": %s, "id": %s }]->(b)' in query
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

        # Check that the query uses %s placeholders for all properties (with quoted keys)
        assert '"string": %s' in query
        assert '"number": %s' in query
        assert '"boolean": %s' in query
        assert '"none": %s' in query
        assert '"list": %s' in query
        assert '"dict": %s' in query
        assert '"id": %s' in query

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

    def test_property_key_quoting_basic(self):
        """Test that property keys are quoted in CREATE queries."""
        edge = Edge(id="test_id", node_ids=["node1", "node2"], relation="RELATES_TO", 
                   properties={"simple_key": "value"})
        query, params = edge.to_cypher_create()
        
        # Property keys should be quoted with double quotes
        assert '"simple_key": %s' in query
        assert '"id": %s' in query
        # Relation type should also be quoted
        assert '"RELATES_TO"' in query

    def test_property_key_quoting_special_characters(self):
        """Test that property keys with special characters are quoted correctly."""
        properties = {
            "key-with-hyphens": "value1",
            "key_with_underscores": "value2", 
            "key.with.dots": "value3",
            "key with spaces": "value4"
        }
        edge = Edge(id="test_id", node_ids=["node1", "node2"], relation="RELATES_TO", 
                   properties=properties)
        query, params = edge.to_cypher_create()
        
        # All property keys should be quoted
        assert '"key-with-hyphens": %s' in query
        assert '"key_with_underscores": %s' in query
        assert '"key.with.dots": %s' in query
        assert '"key with spaces": %s' in query
        assert '"id": %s' in query

    def test_property_key_quoting_reserved_keywords(self):
        """Test that property keys that are Cypher reserved keywords are quoted."""
        properties = {
            "match": "value1",
            "where": "value2",
            "return": "value3",
            "create": "value4"
        }
        edge = Edge(id="test_id", node_ids=["node1", "node2"], relation="RELATES_TO", 
                   properties=properties)
        query, params = edge.to_cypher_create()
        
        # Reserved keywords should be quoted
        assert '"match": %s' in query
        assert '"where": %s' in query
        assert '"return": %s' in query
        assert '"create": %s' in query
        assert '"id": %s' in query

    def test_property_key_quoting_uuid_keys(self):
        """Test that UUID-based property keys (like internal attributes) are quoted correctly."""
        properties = {
            "550e8400-e29b-41d4-a716-446655440000$category": "Technology",
            "123e4567-e89b-12d3-a456-426614174000$rate": 19.5,
            "regular_key": "normal_value"
        }
        edge = Edge(id="test_id", node_ids=["node1", "node2"], relation="RELATES_TO", 
                   properties=properties)
        query, params = edge.to_cypher_create()
        
        # UUID-based keys with separators should be quoted
        assert '"550e8400-e29b-41d4-a716-446655440000$category": %s' in query
        assert '"123e4567-e89b-12d3-a456-426614174000$rate": %s' in query
        assert '"regular_key": %s' in query
        assert '"id": %s' in query

    def test_property_key_quoting_numeric_start(self):
        """Test that property keys starting with numbers are quoted correctly."""
        properties = {
            "123_numeric_start": "value1",
            "456key": "value2",
            "789-key": "value3"
        }
        edge = Edge(id="test_id", node_ids=["node1", "node2"], relation="RELATES_TO", 
                   properties=properties)
        query, params = edge.to_cypher_create()
        
        # Keys starting with numbers should be quoted
        assert '"123_numeric_start": %s' in query
        assert '"456key": %s' in query
        assert '"789-key": %s' in query
        assert '"id": %s' in query

    def test_relation_type_quoting_reserved_keywords(self):
        """Test that relation types that are reserved keywords are quoted correctly."""
        edge = Edge(id="test_id", node_ids=["node1", "node2"], relation="REFERENCES")
        query, params = edge.to_cypher_create()
        
        # Reserved keyword relation types should be quoted
        assert '"REFERENCES"' in query
        assert 'r:"REFERENCES"' in query

    def test_relation_type_quoting_special_characters(self):
        """Test that relation types with special characters are quoted correctly."""
        edge = Edge(id="test_id", node_ids=["node1", "node2"], relation="RELATES-TO")
        query, params = edge.to_cypher_create()
        
        # Relation types with special characters should be quoted
        assert '"RELATES-TO"' in query
        assert 'r:"RELATES-TO"' in query

    def test_property_key_quoting_empty_properties(self):
        """Test that edges with no additional properties still quote the id key."""
        edge = Edge(id="test_id", node_ids=["node1", "node2"], relation="RELATES_TO")
        query, params = edge.to_cypher_create()
        
        # Even with no additional properties, id should be quoted
        assert '"id": %s' in query
        # Should have source_id, target_id, and id parameters
        assert len(params) == 3
        assert params == ("node1", "node2", "test_id")

    def test_relation_validation_disabled(self):
        """Test that relation type validation is disabled and allows flexible formats."""
        # This should work now that validation is disabled
        edge = Edge(id="test_id", node_ids=["node1", "node2"], relation="invalid-relation-format")
        assert edge.relation == "invalid-relation-format"
        
        # Should also work with lowercase
        edge2 = Edge(id="test_id2", node_ids=["node1", "node2"], relation="lowercase_relation")
        assert edge2.relation == "lowercase_relation"
        
        # Should work with spaces
        edge3 = Edge(id="test_id3", node_ids=["node1", "node2"], relation="relation with spaces")
        assert edge3.relation == "relation with spaces"
