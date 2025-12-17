import pytest
from server.database.graph_db.neo4j.models.edge import Edge


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

        # Check the raw query format (with newlines and indentation)
        expected_raw_query = """
        MATCH ()-[r {id: $id}]-()
        RETURN r
        LIMIT 1
        """
        assert query == expected_raw_query
        assert params == {"id": "test_id"}

        # Check the executable query format
        expected_executable_query = """
        MATCH ()-[r {id: 'test_id'}]-()
        RETURN r
        LIMIT 1
        ;"""
        assert edge.to_executable_cypher(query, params) == expected_executable_query

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

        # Check the parameterized query
        assert "MATCH (a {id: $source_id})" in query
        assert "MATCH (b {id: $target_id})" in query
        assert "CREATE (a)-[r:RELATES_TO {id: $id}]->(b)" in query
        assert "SET r += $props" in query
        assert "RETURN r" in query

        # Check parameters
        assert params == {
            "id": "test_id",
            "source_id": "node1",
            "target_id": "node2",
            "props": {"id": "test_id", "since": 2024, "active": True},
        }

    def test_to_executable_cypher(self):
        """Test generation of executable Cypher query."""
        edge = Edge(
            id="test_id", node_ids=["node1", "node2"], relation="RELATES_TO", properties={"since": 2024, "active": True}
        )
        # Using a raw string with double quotes to avoid escaping issues
        expected_query = r"""
        MATCH (a {id: 'node1'})
        MATCH (b {id: 'node2'})
        CREATE (a)-[r:RELATES_TO {id: 'test_id'}]->(b)
        SET r += '{\'since\': 2024, \'active\': True, \'id\': \'test_id\'}'
        RETURN r
        ;"""

        query, params = edge.to_cypher_create()
        assert edge.to_executable_cypher(query, params) == expected_query

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

        # Check that the query uses $props for all properties
        assert "$props" in query
        assert "SET r += $props" in query

        # Check that all properties are included in the params
        assert "props" in params
        assert params["props"] == {
            "id": "test_id",
            "string": "test",
            "number": 42,
            "boolean": True,
            "none": None,
            "list": [1, 2, 3],
            "dict": {"key": "value"},
        }

    def test_edge_with_empty_properties(self):
        """Test edge with empty properties."""
        edge = Edge(id="test_id", node_ids=["node1", "node2"], relation="RELATES_TO", properties={})
        assert edge.properties == {}
        query, params = edge.to_cypher_create()
        assert "props" in params
        # 'id' is added to properties by design
        # no other properties
        assert params["props"] == {"id": "test_id"}

    def test_edge_with_special_chars_in_properties(self):
        """Test edge with special characters in properties."""
        edge = Edge(
            id="test_id",
            node_ids=["node1", "node2"],
            relation="HAS_COMMENT",
            properties={"text": "This is a comment with special chars: !@#$"},
        )
        query, params = edge.to_cypher_create()
        cypher = edge.to_executable_cypher(query, params)
        assert "This is a comment with special chars: !@#$" in cypher

    def test_edge_with_empty_node_ids(self):
        """Test validation fails with empty node IDs."""
        with pytest.raises(ValueError, match="Node IDs cannot be empty"):
            Edge(id="test_id", node_ids=["", "node2"], relation="RELATES_TO")

        with pytest.raises(ValueError, match="Node IDs cannot be empty"):
            Edge(id="test_id", node_ids=["node1", ""], relation="RELATES_TO")
