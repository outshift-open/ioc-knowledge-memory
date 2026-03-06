import logging
import os
import uuid
from contextlib import asynccontextmanager

import requests
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app_logging.logger import setup_logging
from server.api.api import api_router
from server.api.exception_handlers import validation_exception_handler
from server.common import service_name
from server.database.connection import ConnectDB
from server.database.graph_db.agensgraph.src.db import GraphDB as AgensGraphDB

# Load environment variables from .env file in current or parent directories
load_dotenv(override=True)

# Setup logging once for the entire application
setup_logging(service_name)

logger = logging.getLogger(__name__)
logger.info("Environment variables loaded")


def register_provider():
    """Register this service as a memory provider."""
    svc_url = os.environ.get("MEMORY_PROVIDER_REGISTRATION_URL")
    if not svc_url:
        logger.error("MEMORY_PROVIDER_REGISTRATION_URL environment variable not set")
        raise ValueError("MEMORY_PROVIDER_REGISTRATION_URL environment variable is required")

    url = "http://" + os.environ.get("SERVICE_NAME", "ioc-knowledge-memory-svc") + ":" + os.environ.get("PORT", "9003")
    description = (f"Memory provider with support for graph and vector data. "
                   f"API documentation: {url}/docs")
    # Prepare the request payload
    payload = {
        "memory_provider_name": "ioc-memory-provider",
        "description": description,
        "config": {
            "url": url,
            "shared":"True"
        }
    }

    # Make the POST request
    url = f"{svc_url.rstrip('/')}/api/memory-providers"

    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code == 201:
            logger.info(f"Memory provider registered successfully, Response Body: {response.text}")
        elif response.status_code == 409:
            logger.info(f"Memory provider already registered, Response Body: {response.text}")
        else:
            error_msg = f"Unexpected response status: {response.status_code}, body: {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)

    except requests.exceptions.RequestException as e:
        error_msg = f"Memory Provider Registration failed: {str(e)}"
        logger.error(error_msg)
        raise Exception(error_msg)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""

    # Register as memory-provider (non-critical, continue if it fails)
    try:
        register_provider()
    except Exception as e:
        logger.warning(f"Memory provider registration failed, but continuing startup: {str(e)}")

    try:
        # Initialize database connection
        connect_db = ConnectDB()
        connect_db.init()

        # Initialize graph database
        agensgraph_db = AgensGraphDB()
        agensgraph_db.init()

    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

    logger.info("Database connections initialized")

    yield

    # Shutdown
    logger.info("Closing database connection...")
    connect_db.close()
    agensgraph_db.close()
    logger.info("Database connection closed")


# Create FastAPI app
app = FastAPI(
    title=f"{service_name} API",
    version=os.environ.get("APPLICATION_VERSION", "NOT_FOUND"),
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

instrumentator = Instrumentator()
instrumentator.instrument(app)
instrumentator.expose(app, endpoint="/metrics")

# Add exception handlers
app.add_exception_handler(RequestValidationError, validation_exception_handler)


@app.get("/health")
def health():
    return {"status": "healthy"}


################################################
# Service-Specific API Endpoints
################################################
# Register API routes
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    log_level = os.environ.get("LOG_LEVEL", "DEBUG").upper()
    logging.basicConfig(level=getattr(logging, log_level))

    logger = logging.getLogger(__name__)

    version = os.environ.get("APPLICATION_VERSION")
    logger.info(f"Starting up the '{service_name}' FastAPI app! Version: '{version}'")

    port = int(os.environ.get("PORT", 9003))
    uvicorn.run(app, host="0.0.0.0", port=port)
