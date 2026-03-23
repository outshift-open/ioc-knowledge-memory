# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Any


@dataclass
class Edge:
    """Represents a relationship between two nodes.

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
    # relation is added as label
    # (edges can have only 1 label=relation)
    # These fields from request are added to properties
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
        # relation type as uppercase with underscores
        if not self.relation or not re.match(r"^[A-Z0-9_]+$", self.relation):
            raise ValueError("Relation type must be uppercase with underscores")
        if self.direction not in ("->", "<-", "--"):
            raise ValueError("Direction must be one of: '->', '<-', '--'")
        self._validate_properties()

    def _validate_properties(self):
        for key, value in self.properties.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError(f"Invalid property key: {key}")

    def to_cypher_exists(self) -> tuple[str, tuple]:
        """Generate a Cypher query to check if this relationship exists.

        The query will return the edge if it exists (based on the ID property),
        or None if it doesn't. This only checks the edge's ID property and
        not the nodes it connects.
        This only checks the edges's ID property (user provided id).
        Not the internal graph edge id

        Returns:
            tuple: (cypher_query, parameters_tuple) containing the relationship ID
        """
        query = "MATCH ()-[r {id: %s}]-() RETURN r LIMIT 1"
        return query, (self.id,)

    def to_cypher_create(self) -> tuple[str, tuple]:
        """Generate Cypher CREATE clause for this edge.
        First checks if both source and target nodes exist.

        AgensGraph handles arrays better when converted to JSON strings.

        Returns:
            tuple: (cypher_query, parameters_tuple)
        """
        source_id, target_id = self.node_ids
        properties = self.properties.copy()
        properties["id"] = self.id  # use the id sent by the caller

        # Convert lists to JSON strings for AgensGraph compatibility
        for key, value in properties.items():
            if isinstance(value, list):
                properties[key] = json.dumps(value)
            else:
                properties[key] = value

        # Build property string with %s placeholders
        props = ", ".join([f"{k}: %s" for k in properties.keys()])

        # Determine the relationship pattern based on direction
        if self.direction == "->":
            rel_pattern = f"(a)-[r:{self.relation} {{ {props} }}]->(b)"
        elif self.direction == "<-":
            rel_pattern = f"(a)<-[r:{self.relation} {{ {props} }}]-(b)"
        else:  # undirected
            rel_pattern = f"(a)-[r:{self.relation} {{ {props} }}]-(b)"

        # Build the query to check node existence and create relationship
        query = f"MATCH (a {{id: %s}}), (b {{id: %s}}) CREATE {rel_pattern} RETURN r"

        # Return query with tuple of values: source_id, target_id, then all property values
        params = (source_id, target_id) + tuple(properties.values())

        return query, params

    def to_cypher_delete(self) -> tuple[str, tuple]:
        """Generate a Cypher DELETE clause for this edge.
        Deletes only the edge, not the connected nodes.

        Returns:
            tuple: (cypher_query, parameters_tuple)

        Example:
            query, params = edge.to_cypher_delete()
        """
        query = "MATCH ()-[r {id: %s}]-() DELETE r"
        return query, (self.id,)

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
