import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from server.api.api import api_router
from server.database.postgres.db import RelationalDB

from server.common import service_name


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan events."""
    # Startup
    logger = logging.getLogger(__name__)
    logger.info("Initializing database connection...")
    
    db = RelationalDB()
    db.init()
    
    logger.info("Database initialized successfully")
    
    yield
    
    # Shutdown
    logger.info("Closing database connection...")
    db.close()
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


@app.get("/env")
def env_var():
    return {
        "service": "ci-tkf-data-logic-svc",
        "environment_variables": {
            "CONFIGMAP_TEST": os.environ.get("CONFIGMAP_TEST"),
            "CONFIGMAP_DEFAULT_EXAMPLE": os.environ.get("CONFIGMAP_DEFAULT_EXAMPLE"),
            "CONFIGMAP_OVERLAY_EXAMPLE": os.environ.get("CONFIGMAP_OVERLAY_EXAMPLE"),
            "APPLICATION_VERSION": os.environ.get("APPLICATION_VERSION"),
            "MOCK_DB_UPTIME": os.environ.get("MOCK_DB_UPTIME"),
            "MOCK_FOO_UPTIME": os.environ.get("MOCK_FOO_UPTIME"),
        },
    }


################################################
# Service-Specific API Endpoints
################################################
# Register API routes
app.include_router(api_router, prefix="/api")

if __name__ == "__main__":
    import uvicorn

    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=getattr(logging, log_level))

    logger = logging.getLogger(__name__)
    version = os.environ.get("APPLICATION_VERSION")
    logger.info(f"Starting up the '{service_name}' FastAPI app! Version: '{version}'")

    port = int(os.environ.get("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)
