from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from uuid import uuid4
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class Node:
    """Represents a node in the Neo4j graph.

    Attributes:
        id: Unique identifier for the node (will be used as the 'id' property in Neo4j)
        labels: List of labels for the node (e.g., ["Person", "Employee"])
        properties: Dictionary of node properties
        internal_id: Internal Neo4j node ID (set after node creation)
    """

    id: str  # id sent by caller
    labels: List[str]
    properties: Dict[str, Any] = field(default_factory=dict)
    # these fields from TkfStoreRequest are added to labels
    # mas_id, wksp_id, memory_type
    # these fields from TkfStoreRequest are added to properties
    # id (sent by caller)(not editable)
    # name: str
    # description: str
    # attributes (dynamic)
    # embeddings (embeddings_model, embedding_vector)

    @staticmethod
    def sanitize_label(label: str) -> str:
        """Convert a string to a valid Neo4j label.

        Args:
            label: The input string to sanitize

        Returns:
            str: Sanitized label with only alphanumeric characters and underscores,
                 preserving the original case
        """
        if not label or not str(label).strip():
            return "Node"  # Default label if empty or whitespace

        # Convert to string and preserve case
        label = str(label)
        # Replace any non-alphanumeric character with underscore
        sanitized = re.sub(r"[^a-zA-Z0-9_]", "_", label)
        # Remove leading/trailing underscores
        sanitized = sanitized.strip("_")
        # Ensure it starts with a letter or underscore
        if not sanitized or sanitized[0].isdigit():
            sanitized = "n" + sanitized
        return sanitized or "Node"

    def __post_init__(self):
        if not self.id:
            raise ValueError("Node ID cannot be empty")

        # Sanitize all labels
        sanitized_labels = []
        for label in self.labels:
            if not label:  # Skip empty labels
                continue
            sanitized = self.sanitize_label(label)
            if sanitized != label:
                logger.debug(f"Sanitized label '{label}' to '{sanitized}'")
            sanitized_labels.append(sanitized)

        # Ensure we have at least one label
        if not sanitized_labels:
            sanitized_labels = ["NODE"]

        self.labels = sanitized_labels
        self._validate_properties()

    def _validate_properties(self):
        for key, value in self.properties.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError(f"Invalid property key: {key}")

    def to_cypher_exists(self) -> tuple[str, dict]:
        """Generate a Cypher query to check if a node with this ID exists.

        The query will return the node if it exists, or None if it doesn't.
        This only checks the node's ID property (user provided id).
        Not the internal neo4j id

        Returns:
            tuple: (cypher_query, parameters_dict) containing the node ID
        """
        return "MATCH (n {id: $id}) RETURN n LIMIT 1", {"id": self.id}

    def to_cypher_create(self) -> tuple[str, dict]:
        """Generate Cypher CREATE clause for this node.

        Returns:
            tuple: (cypher_query, parameters_dict)
        """
        alias = "n"
        labels = ":".join(self.labels)
        properties = self.properties.copy()
        properties["id"] = self.id  # use the id sent by the caller, so we can find the node using this ID
        props = ", ".join([f"{k}: ${k}" for k in properties.keys()])
        query = f"CREATE ({alias}:{labels} {{ {props} }}) RETURN {alias}"
        return query, properties

    def to_cypher_delete(self) -> tuple[str, dict]:
        """Generate a Cypher DELETE clause for this node.
        Deletes the node and the edges connected to it.

        Returns:
            tuple: (cypher_query, parameters_dict)

        Example:
            query, params = node.to_cypher_delete()
        """
        params = {"id": self.id}
        query = "MATCH (n {id: $id}) DETACH DELETE n"
        return query, params

    def to_cypher_neighbor_query(self) -> tuple[str, dict]:
        """Generate a Cypher query to find nodes matching the criteria along with their
        immediate relationships and neighbor nodes, with a limit on the number of matched nodes.

        Args:
            node_match_limit: Maximum number of nodes to match (default: 1)

        The query will return for each matched node:
        - The node (as 'n')
        - All relationships from/to this node (as 'r')
        - All connected neighbor nodes (as 'm')

        Returns:

        Raises:
            ValueError: Node must have an ID for neighbor queries
        """
        alias = "n"
        # Only match by ID, ignore labels and other properties
        if not hasattr(self, "id") or self.id is None:
            raise ValueError("Node must have an ID for neighbor queries")

        # Match only by ID
        props = f'id: "{self.id}"'

        node_match_cnt = 1  # since we are only matching by ID
        query = (
            f"MATCH ({alias} {{ {props} }})"
            f"\nWITH {alias} LIMIT {node_match_cnt}"
            f"\nOPTIONAL MATCH ({alias})-[r]-(m)"
            f"\nRETURN {alias}, collect(DISTINCT r) as relationships, collect(DISTINCT m) as neighbors"
        )
        return query, {}

    def to_executable_cypher(self, query: str, params: dict) -> str:
        """Generate an executable Cypher query with parameters inlined.

        Args:
            query: The Cypher query string with parameter placeholders (e.g., "$param")
            params: Dictionary of parameter names to values

        Returns:
            str: A complete Cypher query with all parameters inlined as strings

        Example:
            query = "CREATE (n:Label {id: $id, name: $name, value: $value})"
            params = {"id": "123", "name": "Test", "value": 42}
            to_executable_cypher(query, params)
            # Returns: "CREATE (n:Label {id: '123', name: 'Test', value: '42'})"
        """
        try:
            # Process each parameter and replace in the query
            for key, value in params.items():
                # Convert all values to string and escape single quotes
                if value is None:
                    value_str = "null"
                else:
                    # Convert to string, escape single quotes, and wrap in single quotes
                    value_str = "'" + str(value).replace("'", "\\'") + "'"

                # Replace all occurrences of the parameter in the query
                query = query.replace(f"${key}", value_str)

            # Ensure the query ends with a semicolon
            if not query.strip().endswith(";"):
                query += ";"

            return query

        except Exception as e:
            # Log the error and return a meaningful error message
            logging.error(f"Error generating executable Cypher query: {e}")
            return f"/* Error generating query: {str(e)} */"
