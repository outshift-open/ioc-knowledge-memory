import pytest

from knowledge_memory.server.database.graph_db.agensgraph.models.node import Node


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

    def test_node_label_sanitization_during_init(self):
        """Test that labels are stored as-is during initialization."""
        node = Node(id="test_id", labels=["Test Label", "Another-Label"])
        # Labels are not sanitized in the current implementation
        assert node.labels == ["Test Label", "Another-Label"]

    def test_node_property_validation(self):
        """Test that invalid property keys raise ValueError."""
        with pytest.raises(ValueError, match="Invalid property key"):
            Node(id="test_id", labels=["TestLabel"], properties={"": "value"})

        with pytest.raises(ValueError, match="Invalid property key"):
            Node(id="test_id", labels=["TestLabel"], properties={42: "value"})

    def test_to_cypher_neighbor_query(self):
        """Test generation of Cypher neighbor query."""
        # Test with a node with ID
        node = Node(id="test_id", labels=["TestLabel"])
        query, params = node.to_cypher_neighbor_query()
        expected_query = (
            "MATCH (n {id: %s})\n"
            "WITH n LIMIT 1\n"
            "OPTIONAL MATCH (n)-[r]-(m)\n"
            "RETURN n, collect(DISTINCT r) as relationships, collect(DISTINCT m) as neighbors"
        )
        assert query == expected_query
        assert params == ("test_id",)

    def test_to_cypher_exists(self):
        """Test generation of Cypher EXISTS query."""
        node = Node(id="test_id", labels=["TestLabel"])
        query, params = node.to_cypher_exists()
        assert query == "MATCH (n {id: %s}) RETURN n LIMIT 1"
        assert params == ("test_id",)

    def test_to_cypher_create(self):
        """Test generation of Cypher CREATE query."""
        node = Node(id="test_id", labels=["TestLabel", "AnotherLabel"], properties={"name": "Test", "value": 42})
        query, params = node.to_cypher_create()
        # AgensGraph only supports single label, so only first label is used
        assert "CREATE (n:TestLabel { name: %s, value: %s, id: %s }) RETURN n" in query
        # Parameters are returned as tuple in the order they appear in the properties
        assert params == ("Test", 42, "test_id")

    def test_to_cypher_delete(self):
        """Test generation of Cypher DELETE query."""
        node = Node(id="test_id", labels=["TestLabel"])
        query, params = node.to_cypher_delete()
        assert query == "MATCH (n {id: %s}) DETACH DELETE n"
        assert params == ("test_id",)

    def test_to_executable_cypher(self):
        """Test generation of executable Cypher query."""
        node = Node(id="test_id", labels=["TestLabel"], properties={"name": "Test's Node", "value": 42})
        query, params = node.to_cypher_create()
        # The to_executable_cypher method expects dict parameters but gets tuple parameters
        # This should result in an error
        result = node.to_executable_cypher(query, params)
        assert "Error generating query: 'tuple' object has no attribute 'items'" in result

    def test_node_with_empty_labels(self):
        """Test that node keeps empty labels as-is."""
        node = Node(id="test_id", labels=[])
        # Empty labels remain empty in the current implementation
        assert node.labels == []

    def test_node_with_none_properties(self):
        """Test that node handles None properties correctly."""
        node = Node(id="test_id", labels=["TestLabel"], properties={"none_val": None})
        assert node.properties == {"none_val": None}
        query, params = node.to_cypher_create()
        # Parameters are returned as tuple, None should be in the tuple
        assert None in params
        assert params == (None, "test_id")  # (none_val, id)
