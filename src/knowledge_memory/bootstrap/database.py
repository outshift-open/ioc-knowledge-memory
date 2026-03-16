import logging
from knowledge_memory.server.database.connection import ConnectDB
from knowledge_memory.server.database.graph_db.agensgraph.src.db import (
    GraphDB as AgensGraphDB,
)

logger = logging.getLogger(__name__)


class DatabaseManager:
    def __init__(self, db_name: str = None,
                 user: str = None, password: str = None,
                 host: str = None, port: str = None):

        self.connect_db = ConnectDB()
        self.graph_db = AgensGraphDB()

        self.db_name=db_name
        self.user=user
        self.password=password
        self.host=host
        self.port=port

    def start(self):
        logger.info("Initializing databases")

        if all([self.db_name, self.user, self.password, self.host, self.port]):
            self.connect_db.init(
                self.db_name,
                self.user,
                self.password,
                self.host,
                self.port,
            )
            self.graph_db.init(
                self.db_name,
                self.user,
                self.password,
                self.host,
                self.port,
            )
        else:
            # fallback to existing env-based behavior
            self.connect_db.init()
            self.graph_db.init()

    def stop(self):
        logger.info("Closing databases")
        self.connect_db.close()
        self.graph_db.close()
