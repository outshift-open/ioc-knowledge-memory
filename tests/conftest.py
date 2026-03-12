"""
Pytest configuration for knowledge_memory tests.

This file configures pytest for running integration tests.
"""

import sys
import os
import pytest

# Add src directory to Python path for imports
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
sys.path.insert(0, src_path)


@pytest.fixture(scope="session", autouse=True)
def initialize_database():
    """Initialize database connection before running tests."""
    from knowledge_memory.server.database.connection import ConnectDB

    # Use CI environment variable or default to localhost
    db_host = os.environ.get("POSTGRES_HOST", "localhost")
    db_port = os.environ.get("POSTGRES_PORT", "5456")

    # Initialize database connection with credentials
    db = ConnectDB()
    db.init(
        db_name="ioc-knowledge-db",
        user="postgresUser",
        password="postgresPW",
        host=db_host,
        port=db_port
    )

    yield

    # Cleanup after all tests
    db.close()
