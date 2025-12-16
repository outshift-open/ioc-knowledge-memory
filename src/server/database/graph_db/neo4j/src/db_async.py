import os
import logging
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager
from neo4j import AsyncGraphDatabase, AsyncDriver
from neo4j.exceptions import ServiceUnavailable, AuthError

# Used when environment variables are not configured
NEO4J_DATABASE_DEFAULT = "tkf"
NEO4J_HOST_DEFAULT = "localhost"
NEO4J_PORT_DEFAULT = "7687"

# Not configurable via environment variables
NEO4J_SCHEME_DEFAULT = "bolt"
NEO4J_MAX_CONNECTION_POOL_SIZE_DEFAULT = 10
# there is no server specific config for connection lifetime, this is client only config.
NEO4J_MAX_CONNECTION_LIFETIME_DEFAULT = 3600


class GraphDB:
    """
    Async Neo4j Graph Database connection manager with connection pooling.
    Implements singleton pattern for application-wide database access.
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
            await self.verify_connectivity()

        except (ServiceUnavailable, AuthError) as e:
            self.logger.error(f"Failed to connect to Neo4j: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during Neo4j initialization: {e}")
            raise

        self.logger.info(f"Successfully connected to database at {uri}")

    async def verify_connectivity(self):
        """Verify that the driver can connect to the database."""
        if self._driver is None:
            raise RuntimeError("Driver not initialized. Call init() first.")

        async with self._driver.session(database=self.database) as session:
            result = await session.run("RETURN 1 as test")
            record = await result.single()
            if record["test"] != 1:
                raise RuntimeError("Database connectivity test failed")

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
