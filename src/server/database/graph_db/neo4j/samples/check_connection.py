#!/usr/bin/env python3
"""
Script to validate Neo4j database connection.

Run with:
    PYTHONPATH=/path/to/project/root/src python -m server.database.graph_db.neo4j.samples.check_connection
or
Run (if running from project root) with:
    python -m server.database.graph_db.neo4j.samples.check_connection
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Import defaults from db_async
from ..src.db_async import NEO4J_HOST_DEFAULT, NEO4J_PORT_DEFAULT, NEO4J_DATABASE_DEFAULT

try:
    # Absolute imports (preferred when PYTHONPATH is set correctly)
    from server.database.graph_db.neo4j.src.db_async import GraphDB
    from app_logging.logger import setup_logging
except ImportError:
    print("Error: Could not import modules. Please ensure you've set PYTHONPATH to include the 'src' directory.")
    sys.exit(1)

# Load environment variables from .env file in current or parent directories
load_dotenv(override=True)

# Setup logging using the application's logging configuration
setup_logging("test_check_connection")
logger = logging.getLogger(__name__)


async def validate_neo4j_connection(
    host: str,
    port: int,
    username: str = None,
    password: str = None,
    database: str = None,
) -> bool:
    """
    Validate connection to Neo4j database.

    Args:
        host: Neo4j server hostname or IP
        port: Neo4j server port
        username: Database username (optional if no auth)
        password: Database password (optional if no auth)
        database: Database name
        scheme: Connection scheme (bolt, bolt+s, bolt+ssc)

    Returns:
        bool: True if connection is successful, False otherwise
    """
    logger.info("Testing Neo4j database connection...")

    try:
        # Initialize the database connection
        db = GraphDB()
        await db.init()  # Initializes and Verifies connection
        logger.info("Successfully connected to Neo4j database")

        # Run a test query
        result = await db.execute_query("RETURN 'Connection test successful' as message")
        logger.info(f"Test query result: {result[0]['message']}")

        return True

    except Exception as e:
        logger.error(f"Failed to connect to Neo4j database: {e}")
        return False

    finally:
        # Close the connection
        if "db" in locals():
            await db.close()


async def main():
    host = os.getenv("NEO4J_HOST", NEO4J_HOST_DEFAULT)
    port = int(os.getenv("NEO4J_PORT", NEO4J_PORT_DEFAULT))
    username = os.getenv("NEO4J_USERNAME")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", NEO4J_DATABASE_DEFAULT)

    # Validate connection
    success = await validate_neo4j_connection(
        host=host,
        port=port,
        username=username,
        password=password,
        database=database,
    )

    # Exit with appropriate status code
    exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
