import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from server.common import service_name
from server.api.exception_handlers import (
    validation_exception_handler,
)
from fastapi.exceptions import RequestValidationError


def create_app(*, lifespan):
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

    Instrumentator().instrument(app).expose(app, endpoint="/metrics")

    app.add_exception_handler(
        RequestValidationError, validation_exception_handler
    )

    @app.get("/health")
    def health():
        return {"status": "healthy"}

    return app
