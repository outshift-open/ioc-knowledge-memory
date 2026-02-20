import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


@dataclass
class Node:
    """Represents a node.

    Attributes:
        id: Unique identifier for the node (will be used as the 'id' property)
        labels: label for the node (e.g., ["Concept"])
        properties: Dictionary of node properties
        internal_id: Internal node ID (set after node creation)
    """

    id: str  # id sent by caller
    labels: List[str]
    properties: Dict[str, Any] = field(default_factory=dict)
    # these fields from request are added to properties
    # id (sent by caller)(not editable)
    # name: str
    # description: str
    # attributes (dynamic)
    # embeddings (embeddings_model, embedding_vector)
    # mas_id, wksp_id, memory_type
    # tags (dynamic)

    def __post_init__(self):
        if not self.id:
            raise ValueError("Node ID cannot be empty")

        self._validate_properties()

    def _validate_properties(self):
        for key, value in self.properties.items():
            if not isinstance(key, str) or not key.strip():
                raise ValueError(f"Invalid property key: {key}")

    def to_cypher_exists(self) -> tuple[str, tuple]:
        """Generate a Cypher query to check if a node with this ID exists.

        The query will return the node if it exists, or None if it doesn't.
        This only checks the node's ID property (user provided id).
        Not the internal node id from graph database.

        Returns:
            tuple: (cypher_query, parameters_tuple) containing the node ID
        """
        return "MATCH (n {id: %s}) RETURN n LIMIT 1", (self.id,)

    def to_cypher_get(self) -> tuple[str, tuple]:
        """Generate a Cypher query to get this node only.

        This method returns just the node data for concept queries.

        Returns:
            tuple: (cypher_query, parameters_tuple) containing the node ID

        The query returns:
        - The node (as 'n') only

        Raises:
            ValueError: Node must have an ID for get queries
        """
        alias = "n"

        if not hasattr(self, "id") or self.id is None:
            raise ValueError("Node must have an ID for get queries")

        # Return the node in a collection format like other query method for consistent handling in adapter
        query = f"MATCH ({alias} {{id: %s}}) RETURN collect({alias}) as nodes"
        return query, (self.id,)

    def to_cypher_create(self) -> tuple[str, tuple]:
        """Generate Cypher CREATE clause for this node.

        AgensGraph handles arrays better when converted to JSON strings.

        Returns:
            tuple: (cypher_query, parameters_tuple)
        """
        alias = "n"
        # Agensgraph only supports single label
        labels = self.labels[0] if self.labels else "Node"
        properties = self.properties.copy()
        properties["id"] = self.id

        # Convert lists to JSON strings for AgensGraph compatibility
        for key, value in properties.items():
            if isinstance(value, list):
                properties[key] = json.dumps(value)
            else:
                properties[key] = value

        # Build property string with %s placeholders
        props = ", ".join([f"{k}: %s" for k in properties.keys()])
        query = f"CREATE ({alias}:{labels} {{ {props} }}) RETURN {alias}"

        return query, tuple(properties.values())

    def to_cypher_delete(self) -> tuple[str, tuple]:
        """Generate a Cypher DELETE clause for this node.
        Deletes the node and the edges connected to it using DETACH DELETE.

        Returns:
            tuple: (cypher_query, parameters_tuple)

        Example:
            query, params = node.to_cypher_delete()
        """
        query = "MATCH (n {id: %s}) DETACH DELETE n"
        return query, (self.id,)

    def to_cypher_neighbor_query(self) -> tuple[str, tuple]:
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

        # Match only by ID using parameterized query
        node_match_cnt = 1  # since we are only matching by ID
        query = (
            f"MATCH ({alias} {{id: %s}})"
            f"\nWITH {alias} LIMIT {node_match_cnt}"
            f"\nOPTIONAL MATCH ({alias})-[r]-(m)"
            f"\nRETURN {alias}, collect(DISTINCT r) as relationships, collect(DISTINCT m) as neighbors"
        )
        return query, (self.id,)

    def to_cypher_path_query(self, node_dst, depth: int = None) -> tuple[str, tuple]:
        """Generate a Cypher query to find all paths between this node and a destination node.

        Args:
            node_dst: Destination Node object
            depth: Maximum path depth/length (optional, if None no depth limit is applied)

        The query will return all paths between the source and destination nodes.
        If depth is specified, only paths within that depth limit are returned.

        Returns:
            tuple: (cypher_query, parameters_tuple) containing source_id and dest_id

        Raises:
            ValueError: Both nodes must have an ID for path queries
        """
        if not hasattr(self, "id") or self.id is None:
            raise ValueError("Source node must have an ID for path queries")

        if not hasattr(node_dst, "id") or node_dst.id is None:
            raise ValueError("Destination node must have an ID for path queries")

        # path query
        if depth is not None:
            query = f"MATCH p = (start {{id: %s}})-[*1..{depth}]-(finish {{id: %s}}) RETURN p"
        else:
            query = "MATCH p = (start {id: %s})-[*]-(finish {id: %s}) RETURN p"

        return query, (self.id, node_dst.id)

    def to_cypher_path_query_with_direction(self, node_dst, depth: int = None) -> tuple[str, tuple]:
        """Generate a Cypher query to find all directed paths from this node to a destination node.

        Args:
            node_dst: Destination Node object
            depth: Maximum path depth/length (optional, if None no depth limit is applied)

        The query will return all directed paths from the source to destination nodes,
        following the direction of relationships. Uses directed relationship pattern (-[*]->).
        If depth is specified, only paths within that depth limit are returned.

        Returns:
            tuple: (cypher_query, parameters_tuple) containing source_id and dest_id

        Raises:
            ValueError: Both nodes must have an ID for path queries
        """
        if not hasattr(self, "id") or self.id is None:
            raise ValueError("Source node must have an ID for path queries")

        if not hasattr(node_dst, "id") or node_dst.id is None:
            raise ValueError("Destination node must have an ID for path queries")

        # directed path query
        if depth is not None:
            query = f"MATCH p = (start {{id: %s}})-[*1..{depth}]->(finish {{id: %s}}) RETURN p"
        else:
            query = "MATCH p = (start {id: %s})-[*]->(finish {id: %s}) RETURN p"

        return query, (self.id, node_dst.id)

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

    def to_executable_cypher_with_params(self, query: str, params: tuple, param_names: list = None) -> str:
        """Wrapper method to convert tuple-based parameters to executable Cypher query.

        This method handles the conversion from tuple parameters (used by most query methods)
        to the dictionary format expected by to_executable_cypher.

        Args:
            query: The Cypher query string with %s placeholders
            params: Tuple of parameter values
            param_names: List of parameter names (defaults to ['id'] for single param,
                        or ['param0', 'param1', ...] for multiple params)

        Returns:
            str: A complete Cypher query with all parameters inlined as strings

        Example:
            query, params = node.to_cypher_delete()
            executable_query = node.to_executable_cypher_with_params(query, params)
            # Returns: "MATCH (n {id: 'node-id'}) DETACH DELETE n;"
        """
        if not params:
            # No parameters, just ensure semicolon and return
            return query + (";" if not query.strip().endswith(";") else "")

        # Default parameter names for common cases
        if param_names is None:
            if len(params) == 1:
                param_names = ["id"]
            else:
                param_names = [f"param{i}" for i in range(len(params))]

        # Convert %s placeholders to $param format and create params dict
        converted_query = query
        params_dict = {}

        for i, (param_name, param_value) in enumerate(zip(param_names, params)):
            converted_query = converted_query.replace("%s", f"${param_name}", 1)
            params_dict[param_name] = param_value

        return self.to_executable_cypher(converted_query, params_dict)
