import logging
import os

from dotenv import load_dotenv

from knowledge_memory.app_logging.logger import setup_logging
from server.api.api import api_router
from server.common import service_name
from knowledge_memory.bootstrap.lifespan import create_lifespan
from knowledge_memory.bootstrap.app_factory import create_app

# Load environment variables from .env file in current or parent directories
load_dotenv(override=True)

# Setup logging once for the entire application
setup_logging(service_name)

logger = logging.getLogger(__name__)

provider_config = {
    "provider_name": "ioc-memory-provider",
    "description": "Memory provider with support for graph and vector data.",
    "service_host": os.environ.get("SERVICE_NAME", "ioc-knowledge-memory-svc"),
    "service_port": os.environ.get("PORT", "9003"),
}

lifespan = create_lifespan(
    register=True,
    provider_config=provider_config,
)

app = create_app(lifespan=lifespan)
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
