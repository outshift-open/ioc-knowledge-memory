import logging

from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import agensgraph

from knowledge_memory.server.database.connection import ConnectDB


class GraphDB:
    """
    Sync Agensgraph Database operations using ConnectDB singleton.
    Uses shared database connection for all graph operations.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connect_db = ConnectDB()

    def init(self, db_name: str = None, user: str = None, password: str = None, host: str = None, port: str = None):
        """Initialize the database connection using ConnectDB singleton.

        Args:
            db_name: Database name (passed to ConnectDB)
            user: Database user (passed to ConnectDB)
            password: Database password (passed to ConnectDB)
            host: Database host (passed to ConnectDB)
            port: Database port (passed to ConnectDB)

        Raises:
            Exception: If there's an error initializing the database connection
        """
        try:
            # Initialize the shared database connection
            self.connect_db.init(db_name, user, password, host, port)
            self.logger.info("Graph database connection initialized successfully using ConnectDB")
        except Exception as e:
            self.logger.error(f"Failed to initialize graph database connection: {str(e)}")
            raise

    def close(self):
        """Close the database connection using ConnectDB."""
        self.connect_db.close()

    @property
    def engine(self):
        """Get the engine instance from ConnectDB."""
        return self.connect_db.engine

    @property
    def session_factory(self):
        """Get the session factory from ConnectDB."""
        return self.connect_db.session_factory

    def verify_connectivity(self) -> None:
        """Verify database connectivity by executing a simple query.

        Raises:
            RuntimeError: If the database connection fails
        """
        if self.connect_db.engine is None:
            raise RuntimeError("Database engine not initialized. Call init() first.")

        try:
            with self.connect_db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
                conn.commit()
        except SQLAlchemyError as e:
            raise RuntimeError(f"Database connection failed: {str(e)}")

    def create_graph(self, graph_name: str) -> bool:
        """Create a new graph in the database if it does not exist.

        Args:
            graph_name: Name of the graph to create

        Returns:
            bool: True if graph was created successfully, True if it already exists

        Raises:
            RuntimeError: If there's an error creating the graph
        """
        try:
            with self.connect_db.engine.begin() as conn:
                # Check if graph already exists
                result = conn.execute(
                    text("SELECT COUNT(*) FROM ag_graph WHERE graphname = :name"), {"name": graph_name}
                )
                if result.scalar() > 0:
                    self.logger.warning(f"Graph '{graph_name}' already exists")
                    return True

                # Create the graph
                conn.execute(text(f'CREATE GRAPH "{graph_name}"'))
                self.logger.info(f"Created graph '{graph_name}'")
                return True
                # Transaction automatically committed on successful exit

        except SQLAlchemyError as e:
            # Transaction automatically rolled back on exception
            raise RuntimeError(f"Failed to create graph '{graph_name}': {str(e)}")

    def delete_graph(self, graph_name: str, soft_delete: bool = False) -> bool:
        """Delete a graph from the database.

        Args:
            graph_name: Name of the graph to delete
            soft_delete: If True, marks the graph as deleted instead of dropping it.
                       If False (default), performs a hard delete with CASCADE.

        Returns:
            bool: True if graph was deleted or marked as deleted, True if it didn't exist

        Raises:
            RuntimeError: If there's an error deleting the graph
        """
        try:
            with self.connect_db.engine.begin() as conn:
                # Check if graph exists first
                check_stmt = text(
                    """
                    SELECT count(*) as count FROM ag_graph WHERE graphname = :graph_name
                    """
                )
                result = conn.execute(check_stmt, {"graph_name": graph_name}).fetchone()

                if not result or result[0] == 0:
                    self.logger.info(f"Graph '{graph_name}' does not exist, nothing to delete")
                    return True

                if soft_delete:
                    # Soft delete: Unsupported
                    # Graph will be maintained in ag_graph
                    # No existing metadata tracking soft deleted graphs
                    self.logger.warning(f"Soft delete for graph '{graph_name}'")
                else:
                    # Hard delete
                    conn.execute(text(f'DROP GRAPH "{graph_name}" CASCADE'))
                    self.logger.info(f"Hard-deleted graph '{graph_name}'")

                return True
                # Transaction automatically committed on successful exit

        except SQLAlchemyError as e:
            # Transaction automatically rolled back on exception
            raise RuntimeError(f"Failed to delete graph '{graph_name}': {str(e)}")

    def get_graph(self, graph_name: str) -> dict:
        """Get information about a specific graph.

        Args:
            graph_name: Name of the graph to retrieve

        Returns:
            dict: Graph information including name and creation time,
                  or None if graph doesn't exist

        Raises:
            RuntimeError: If there's an error retrieving the graph
        """
        try:
            with self.connect_db.engine.connect() as conn:
                result = conn.execute(
                    text(
                        """
                        SELECT graphname, nspname
                        FROM ag_graph g
                        JOIN pg_namespace n ON n.nspname = g.graphname
                        WHERE g.graphname = :name
                        """
                    ),
                    {"name": graph_name},
                ).fetchone()

                if not result:
                    return None

                return {
                    "name": result[0],
                    "namespace": result[1],
                }

        except SQLAlchemyError as e:
            raise RuntimeError(f"Failed to get graph '{graph_name}': {str(e)}")

    def get_node(self, graph: str, node) -> dict | None:
        """Get a node from the graph if it exists.

        Args:
            graph: Name of the graph to search in
            node: Node object to search for

        Returns:
            dict: Node information if it exists, None if it doesn't exist

        Raises:
            RuntimeError: If there's an error retrieving the node
        """
        try:
            with self.connect_db.engine.connect() as conn:
                with conn.begin():
                    # Set the graph path
                    conn.exec_driver_sql(f'SET graph_path = "{graph}"')

                    # Get the existence query from the node
                    query, params = node.to_cypher_exists()

                    # Execute the query
                    result = conn.exec_driver_sql(query, params).fetchone()

                    if not result:
                        return None

                    # Extract node properties from the result
                    # The result should contain the node data
                    node_data = result[0] if result else None

                    if node_data:
                        # Convert the node data to a dictionary format
                        # AgentsGraph returns node data in a specific format
                        return node_data

                    return None

        except SQLAlchemyError as e:
            error_msg = f"Failed to get node with id '{node.id}' from graph '{graph}': {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg)

    def get_edge(self, graph: str, edge) -> dict | None:
        """Get an edge from the graph if it exists.

        Args:
            graph: Name of the graph to search in
            edge: Edge object to search for

        Returns:
            dict: Edge information if it exists, None if it doesn't exist

        Raises:
            RuntimeError: If there's an error retrieving the edge
        """
        try:
            with self.connect_db.engine.connect() as conn:
                with conn.begin():
                    # Set the graph path
                    conn.exec_driver_sql(f'SET graph_path = "{graph}"')

                    # Get the existence query from the edge
                    query, params = edge.to_cypher_exists()

                    # Execute the query
                    result = conn.exec_driver_sql(query, params).fetchone()

                    if not result:
                        return None

                    # Extract edge properties from the result
                    # The result should contain the edge data
                    edge_data = result[0] if result else None

                    if edge_data:
                        # Convert the edge data to a dictionary format
                        # AgentsGraph returns edge data in a specific format
                        return edge_data

                    return None

        except SQLAlchemyError as e:
            error_msg = f"Failed to get edge with id '{edge.id}' from graph '{graph}': {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise RuntimeError(error_msg)

    def save(self, graph: str, nodes=None, edges=None, force_replace=False):
        """
        Save nodes and edges in a single transaction using AgensGraph.
        Creates the graph if it doesn't exist and checks for node existence before creating them.

        Args:
            graph: Name of the graph to save to
            nodes: List of Node objects
            edges: List of Edge objects
            force_replace: bool - if True, force replace existing nodes and edges

        Returns:
            tuple: (success: bool, message: str)
        """
        if not graph:
            return False, "Graph name cannot be empty"

        # Ensure the graph exists
        try:
            if not self.create_graph(graph):
                return False, f"Failed to create or access graph '{graph}'"
        except Exception as e:
            return False, f"Error creating/accessing graph '{graph}': {str(e)}"

        self.logger.debug(
            f"Starting save to graph '{graph}' with {len(nodes or [])} nodes and {len(edges or [])} edges"
        )

        if not nodes and not edges:
            self.logger.warning("No nodes or edges provided for save")
            return True, f"Graph: {graph} created"

        try:
            with self.connect_db.engine.connect() as conn:
                # Start a transaction
                with conn.begin():
                    # Set the graph path for this connection
                    conn.exec_driver_sql(f'SET graph_path = "{graph}"')

                    existing_nodes = []
                    existing_edges = []

                    # Check for existing nodes
                    for node in nodes or []:
                        query, params = node.to_cypher_exists()
                        self.logger.debug(f"Checking for existing node: {query} {params}")
                        result = conn.exec_driver_sql(query, params).fetchone()
                        if result and result[0]:
                            existing_nodes.append(node.id)

                    # Check for existing edges
                    for edge in edges or []:
                        query, params = edge.to_cypher_exists()
                        self.logger.debug(f"Checking for existing edge: {query} {params}")
                        result = conn.exec_driver_sql(query, params).fetchone()
                        if result and result[0]:
                            existing_edges.append(edge.id)

                    # Check for existing nodes/edges if not forcing replace
                    if not force_replace:
                        if existing_nodes or existing_edges:
                            error_msg = []
                            if existing_nodes:
                                error_msg.append(f"Nodes already exist with IDs: {', '.join(existing_nodes)}")
                            if existing_edges:
                                error_msg.append(f"Edges already exist with IDs: {', '.join(existing_edges)}")
                            error_msg.append(f"Use force_replace=True to recreate in graph:{graph}.")
                            # Raise exception to trigger rollback
                            raise ValueError(". ".join(error_msg))

                    # If force_replace is True, delete existing nodes/edges first
                    if force_replace:
                        self.logger.info(
                            f"Force replace enabled, deleting existing nodes {existing_nodes} and edges {existing_edges}"
                        )
                        nodes_to_delete = [n for n in nodes if n.id in existing_nodes] if nodes else []
                        # delete nodes and associated edges
                        for node in nodes_to_delete or []:
                            query, params = node.to_cypher_delete()
                            self.logger.debug(f"Cypher: {node.to_executable_cypher_with_params(query, params)}")
                            conn.exec_driver_sql(query, params)
                            self.logger.info(f"Node {node.id} and associated edges deleted")

                    # Process nodes
                    for node in nodes or []:
                        # Create or update node
                        query, params = node.to_cypher_create()
                        conn.exec_driver_sql(query, params)

                    # Process edges
                    for edge in edges or []:
                        # Create or update edge
                        query, params = edge.to_cypher_create()
                        conn.exec_driver_sql(query, params)

                self.logger.info(f"Successfully saved {len(nodes or [])} nodes and {len(edges or [])} edges")
                return (
                    True,
                    f"Successfully saved {len(nodes or [])} nodes and {len(edges or [])} edges to graph '{graph}'",
                )

        except ValueError as e:
            # custom error for existing nodes/edges
            self.logger.warning(f"Validation error: {str(e)}")
            return False, str(e)
        except SQLAlchemyError as e:
            self.logger.error(f"Error in save transaction: {str(e)}")
            return False, f"Database error: {str(e)}"
        except Exception as e:
            self.logger.error(f"Error in save operation: {str(e)}", exc_info=True)
            return False, f"Save operation failed: {str(e)}"

    def delete(self, graph: str, nodes: list) -> tuple[bool, str]:
        """
        Delete nodes and associated edges in a single transaction.

        Args:
            graph: Graph name
            nodes: List of Node objects

        Returns:
            Tuple containing (success: bool, message: str)
        """
        if not nodes:
            self.logger.warning("No nodes provided for deletion")
            return True, "No nodes provided for deletion"

        try:
            with self.connect_db.engine.connect() as conn:
                # Start a transaction
                with conn.begin():
                    # Set the graph path for this connection
                    conn.exec_driver_sql(f'SET graph_path = "{graph}"')

                    # Delete all nodes (this will also delete associated edges)
                    for node in nodes:
                        query, params = node.to_cypher_delete()
                        self.logger.info(
                            f"Executing delete query: {node.to_executable_cypher_with_params(query, params)}"
                        )
                        conn.exec_driver_sql(query, params)
                        self.logger.info(f"Node {node.id} and associated edges deleted")

                self.logger.info(f"Successfully deleted:{len(nodes)} nodes and associated edges from graph:'{graph}'")
                return (
                    True,
                    f"Successfully deleted:{len(nodes)} nodes and associated edges from graph:'{graph}'",
                )

        except SQLAlchemyError as e:
            self.logger.error(f"Error in delete transaction: {str(e)}")
            return False, f"Database error: {str(e)}"
        except Exception as e:
            self.logger.error(f"Error in delete operation: {str(e)}", exc_info=True)
            return False, f"Delete operation failed: {str(e)}"

    def query_type_concept(self, graph: str, nodes: list) -> tuple[bool, list, str]:
        """
        Query the graph database for the given node.

        Args:
            graph: Graph name
            nodes: List of Node objects to be used for querying

        Returns:
            Tuple containing (success: bool, results: list, msg: str)
        """
        results = []
        try:
            # validate input
            if len(nodes) > 1:
                raise ValueError("Only one node can be used for concept query")

            node = nodes[0]
            with self.connect_db.engine.connect() as conn:
                # Set the graph path for this connection
                conn.exec_driver_sql(f'SET graph_path = "{graph}"')

                # Use the new to_cypher_get method that returns only the node
                query, params = node.to_cypher_get()
                self.logger.debug(f"Executing get query: {node.to_executable_cypher_with_params(query, params)}")
                result = conn.exec_driver_sql(query, params).fetchone()

                if not result:
                    self.logger.warning(f"Node {node.id} does not exist")
                    return False, [], f"Node {node.id} does not exist"

                # Extract node data - result[0] is a collection of nodes like neighbor query
                if result and result[0]:
                    # Use list comprehension like neighbor query to handle Vertex conversion
                    node_data = [dict(n) for n in result[0]] if result[0] else []
                else:
                    node_data = []

                # For concept queries, we only return the node with empty edges
                results.append({"edges": [], "nodes": node_data})
                msg = f"Successfully queried:{node.id} in graph:{graph}."

            return True, results, msg
        except Exception as e:
            self.logger.error(f"Error in concept query: {str(e)}", exc_info=True)
            return False, [], f"Query failed: {str(e)}"

    def query_type_neighbor(self, graph: str, nodes: list) -> tuple[bool, list, str]:
        """
        Query the graph database for neighbors of the given nodes.

        Args:
            graph: Graph name
            nodes: List of Node objects to be used for querying

        Returns:
            Tuple containing (success: bool, results: list, msg: str)
        """
        results = []
        try:
            # validate input
            if len(nodes) > 1:
                raise ValueError("Only one node can be used for neighbor query")

            node = nodes[0]

            # Execute the query
            with self.connect_db.engine.connect() as conn:
                # Set the graph path for this connection
                conn.exec_driver_sql(f'SET graph_path = "{graph}"')

                # check if node exists
                query, params = node.to_cypher_exists()
                self.logger.debug(f"Executing exists query: {node.to_executable_cypher_with_params(query, params)}")
                result = conn.exec_driver_sql(query, params).fetchone()
                if not result:
                    self.logger.warning(f"Node {node.id} does not exist")
                    return False, [], f"Node {node.id} does not exist"

                query, params = node.to_cypher_neighbor_query()
                self.logger.debug(f"Executing neighbor query: {node.to_executable_cypher_with_params(query, params)}")

                result = conn.exec_driver_sql(query, params).fetchone()

                if not result:
                    self.logger.warning(f"No results found for node {node.id}")
                    msg = f"No neighbors found for:{node.id} in graph:{graph}."
                else:
                    # Extract the neighbor relationships and concepts
                    relationships = [dict(rel) for rel in result[1]] if result[1] else []  # All relationships
                    neighbors = [dict(n) for n in result[2]] if result[2] else []  # All neighbor nodes
                    results.append({"edges": relationships, "nodes": neighbors})
                    msg = f"Successfully queried neighbours for:{node.id} in graph:{graph}."

            return True, results, msg

        except Exception as e:
            error_msg = f"Error in query operation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, [], error_msg

    def query_type_path(
        self, graph: str, nodes: list, depth: int = None, use_direction: bool = True
    ) -> tuple[bool, list, str]:
        """
        Query the graph database for paths between given nodes.

        Args:
            graph: Graph name
            nodes: List of Node objects to be used for querying
            depth: Maximum path depth/length (optional, if None no depth limit is applied)
            use_direction: Whether to use directed relationships in path queries

        Returns:
            Tuple containing (success: bool, results: list, msg: str)
        """
        results = []
        try:
            # validate input
            if len(nodes) != 2:
                raise ValueError("Only 2 nodes can be used for path query")

            node_src = nodes[0]
            node_dst = nodes[1]

            with self.connect_db.engine.connect() as conn:
                # Set the graph path for this connection
                conn.exec_driver_sql(f'SET graph_path = "{graph}"')

                # check if node_src exists
                query, params = node_src.to_cypher_exists()
                self.logger.info(f"Executing exists query: {node_src.to_executable_cypher_with_params(query, params)}")
                result = conn.exec_driver_sql(query, params).fetchone()
                if not result:
                    self.logger.warning(f"Node {node_src.id} does not exist")
                    return False, [], f"Node {node_src.id} does not exist"

                # check if node_dst exists
                query, params = node_dst.to_cypher_exists()
                self.logger.debug(f"Executing exists query: {node_dst.to_executable_cypher_with_params(query, params)}")
                result = conn.exec_driver_sql(query, params).fetchone()
                if not result:
                    self.logger.warning(f"Node {node_dst.id} does not exist")
                    return False, [], f"Node {node_dst.id} does not exist"

                if use_direction:
                    query, params = node_src.to_cypher_path_query_with_direction(node_dst, depth)
                else:
                    query, params = node_src.to_cypher_path_query(node_dst, depth)
                self.logger.debug(f"Executing path query: {node_src.to_executable_cypher_with_params(query, params)}")

                # Fetch all paths, using provided query criteria
                result = conn.exec_driver_sql(query, params)
                path_results = result.fetchall()

                if not path_results:
                    self.logger.warning(f"No paths found between {node_src.id} and {node_dst.id}")
                    msg = f"No paths found between {node_src.id} and {node_dst.id} in graph:{graph}."
                else:
                    # Process each path using AgensGraph Path object
                    for i, row in enumerate(path_results):
                        path = row[0]  # This should be an AgensGraph Path object

                        self.logger.debug(f"Path {i+1} from {node_src.id} to {node_dst.id}:")
                        self.logger.debug(f"Path object: {path}")

                        # Try to access path attributes
                        path_nodes = []
                        path_edges = []

                        try:
                            # Check if it's a proper AgensGraph Path object
                            if hasattr(path, "vertices") and hasattr(path, "edges"):
                                self.logger.info(f"Found AgensGraph Path object with length: {len(path)}")

                                # Extract nodes (vertices) from path
                                if path.vertices:
                                    self.logger.info(f"Processing {len(path.vertices)} vertices")
                                    for j, vertex in enumerate(path.vertices):
                                        node_data = dict(vertex.props) if hasattr(vertex, "props") else {}
                                        path_nodes.append(node_data)
                                        self.logger.info(f"  Node {j}: {vertex.props}")

                                # Extract edges from path
                                if path.edges:
                                    self.logger.info(f"Processing {len(path.edges)} edges")
                                    for j, edge in enumerate(path.edges):
                                        edge_data = dict(edge.props) if hasattr(edge, "props") else {}
                                        edge_data["label"] = edge.label if hasattr(edge, "label") else "unknown"
                                        path_edges.append(edge_data)
                                        self.logger.info(f"  Edge {j}: {edge.label}, props: {edge.props}")
                            else:
                                self.logger.warning("Path object does not have vertices/edges attributes")
                                self.logger.info(f"Available attributes: {dir(path)}")

                        except Exception as e:
                            self.logger.error(f"Error processing path object: {e}")

                        # Append this path's nodes and edges
                        results.append(
                            {
                                "nodes": path_nodes,
                                "edges": path_edges,
                            }
                        )

                    total_paths = len(path_results)
                    msg = f"Found {total_paths} path(s) between:{node_src.id} and {node_dst.id} in graph:{graph}."

            return True, results, msg

        except Exception as e:
            error_msg = f"Error in query operation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            return False, [], error_msg
