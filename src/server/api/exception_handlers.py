from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Convert Pydantic request validation errors to required response format.

    This handler routes knowledge graph requests to their specific handler
    and uses FastAPI's default handling for other endpoints.
    """

    if request.url.path.startswith("/api/knowledge/graph"):
        # Import here to avoid circular imports
        from server.api.endpoints.knowledge_graph import validation_exception_handler

        return await validation_exception_handler(request, exc)

    # For non-knowledge-graph requests, let FastAPI handle with default 422 response
    from fastapi.exception_handlers import request_validation_exception_handler

    return await request_validation_exception_handler(request, exc)
