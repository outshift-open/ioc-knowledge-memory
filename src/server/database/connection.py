import logging
import os
from threading import Lock

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import QueuePool

# Used when environment variables are not configured
IOC_KNOWLEDGE_DB_DEFAULT = "ioc-knowledge-db"
IOC_KNOWLEDGE_DB_HOST_DEFAULT = "localhost"
IOC_KNOWLEDGE_DB_PORT_DEFAULT = "5456"


class ConnectDB:
    """
    Singleton database connection manager with connection pooling.
    Provides shared database engine and session factory for all database operations.
    """

    _instance = None
    _lock = Lock()
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(ConnectDB, cls).__new__(cls)
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
            self.logger.debug("Initializing ConnectDB instance")

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
                db_name = db_name or os.getenv("IOC_KNOWLEDGE_DB", IOC_KNOWLEDGE_DB_DEFAULT)
                user = user or os.getenv("IOC_KNOWLEDGE_DB_USER")
                password = password or os.getenv("IOC_KNOWLEDGE_DB_PASSWORD")
                host = host or os.getenv("IOC_KNOWLEDGE_DB_HOST", IOC_KNOWLEDGE_DB_HOST_DEFAULT)
                port = port or os.getenv("IOC_KNOWLEDGE_DB_PORT", IOC_KNOWLEDGE_DB_PORT_DEFAULT)

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
