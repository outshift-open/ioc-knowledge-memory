from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, field
from uuid import uuid4
import re


@dataclass
class Edge:
    """Represents a relationship between two nodes in Neo4j.

    Attributes:
        node_ids: List of exactly two node IDs [source_id, target_id]
        relation: Type of the relationship (e.g., 'KNOWS', 'WORKS_AT')
        properties: Dictionary of relationship properties
        direction: Direction of the relationship ('->' or '<-' or '--')
    """

    id: str  # id sent by caller
    node_ids: List[str]
    relation: str  # relation type (e.g., 'KNOWS', 'WORKS_AT')
    properties: Dict[str, Any] = field(default_factory=dict)
    direction: str = "->"
    # TkfStoreRequest.relation is added as label
    # (neo4j edges can have only 1 label=relation)
    # These fields from TkfStoreRequest are added to properties
    # id (sent by caller)(not editable)
    # node_ids (sent by caller)
    # attributes (dynamic)
    # embeddings (embeddings_model, embedding_vector)
    # mas_id, wksp_id, memory_type

    def __post_init__(self):
        if not self.id:
            raise ValueError("Edge ID cannot be empty")
        if len(self.node_ids) != 2:
            raise ValueError("Exactly two node IDs are required")
        if not all(self.node_ids):
            raise ValueError("Node IDs cannot be empty")
        # per neo4j recommendations, relation type should be uppercase with underscores
        if not self.relation or not re.match(r"^[A-Z_]+$", self.relation):
            raise ValueError("Relation type must be uppercase with underscores")
        if self.direction not in ("->", "<-", "--"):
            raise ValueError("Direction must be one of: '->', '<-', '--'")
        self._validate_properties()

    def _validate_properties(self):
        for key, value in self.properties.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError(f"Invalid property key: {key}")

    def to_cypher_exists(self) -> tuple[str, dict]:
        """Generate a Cypher query to check if this relationship exists.

        The query will return the edge if it exists (based on the ID property),
        or None if it doesn't. This only checks the edge's ID property and
        not the nodes it connects.
        This only checks the edges's ID property (user provided id).
        Not the internal neo4j id

        Returns:
            tuple: (cypher_query, parameters_dict) containing the relationship ID
        """
        query = f"""
        MATCH ()-[r {{id: $id}}]-()
        RETURN r
        LIMIT 1
        """

        return query, {"id": self.id}

    def to_cypher_create(self) -> tuple[str, dict]:
        """Generate Cypher CREATE clause for this edge.
        First checks if both source and target nodes exist.

        Returns:
            tuple: (cypher_query, parameters_dict)
        """
        source_id, target_id = self.node_ids
        properties = self.properties.copy()
        properties["id"] = self.id  # use the id sent by the caller

        # Create safe parameter names
        source_param = "source_id"
        target_param = "target_id"

        # Determine the relationship pattern based on direction
        if self.direction == "->":
            rel_pattern = f"(a)-[r:{self.relation} {{id: $id}}]->(b)"
        elif self.direction == "<-":
            rel_pattern = f"(a)<-[r:{self.relation} {{id: $id}}]-(b)"
        else:  # undirected
            rel_pattern = f"(a)-[r:{self.relation} {{id: $id}}]-(b)"

        # Build the query to check node existence and create relationship
        # First check if both nodes exist
        # If both nodes exist, create the relationship
        query = f"""
        MATCH (a {{id: ${source_param}}})
        MATCH (b {{id: ${target_param}}})
        CREATE {rel_pattern}
        SET r += $props
        RETURN r
        """

        params = {source_param: source_id, target_param: target_id, "id": self.id, "props": properties}

        return query, params

    def to_executable_cypher(self, query: str, params: dict) -> str:
        """Generate an executable Cypher query with parameters inlined.

        Args:
            query: The Cypher query string with parameter placeholders (e.g., "$param")
            params: Dictionary of parameter names to values

        Returns:
            str: A complete Cypher query with all parameters inlined as strings
        """
        try:
            # Process each parameter and replace in the query
            for key, value in params.items():
                if value is None:
                    value_str = "null"
                else:
                    # Convert all values to string, escape single quotes, and wrap in single quotes
                    value_str = "'" + str(value).replace("'", "\\'") + "'"

                # Replace all occurrences of the parameter in the query
                query = query.replace(f"${key}", value_str)

            # Ensure the query ends with a semicolon
            if not query.strip().endswith(";"):
                query += ";"

            return query

        except Exception as e:
            # Log the error and return a meaningful error message
            import logging

            logging.error(f"Error generating executable Cypher query: {e}")
            return f"/* Error generating query: {str(e)} */"
