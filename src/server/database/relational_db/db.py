import os
from typing import Optional
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool


class RelationalDB:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RelationalDB, cls).__new__(cls)
            cls._instance._engine = None
            cls._instance._session_factory = None
        return cls._instance

    def __init__(self):
        # __init__ is called every time, but we only want to initialize once
        pass

    def init(self, db_name: str = None, user: str = None, password: str = None, host: str = None, port: str = None):
        """Initialize the database connection and sessionmaker.

        Args:
            db_name: Database name (default: from POSTGRES_DB or 'postgresDB')
            user: Database user (default: from POSTGRES_USER or 'postgresUser')
            password: Database password (default: from POSTGRES_PASSWORD or 'postgresPW')
            host: Database host (default: from POSTGRES_HOST or 'localhost')
            port: Database port (default: from POSTGRES_PORT or '5455')
        """
        if self._engine is None or self._session_factory is None:
            # Get connection parameters from arguments or environment variables
            db_name = db_name or os.getenv("POSTGRES_DB", "tkf_relational_db")
            user = user or os.getenv("POSTGRES_USER", "postgresUser")
            password = password or os.getenv("POSTGRES_PASSWORD", "postgresPW")
            host = host or os.getenv("POSTGRES_HOST", "localhost")
            port = port or os.getenv("POSTGRES_PORT", "5455")

            # Create connection URL
            sync_url = f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

            # Create sync engine for psycopg2
            self._engine = create_engine(
                sync_url,
                echo=os.getenv("DB_ECHO", "False").lower() == "true",
                poolclass=QueuePool,
                pool_pre_ping=True,
                pool_recycle=300,
                pool_size=5,
                max_overflow=10,
                pool_timeout=30,
            )

            # Create session factory
            self._session_factory = sessionmaker(
                bind=self._engine, autocommit=False, autoflush=False, expire_on_commit=False
            )

    def get_session(self) -> Session:
        """Get a database session."""
        if self._session_factory is None:
            raise RuntimeError("Database not initialized. Call init() first.")

        session = self._session_factory()
        try:
            return session
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

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
