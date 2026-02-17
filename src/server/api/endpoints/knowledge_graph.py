import json
from server.schemas.knowledge_graph import (
    KnowledgeGraphStoreRequest,
    KnowledgeGraphStoreResponse,
    KnowledgeGraphQueryRequest,
    KnowledgeGraphQueryResponse,
    KnowledgeGraphDeleteRequest,
    KnowledgeGraphDeleteResponse,
    ResponseStatus,
)
from server.services.knowledge_graph import knowledge_graph_service
from fastapi import APIRouter, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from typing import Union
from enum import Enum

router = APIRouter()
internal_router = APIRouter()


@router.post(
    "",
    response_model=KnowledgeGraphStoreResponse,
    responses={
        201: {"description": "Knowledge graph data successfully created/updated"},
        400: {
            "description": "Bad request - validation error (missing required fields, invalid data format, or business logic validation failure)"
        },
        500: {"description": "Internal server error - unexpected system failure"},
    },
)
def create_graph_store(data: KnowledgeGraphStoreRequest):
    """
    Create/update graph knowledge store

    Args:
        data: The knowledge data to store
    """
    response = knowledge_graph_service.create_graph_store(data)

    if response.status == ResponseStatus.SUCCESS:
        status_code = status.HTTP_201_CREATED
    elif response.status == ResponseStatus.VALIDATION_ERROR:
        status_code = status.HTTP_400_BAD_REQUEST
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(content=response.model_dump(), status_code=status_code)


@router.delete(
    "",
    response_model=KnowledgeGraphDeleteResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Knowledge graph data successfully deleted"},
        400: {
            "description": "Bad request - validation error (missing required fields, invalid data format, or business logic validation failure)"
        },
        500: {"description": "Internal server error - unexpected system failure"},
    },
)
def delete_graph_store(data: KnowledgeGraphDeleteRequest):
    """
    Delete a graph knowledge store
    """
    response = knowledge_graph_service.delete_graph_store(data)
    if response.status == ResponseStatus.SUCCESS:
        status_code = status.HTTP_200_OK
    elif response.status == ResponseStatus.VALIDATION_ERROR:
        status_code = status.HTTP_400_BAD_REQUEST
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(content=response.model_dump(), status_code=status_code)


@router.post(
    "/query",
    response_model=KnowledgeGraphQueryResponse,
    responses={
        200: {"description": "Query executed successfully - returns matching knowledge graph data"},
        400: {
            "description": "Bad request - validation error (invalid query parameters, wrong concept count for query type, missing required fields)"
        },
        404: {"description": "Not found - requested concepts or relationships do not exist in the knowledge graph"},
        500: {"description": "Internal server error - unexpected system failure"},
    },
)
def query_graph_store(data: KnowledgeGraphQueryRequest):
    """
    Query graph knowledge store
    """
    response = knowledge_graph_service.query_graph_store(data)

    if response.status == ResponseStatus.SUCCESS:
        status_code = status.HTTP_200_OK
    elif response.status == ResponseStatus.VALIDATION_ERROR:
        status_code = status.HTTP_400_BAD_REQUEST
    elif response.status == ResponseStatus.NOT_FOUND:
        status_code = status.HTTP_404_NOT_FOUND
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(content=response.model_dump(), status_code=status_code)


@internal_router.delete(
    "",
    response_model=KnowledgeGraphDeleteResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Knowledge graph data successfully deleted (internal endpoint)"},
        400: {
            "description": "Bad request - validation error (missing required fields, invalid data format, or business logic validation failure)"
        },
        500: {"description": "Internal server error - unexpected system failure"},
    },
)
def internal_delete_graph_store(data: KnowledgeGraphDeleteRequest):
    """
    Internal API to Delete a graph knowledge store
    """
    response = knowledge_graph_service.delete_graph_store_internal(data)
    if response.status == ResponseStatus.SUCCESS:
        status_code = status.HTTP_200_OK
    elif response.status == ResponseStatus.VALIDATION_ERROR:
        status_code = status.HTTP_400_BAD_REQUEST
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(content=response.model_dump(), status_code=status_code)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors specifically for knowledge graph endpoints."""

    # Extract validation error details
    error_messages = []

    for error in exc.errors():
        field_path = " -> ".join(str(loc) for loc in error["loc"])
        error_messages.append(f"{field_path}: {error['msg']}")

    # Create comprehensive message
    message = f"Request validation failed: {'; '.join(error_messages)}"

    # Determine the appropriate response model based on the request path and method
    path = request.url.path
    method = request.method

    if method == "POST" and path.endswith("/query"):
        # Query endpoint - use KnowledgeGraphQueryResponse
        response = KnowledgeGraphQueryResponse(status=ResponseStatus.VALIDATION_ERROR, message=message)
    elif method == "DELETE":
        # Delete endpoint - use KnowledgeGraphDeleteResponse
        response = KnowledgeGraphDeleteResponse(status=ResponseStatus.VALIDATION_ERROR, message=message)
    else:
        # Store endpoint (POST without /query) - use KnowledgeGraphStoreResponse
        response = KnowledgeGraphStoreResponse(status=ResponseStatus.VALIDATION_ERROR, message=message)

    return JSONResponse(content=response.model_dump(), status_code=status.HTTP_400_BAD_REQUEST)
