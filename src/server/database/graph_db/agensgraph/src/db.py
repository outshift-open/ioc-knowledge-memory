import logging
import os

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool
import agensgraph

# Used when environment variables are not configured
AGENSGRAPH_DB_DEFAULT = "ioc-graph-db"
AGENSGRAPH_HOST_DEFAULT = "localhost"
AGENSGRAPH_PORT_DEFAULT = "5456"


class GraphDB:
    """
    Sync Agensgraph Database connection manager with connection pooling.
    Implements singleton pattern for application-wide database access.
    """

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GraphDB, cls).__new__(cls)
            # Only initialize instance attributes once
            cls._instance._engine = None
            cls._instance._session_factory = None
            cls._instance.logger = logging.getLogger(__name__)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        # This will be called on each instantiation, but we only want to initialize once
        if not self._initialized:
            self._initialized = True
            self.logger.debug("Initializing RelationalDB instance")

    def init(self, db_name: str = None, user: str = None, password: str = None, host: str = None, port: str = None):
        """Initialize the database connection and sessionmaker.

        Args:
            db_name: Database name
            user: Database user
            password: Database password
            host: Database host
            port: Database port

        Raises:
            Exception: If there's an error initializing the database connection
        """
        try:
            if self._engine is None or self._session_factory is None:
                # Get connection parameters from arguments or environment variables
                db_name = db_name or os.getenv("AGENSGRAPH_DB", AGENSGRAPH_DB_DEFAULT)
                user = user or os.getenv("AGENSGRAPH_USER")
                password = password or os.getenv("AGENSGRAPH_PASSWORD")
                host = host or os.getenv("AGENSGRAPH_HOST", AGENSGRAPH_HOST_DEFAULT)
                port = port or os.getenv("AGENSGRAPH_PORT", AGENSGRAPH_PORT_DEFAULT)

                # Create connection URL (mask password in logs)
                url = f"postgresql://{user}:***@{host}:{port}/{db_name}"
                url_with_password = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

                self.logger.debug(f"Connection to {url}")

                # Create sync engine for psycopg2
                self._engine = create_engine(
                    url_with_password,
                    echo=os.getenv("DB_ECHO", "False").lower() == "true",
                    poolclass=QueuePool,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                    pool_size=5,
                    max_overflow=10,
                    pool_timeout=30,
                )

                # Verify database connectivity
                self.verify_connectivity()

                # Create session factory
                self._session_factory = sessionmaker(autocommit=False, autoflush=False, bind=self._engine)
                self.logger.debug("Database session factory created successfully")

                self.logger.info(f"Successfully connected to database at {url}")

        except Exception as e:
            self.logger.error(f"Failed to initialize database connection: {str(e)}")
            # Reset the instance variables to allow retry
            self._engine = None
            self._session_factory = None
            raise

    def close(self):
        """Close the database connection."""
        if self._engine is not None:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None

    @property
    def engine(self):
        """Get the engine instance."""
        if self._engine is None:
            raise RuntimeError("Database not initialized. Call init() first.")
        return self._engine

    @property
    def session_factory(self):
        """Get the session factory."""
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call init() first.")
        return self._session_factory

    def verify_connectivity(self) -> None:
        """Verify database connectivity by executing a simple query.

        Raises:
            RuntimeError: If the database connection fails
        """
        if self._engine is None:
            raise RuntimeError("Database engine not initialized. Call init() first.")

        try:
            with self._engine.connect() as conn:
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
            with self._engine.begin() as conn:
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
            with self._engine.begin() as conn:
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
            with self._engine.connect() as conn:
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
            with self._engine.connect() as conn:
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
            with self._engine.connect() as conn:
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
            with self._engine.connect() as conn:
                # Start a transaction
                with conn.begin():
                    # Set the graph path for this connection
                    conn.exec_driver_sql(f'SET graph_path = "{graph}"')

                    existing_nodes = []
                    existing_edges = []

                    # Check for existing nodes
                    for node in nodes or []:
                        query, params = node.to_cypher_exists()
                        self.logger.info(f"Checking for existing node: {query} {params}")
                        result = conn.exec_driver_sql(query, params).fetchone()
                        if result and result[0]:
                            existing_nodes.append(node.id)

                    # Check for existing edges
                    for edge in edges or []:
                        query, params = edge.to_cypher_exists()
                        self.logger.info(f"Checking for existing edge: {query} {params}")
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
                            self.logger.info(f"Cypher: {node.to_executable_cypher_with_params(query, params)}")
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
            with self._engine.connect() as conn:
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
            with self._engine.connect() as conn:
                # Set the graph path for this connection
                conn.exec_driver_sql(f'SET graph_path = "{graph}"')

                # Use the new to_cypher_get method that returns only the node
                query, params = node.to_cypher_get()
                self.logger.info(f"Executing get query: {node.to_executable_cypher_with_params(query, params)}")
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
            with self._engine.connect() as conn:
                # Set the graph path for this connection
                conn.exec_driver_sql(f'SET graph_path = "{graph}"')

                # check if node exists
                query, params = node.to_cypher_exists()
                self.logger.info(f"Executing exists query: {node.to_executable_cypher_with_params(query, params)}")
                result = conn.exec_driver_sql(query, params).fetchone()
                if not result:
                    self.logger.warning(f"Node {node.id} does not exist")
                    return False, [], f"Node {node.id} does not exist"

                query, params = node.to_cypher_neighbor_query()
                self.logger.info(f"Executing neighbor query: {node.to_executable_cypher_with_params(query, params)}")

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

            with self._engine.connect() as conn:
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
                self.logger.info(f"Executing exists query: {node_dst.to_executable_cypher_with_params(query, params)}")
                result = conn.exec_driver_sql(query, params).fetchone()
                if not result:
                    self.logger.warning(f"Node {node_dst.id} does not exist")
                    return False, [], f"Node {node_dst.id} does not exist"

                if use_direction:
                    query, params = node_src.to_cypher_path_query_with_direction(node_dst, depth)
                else:
                    query, params = node_src.to_cypher_path_query(node_dst, depth)
                self.logger.info(f"Executing path query: {node_src.to_executable_cypher_with_params(query, params)}")

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

                        self.logger.info(f"Path {i+1} from {node_src.id} to {node_dst.id}:")
                        self.logger.info(f"Path object: {path}")

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
