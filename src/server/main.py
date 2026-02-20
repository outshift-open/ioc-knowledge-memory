import logging
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app_logging.logger import setup_logging
from server.api.api import api_router
from server.api.exception_handlers import validation_exception_handler
from server.common import service_name
from server.database.graph_db.agensgraph.src.db import GraphDB as AgensGraphDB

# Load environment variables from .env file in current or parent directories
load_dotenv(override=True)

# Setup logging once for the entire application
setup_logging(service_name)

logger = logging.getLogger(__name__)
logger.info("Environment variables loaded")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""

    try:
        agensgraph_db = AgensGraphDB()
        agensgraph_db.init()

    except Exception as e:
        logger.error(f"Graph Database initialization failed: {str(e)}")
        raise

    logger.info("Database connections initialized")

    yield

    # Shutdown
    logger.info("Closing database connection...")
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

    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
