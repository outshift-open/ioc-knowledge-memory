import pytest
from server.database.graph_db.neo4j.models.node import Node


class TestNode:
    """Test cases for the Node class."""

    def test_node_initialization(self):
        """Test basic node initialization with required fields."""
        node = Node(id="test_id", labels=["TestLabel"])
        assert node.id == "test_id"
        assert node.labels == ["TestLabel"]
        assert node.properties == {}

    def test_node_with_properties(self):
        """Test node initialization with properties."""
        props = {"name": "Test Node", "value": 42}
        node = Node(id="test_id", labels=["TestLabel"], properties=props)
        assert node.properties == props
        assert node.properties["name"] == "Test Node"

    def test_node_without_id_raises_error(self):
        """Test that node initialization without ID raises ValueError."""
        with pytest.raises(ValueError, match="Node ID cannot be empty"):
            Node(id="", labels=["TestLabel"])

    def test_node_sanitize_label(self):
        """Test label sanitization."""
        assert Node.sanitize_label("Test Label") == "Test_Label"
        assert Node.sanitize_label("Test-Label") == "Test_Label"
        assert Node.sanitize_label("123Test") == "n123Test"
        assert Node.sanitize_label("") == "Node"
        assert Node.sanitize_label("  ") == "Node"
        assert Node.sanitize_label("Test@Node#1") == "Test_Node_1"

    def test_node_label_sanitization_during_init(self):
        """Test that labels are properly sanitized during initialization."""
        node = Node(id="test_id", labels=["Test Label", "Another-Label"])
        assert node.labels == ["Test_Label", "Another_Label"]

    def test_node_property_validation(self):
        """Test that invalid property keys raise ValueError."""
        with pytest.raises(ValueError, match="Invalid property key"):
            Node(id="test_id", labels=["TestLabel"], properties={"": "value"})

        with pytest.raises(ValueError, match="Invalid property key"):
            Node(id="test_id", labels=["TestLabel"], properties={42: "value"})

    def test_to_cypher_exists(self):
        """Test generation of Cypher EXISTS query."""
        node = Node(id="test_id", labels=["TestLabel"])
        query, params = node.to_cypher_exists()
        assert query == "MATCH (n {id: $id}) RETURN n LIMIT 1"
        assert params == {"id": "test_id"}

        expected_query = "MATCH (n {id: 'test_id'}) RETURN n LIMIT 1;"
        assert node.to_executable_cypher(query, params) == expected_query

    def test_to_cypher_create(self):
        """Test generation of Cypher CREATE query."""
        node = Node(id="test_id", labels=["TestLabel", "AnotherLabel"], properties={"name": "Test", "value": 42})
        query, params = node.to_cypher_create()
        assert "CREATE (n:TestLabel:AnotherLabel { name: $name, value: $value, id: $id }) RETURN n" in query
        assert params == {"id": "test_id", "name": "Test", "value": 42}

        expected_query = "CREATE (n:TestLabel:AnotherLabel { name: 'Test', value: '42', id: 'test_id' }) RETURN n;"
        assert node.to_executable_cypher(query, params) == expected_query

    def test_to_cypher_delete(self):
        """Test generation of Cypher DELETE query."""
        node = Node(id="test_id", labels=["TestLabel"])
        query, params = node.to_cypher_delete()
        assert query == "MATCH (n {id: $id}) DETACH DELETE n"
        assert params == {"id": "test_id"}

        expected_query = "MATCH (n {id: 'test_id'}) DETACH DELETE n;"
        assert node.to_executable_cypher(query, params) == expected_query

    def test_to_executable_cypher(self):
        """Test generation of executable Cypher query."""
        node = Node(id="test_id", labels=["TestLabel"], properties={"name": "Test's Node", "value": 42})
        expected_query = "CREATE (n:TestLabel { name: 'Test\\'s Node', value: '42', id: 'test_id' }) RETURN n;"
        query, params = node.to_cypher_create()
        assert node.to_executable_cypher(query, params) == expected_query

    def test_node_with_empty_labels(self):
        """Test that node gets a default 'NODE' label if no labels provided."""
        node = Node(id="test_id", labels=[])
        assert node.labels == ["NODE"]

    def test_node_with_none_properties(self):
        """Test that node handles None properties correctly."""
        node = Node(id="test_id", labels=["TestLabel"], properties={"none_val": None})
        assert node.properties == {"none_val": None}
        query, params = node.to_cypher_create()
        assert "none_val" in params
        assert params["none_val"] is None
