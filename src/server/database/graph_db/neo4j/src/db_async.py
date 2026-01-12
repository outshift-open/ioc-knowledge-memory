import os
import logging
import time
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from server.schemas.tkf import QUERY_TYPE_NEIGHBOUR
from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import ServiceUnavailable, AuthError
from server.database.graph_db.neo4j.models.node import Node
from server.database.graph_db.neo4j.models.edge import Edge
from server.schemas.tkf import QueryCriteria

# Used when environment variables are not configured
NEO4J_DATABASE_DEFAULT = "tkf"
NEO4J_HOST_DEFAULT = "localhost"
NEO4J_PORT_DEFAULT = "7687"

# Not configurable via environment variables
NEO4J_SCHEME_DEFAULT = "bolt"
NEO4J_MAX_CONNECTION_POOL_SIZE_DEFAULT = 10
# there is no server specific config for connection lifetime, this is client only config.
# default = 3600 seconds
NEO4J_MAX_CONNECTION_LIFETIME_DEFAULT = 3600


class GraphDB:
    """
    Async Neo4j Graph Database connection manager with connection pooling.
    Implements singleton pattern for application-wide database access.
    https://neo4j.com/docs/api/python-driver/current/async_api.html#
    """

    _instance = None
    _driver: Optional[AsyncDriver] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(GraphDB, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the GraphDB instance."""
        # Get logger instance (logging is setup in main.py)
        self.logger = logging.getLogger(__name__)

    async def verify_connectivity(self):
        """Verify that the driver can connect to the database."""
        if self._driver is None:
            raise RuntimeError("Driver not initialized. Call init() first.")

        async with self._driver.session(database=self.database) as session:
            result = await session.run("RETURN 1 as test")
            record = await result.single()
            if record["test"] != 1:
                raise RuntimeError("Database connectivity test failed")

    async def init(
        self,
        host: str = None,
        port: int = None,
        username: str = None,
        password: str = None,
        database: str = None,
        max_connection_lifetime: int = NEO4J_MAX_CONNECTION_LIFETIME_DEFAULT,
        max_connection_pool_size: int = NEO4J_MAX_CONNECTION_POOL_SIZE_DEFAULT,
        **kwargs,
    ):
        """
        Initialize the Neo4j async driver with connection pooling.
        Verifies connectivity to the database.

        Args:
            host: Neo4j host (default: from NEO4J_HOST or 'localhost')
            port: Neo4j port (default: from NEO4J_PORT or 7687)
            username: Neo4j username (default: from NEO4J_USERNAME or None for no auth)
            password: Neo4j password (default: from NEO4J_PASSWORD or None for no auth)
            database: Neo4j database name (default: from NEO4J_DATABASE or set default)
            max_connection_lifetime: Max lifetime of connections in seconds
            max_connection_pool_size: Maximum number of connections in pool
            **kwargs: Additional driver configuration options

        Note:
            If both username and password are None/empty, connects without authentication.
        """
        if self._driver is not None:
            self.logger.warning("Driver already initialized. Skipping initialization.")
            return

        # Get connection parameters from arguments or environment variables
        host = host or os.getenv("NEO4J_HOST", NEO4J_HOST_DEFAULT)
        port = port or int(os.getenv("NEO4J_PORT", NEO4J_PORT_DEFAULT))
        username = username or os.getenv("NEO4J_USERNAME")
        password = password or os.getenv("NEO4J_PASSWORD")
        self.database = database or os.getenv("NEO4J_DATABASE", NEO4J_DATABASE_DEFAULT)
        scheme = NEO4J_SCHEME_DEFAULT

        # Construct URI from host, port, and scheme
        uri = f"{scheme}://{host}:{port}"

        # Determine authentication
        auth = None
        if username and password:
            auth = (username, password)
            self.logger.debug(f"Connecting to Neo4j at {uri} with authentication")
        else:
            self.logger.debug(f"Connecting to Neo4j at {uri} without authentication")

        try:
            # Create async driver with connection pooling configuration
            self._driver = AsyncGraphDatabase.driver(
                uri,
                auth=auth,
                max_connection_lifetime=max_connection_lifetime,
                max_connection_pool_size=max_connection_pool_size,
                **kwargs,
            )

            # Verify connectivity
            try:
                await self.verify_connectivity()
                self.logger.info("Successfully connected to Neo4j database")
            except Exception as e:
                self.logger.error(f"Failed to verify connectivity: {e}")
                raise

        except (ServiceUnavailable, AuthError) as e:
            self.logger.error(f"Failed to connect to Neo4j: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during Neo4j initialization: {e}")
            raise

        self.logger.info(f"Successfully connected to database at {uri}")

    @asynccontextmanager
    async def get_session(self, **session_config):
        """
        Get an async session with automatic cleanup.

        Args:
            **session_config: Additional session configuration options

        Yields:
            AsyncSession: Neo4j async session

        Example:
            async with graph_db.get_session() as session:
                result = await session.run("MATCH (n) RETURN count(n)")
        """
        if self._driver is None:
            raise RuntimeError("Driver not initialized. Call init() first.")

        session = self._driver.session(database=self.database, **session_config)
        try:
            yield session
        except Exception as e:
            self.logger.error(f"Session error: {e}")
            raise
        finally:
            await session.close()

    async def node_exists(self, node):
        """Check if a node exists in the database.

        Args:
            node: Node object to check

        Returns:
            tuple: (exists: bool, node_data: dict or None) - Returns (True, node_data) if node exists,
                  (False, None) if it doesn't exist
        """
        if not node:
            return False, None

        try:
            exists_query, exists_params = node.to_cypher_exists()
            async with self.get_session() as session:
                result = await session.run(exists_query, **exists_params)
                record = await result.single()
                if record:
                    node_data = record["n"]
                    self.logger.debug(f"Found existing node - ID: {node.id}, ")
                    return True, node_data

            return False, None

        except Exception as e:
            self.logger.error(f"Error checking if edge exists: {e}", exc_info=True)
            return False, None

    async def edge_exists(self, edge):
        """Check if an edge exists in the database.

        Args:
            edge: Edge object to check

        Returns:
            tuple: (exists: bool, edge_data: dict or None) - Returns (True, edge_data) if edge exists,
                  (False, None) if it doesn't exist
        """
        if not edge:
            return False, None

        try:
            exists_query, exists_params = edge.to_cypher_exists()
            async with self.get_session() as session:
                result = await session.run(exists_query, **exists_params)
                record = await result.single()
                if record:
                    edge_data = record["r"]
                    self.logger.debug(f"Found existing edge - ID: {edge.id}, ")
                    return True, edge_data

            return False, None

        except Exception as e:
            self.logger.error(f"Error checking if edge exists: {e}", exc_info=True)
            return False, None

    async def _check_nodes_exist(self, tx, nodes):
        """Check if any nodes already exist in the database.

        Args:
            tx: The current transaction
            nodes: List of Node objects to check

        Returns:
            List[str]: List of IDs of nodes that already exist
        """
        existing_nodes = []
        for node in nodes or []:
            exists_query, exists_params = node.to_cypher_exists()
            result = await tx.run(exists_query, **exists_params)
            if await result.single():
                existing_nodes.append(node.id)
        return existing_nodes

    async def _check_edges_exist(self, tx, edges):
        """Check if any edges already exist in the database.

        Args:
            tx: The current transaction
            edges: List of Edge objects to check

        Returns:
            List[str]: List of IDs of edges that already exist
        """
        existing_edges = []
        for edge in edges or []:
            exists_query, exists_params = edge.to_cypher_exists()
            result = await tx.run(exists_query, **exists_params)
            if await result.single():
                existing_edges.append(edge.id)
        return existing_edges

    async def save(self, nodes=None, edges=None, force_replace=False):
        """
        Save nodes and edges in a single transaction.
        Checks for node existence before creating them to prevent duplicates.

        Args:
            nodes: List of Node objects
            edges: List of Edge objects
            force_replace: bool - if True, force replace existing nodes and edges

        Returns:
            bool: True if all operations were successful, False otherwise
        """
        self.logger.debug(f"Starting save with {len(nodes or [])} nodes and {len(edges or [])} edges")

        if not nodes and not edges:
            self.logger.warning("No nodes or edges provided for save")
            return True, "No nodes or edges provided for save"

        try:
            # Get a session with a transaction
            async with self.driver.session(database=self.database) as session:
                # Start a transaction
                tx = await session.begin_transaction()
                try:
                    existing_nodes = await self._check_nodes_exist(tx, nodes)
                    existing_edges = await self._check_edges_exist(tx, edges)
                    if not force_replace:
                        if existing_nodes or existing_edges:
                            error_msg = ""
                            if existing_nodes:
                                error_msg += f"Nodes already exist with IDs: {', '.join(existing_nodes)}."
                            if existing_edges:
                                error_msg += f"Edges already exist with IDs: {', '.join(existing_edges)}."
                            error_msg += " Use force_replace: true to recreate"
                            return False, error_msg
                    else:
                        self.logger.info("******* Force replace enabled, deleting existing nodes and edges ********")
                        # Find nodes to delete (those that exist in both existing_nodes and nodes)
                        nodes_to_delete = [n for n in nodes if n.id in existing_nodes] if nodes else []
                        # Delete existing nodes and associated edges
                        for node in nodes_to_delete:
                            cypher, params = node.to_cypher_delete()
                            self.logger.info(f"Deleting node {node.id}")
                            self.logger.debug(f"Cypher: {node.to_executable_cypher(cypher, params)}")
                            result = await tx.run(cypher, **params)
                            self.logger.info(f"Node {node.id} and associated edges deleted")

                    self.logger.info("******* Creating nodes ********")
                    # Create nodes
                    for node in nodes or []:
                        cypher, params = node.to_cypher_create()
                        self.logger.info(node.to_executable_cypher(cypher, params))
                        result = await tx.run(cypher, **params)
                        self.logger.debug(f"Node {node.id} save result: {result}")

                    # Create edges (after all nodes are saved)
                    # If associated nodes do not exist raise an exception
                    self.logger.info("******* Creating edges ********")
                    for edge in edges or []:
                        cypher, params = edge.to_cypher_create()
                        self.logger.info(edge.to_executable_cypher(cypher, params))
                        result = await tx.run(cypher, **params)
                        self.logger.debug(f"Edge {edge.id} save result: {result}")

                    # If we get here, commit the transaction
                    await tx.commit()
                    self.logger.info(f"Successfully saved {len(nodes)} nodes and {len(edges)} edges")

                    return True, f"Saved {len(nodes)} nodes and {len(edges)} edges"

                except Exception as e:
                    self.logger.error(f"Save Transaction failed: {e}", exc_info=True)
                    if tx:
                        await tx.rollback()
                        self.logger.debug("Save Transaction rolled back")
                    raise

        except Exception as e:
            self.logger.error(f"Error in save operation: {e}", exc_info=True)
            raise  # Re-raise the exception

    async def delete(self, nodes):
        """
        Delete nodes and associated edges in a single transaction.

        Args:
            nodes: List of Node objects
        """
        try:
            # Get a session with a transaction
            async with self.driver.session(database=self.database) as session:
                # Start a transaction
                tx = await session.begin_transaction()
                try:
                    # Delete all nodes
                    for node in nodes or []:
                        cypher, params = node.to_cypher_delete()
                        self.logger.info(node.to_executable_cypher(cypher, params))
                        await tx.run(cypher, **params)

                    # If we get here, commit the transaction
                    await tx.commit()
                    self.logger.info(f"Successfully deleted {len(nodes)} nodes and associated edges")
                    return True, f"Deleted {len(nodes)} nodes and associated edges"

                except Exception as e:
                    self.logger.error(f"Delete Transaction failed: {e}")
                    await tx.rollback()
                    raise  # Re-raise the exception

        except Exception as e:
            self.logger.error(f"Delete Session error: {e}")
            raise  # Re-raise the exception

    async def execute_query(
        self, query: str, parameters: Dict[str, Any] = None, **session_config
    ) -> List[Dict[str, Any]]:
        """
        Execute a Cypher query and return results.

        Args:
            query: Cypher query string
            parameters: Query parameters dictionary
            **session_config: Additional session configuration

        Returns:
            List of result records as dictionaries
        """
        parameters = parameters or {}

        async with self.get_session(**session_config) as session:
            result = await session.run(query, parameters)
            records = []
            async for record in result:
                records.append(dict(record))
            return records

    async def close(self):
        """Close the driver and all connections."""
        if self._driver is not None:
            await self._driver.close()
            self._driver = None
            self.logger.info("Neo4j driver closed")

    @property
    def driver(self) -> AsyncDriver:
        """Get the driver instance."""
        if self._driver is None:
            raise RuntimeError("Driver not initialized. Call init() first.")
        return self._driver

    @property
    def is_connected(self) -> bool:
        """Check if the driver is initialized and connected."""
        return self._driver is not None

    async def query(self, nodes, query_criteria: QueryCriteria) -> tuple[bool, list, str]:
        """
        Query the graph database.
        If query_type="neighbor", query for neighbors of the given nodes.

        Args:
            nodes: List of Node objects to be used for querying
            query_criteria: Dictionary containing the query criteria

        Returns:
            Tuple containing (success: bool, results: list, msg: str) where:
                - success: Boolean indicating if the operation was successful
                - results: List of query results (empty if error)
                - msg: Status or error message

        Raises:
            ValueError: If input validation fails
        """
        # Ensure nodes is a list (not a tuple containing a list)
        if isinstance(nodes, tuple) and len(nodes) == 1 and isinstance(nodes[0], list):
            nodes = nodes[0]
        elif not isinstance(nodes, list):
            nodes = [nodes]  # Convert single node to list for consistent processing

        query_type = query_criteria.query_type.lower()
        results = []

        try:
            if query_type == QUERY_TYPE_NEIGHBOUR:
                # First, check if all nodes exist
                missing_nodes = []
                for node in nodes:
                    if not hasattr(node, "id") or not node.id:
                        raise ValueError("All nodes must have an ID for querying")

                    exists, _ = await self.node_exists(node)
                    if not exists:
                        missing_nodes.append(node.id)

                if missing_nodes:
                    return False, [], f"Nodes not found: {', '.join(missing_nodes)}"

                for node in nodes:
                    try:
                        query, params = node.to_cypher_neighbor_query()
                        self.logger.info(f"Executing neighbor query: {node.to_executable_cypher(query, params)}")

                        # Execute the query
                        async with self.get_session() as session:
                            result = await session.run(query, **params)
                            record = await result.single()

                            if not record:
                                self.logger.warning(f"No results found for node {node.id}")
                                results.append({"node": {"id": node.id}, "relationships": [], "neighbors": []})
                                continue

                            # Extract the node, relationships, and neighbors
                            node_data = dict(record[0])  # The main node
                            relationships = [dict(rel) for rel in record[1]]  # All relationships
                            neighbors = [dict(n) for n in record[2]]  # All neighbor nodes

                            results.append({"node": node_data, "relationships": relationships, "neighbors": neighbors})
                    except Exception as e:
                        self.logger.error(f"Error querying node {getattr(node, 'id', 'unknown')}: {str(e)}")
                        results.append(
                            {
                                "node": {"id": getattr(node, "id", "unknown")},
                                "error": str(e),
                                "relationships": [],
                                "neighbors": [],
                            }
                        )

                success_count = len([r for r in results if "error" not in r])
                failed_nodes = [r["node"]["id"] for r in results if "error" in r]

                msg = f"Successfully queried neighbours for {success_count} of {len(nodes)} nodes"
                if failed_nodes:
                    msg += f" (failed nodes: {', '.join(map(str, failed_nodes))})"

                return True, results, msg

            else:
                error_msg = f"Unsupported query type: {query_type}"
                self.logger.error(error_msg)

        except Exception as e:
            error_msg = f"Error in query operation: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            raise  # Re-raise the exception
