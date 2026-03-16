import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI

from .database import DatabaseManager
from .provider import register_provider

logger = logging.getLogger(__name__)


def create_lifespan(
    *,
    register: bool = True,
    provider_config: dict | None = None,
):
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        db = DatabaseManager()

        if register and provider_config:
            try:
                register_provider(**provider_config)
            except Exception as exc:
                logger.warning(
                    "Provider registration failed, continuing startup: %s",
                    exc,
                )

        try:
            db.start()
        except Exception:
            logger.exception("Database initialization failed")
            raise

        yield

        db.stop()

    return lifespan
