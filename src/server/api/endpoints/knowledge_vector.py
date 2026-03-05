from fastapi import APIRouter, status, Request, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from server.schemas.knowledge_vector import (
    KnowledgeVectorStoreOnboardRequest,
    KnowledgeVectorStoreOnboardResponse,
    KnowledgeVectorStoreOnboardDeleteRequest,
    KnowledgeVectorStoreOnboardDeleteResponse,
    KnowledgeVectorStoreRequest,
    KnowledgeVectorStoreResponse,
    KnowledgeVectorQueryRequest,
    KnowledgeVectorQueryResponse,
    KnowledgeVectorDeleteRequest,
    KnowledgeVectorDeleteResponse,
    ResponseStatus,
)
from server.services.knowledge_vector import knowledge_vector_service

router = APIRouter()
internal_router = APIRouter()


@router.post(
    "/stores/{store_id}",
    response_model=KnowledgeVectorStoreOnboardResponse,
    responses={
        201: {"description": "Knowledge vector store onboarded successfully"},
        400: {
            "description": "Bad request - validation error (missing required fields, invalid data format, or business logic validation failure)"
        },
        404: {"description": "Not found"},
        500: {"description": "Internal server error - unexpected system failure"},
    },
)
def onboard_store(store_id: str, data: KnowledgeVectorStoreOnboardRequest):
    """
    Creates essential entities for the vector store to function and provides partiioning by workspace.
    """
    response = knowledge_vector_service.onboard(store_id, data)

    if response.status == ResponseStatus.SUCCESS:
        status_code = status.HTTP_201_CREATED
    elif response.status == ResponseStatus.VALIDATION_ERROR:
        status_code = status.HTTP_400_BAD_REQUEST
    elif response.status == ResponseStatus.NOT_FOUND:
        status_code = status.HTTP_404_NOT_FOUND
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(content=response.model_dump(), status_code=status_code)


@router.delete(
    "/stores/{store_id}",
    response_model=KnowledgeVectorStoreOnboardDeleteResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Knowledge graph data successfully deleted"},
        400: {
            "description": "Bad request - validation error (missing required fields, invalid data format, or business logic validation failure)"
        },
        404: {"description": "Not found"},
        500: {"description": "Internal server error - unexpected system failure"},
    },
)
def onboard_store_delete(store_id: str, data: KnowledgeVectorStoreOnboardDeleteRequest):
    """
    Delete a partition of the vector knowledge store and associated entities created during onboarding of the store.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Vector knowledge store deletion is currently supported as an *internal API*",
    )


@router.post(
    "",
    response_model=KnowledgeVectorStoreResponse,
    responses={
        201: {"description": "Knowledge vector data successfully created/updated"},
        400: {
            "description": "Bad request - validation error (missing required fields, invalid data format, or business logic validation failure)"
        },
        404: {"description": "Not found"},
        500: {"description": "Internal server error - unexpected system failure"},
    },
)
def upsert_vector_store(data: KnowledgeVectorStoreRequest):
    """
    upsert entity in the vector knowledge store
    """
    response = knowledge_vector_service.create_vector_store(data)

    if response.status == ResponseStatus.SUCCESS:
        status_code = status.HTTP_201_CREATED
    elif response.status == ResponseStatus.VALIDATION_ERROR:
        status_code = status.HTTP_400_BAD_REQUEST
    elif response.status == ResponseStatus.NOT_FOUND:
        status_code = status.HTTP_404_NOT_FOUND
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(content=response.model_dump(), status_code=status_code)


@router.delete(
    "",
    response_model=KnowledgeVectorDeleteResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Knowledge graph data successfully deleted"},
        400: {
            "description": "Bad request - validation error (missing required fields, invalid data format, or business logic validation failure)"
        },
        404: {"description": "Not found"},
        500: {"description": "Internal server error - unexpected system failure"},
    },
)
def delete_vector_store(data: KnowledgeVectorDeleteRequest):
    """
    Delete an entity from the vector knowledge store
    """
    response = knowledge_vector_service.delete_vector_store(data)

    if response.status == ResponseStatus.SUCCESS:
        status_code = status.HTTP_200_OK
    elif response.status == ResponseStatus.VALIDATION_ERROR:
        status_code = status.HTTP_400_BAD_REQUEST
    elif response.status == ResponseStatus.NOT_FOUND:
        status_code = status.HTTP_404_NOT_FOUND
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(content=response.model_dump(), status_code=status_code)


@router.post(
    "/query",
    response_model=KnowledgeVectorQueryResponse,
    responses={
        200: {"description": "Query executed successfully"},
        400: {"description": "Bad request"},
        404: {"description": "Not found"},
        500: {"description": "Internal server error - unexpected system failure"},
    },
)
def query_vector_store(data: KnowledgeVectorQueryRequest):
    """
    Query entities from the vector knowledge store
    """
    response = knowledge_vector_service.query_vector_store(data)

    if response.status == ResponseStatus.SUCCESS:
        status_code = status.HTTP_200_OK
    elif response.status == ResponseStatus.VALIDATION_ERROR:
        status_code = status.HTTP_400_BAD_REQUEST
    elif response.status == ResponseStatus.NOT_FOUND:
        status_code = status.HTTP_404_NOT_FOUND
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(content=response.model_dump(), status_code=status_code)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors specifically for knowledge vector endpoints."""

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
        # Query endpoint - use KnowledgeVectorQueryResponse
        response = KnowledgeVectorQueryResponse(status=ResponseStatus.VALIDATION_ERROR, message=message)
    elif method == "POST" and path.endswith("/stores/onboard"):
        # Onboard endpoint - use KnowledgeVectorStoreOnboardResponse
        response = KnowledgeVectorStoreOnboardResponse(status=ResponseStatus.VALIDATION_ERROR, message=message)
    elif method == "DELETE":
        # Delete endpoint - use KnowledgeVectorDeleteResponse
        response = KnowledgeVectorDeleteResponse(status=ResponseStatus.VALIDATION_ERROR, message=message)
    else:
        # Store endpoint (POST without /query or /onboard) - use KnowledgeVectorStoreResponse
        response = KnowledgeVectorStoreResponse(status=ResponseStatus.VALIDATION_ERROR, message=message)

    return JSONResponse(content=response.model_dump(), status_code=status.HTTP_400_BAD_REQUEST)


@internal_router.delete(
    "/stores/{store_id}",
    response_model=KnowledgeVectorStoreOnboardDeleteResponse,
    status_code=status.HTTP_200_OK,
    responses={
        200: {"description": "Knowledge graph data successfully deleted"},
        400: {
            "description": "Bad request - validation error (missing required fields, invalid data format, or business logic validation failure)"
        },
        404: {"description": "Not found"},
        500: {"description": "Internal server error - unexpected system failure"},
    },
)
def internal_delete_vector_store(store_id: str, data: KnowledgeVectorStoreOnboardDeleteRequest):
    """
    Delete a partition of the vector knowledge store and associated entities created during onboarding of the store.
    """
    response = knowledge_vector_service.internal_delete_vector_store(store_id, data)

    if response.status == ResponseStatus.SUCCESS:
        status_code = status.HTTP_200_OK
    elif response.status == ResponseStatus.VALIDATION_ERROR:
        status_code = status.HTTP_400_BAD_REQUEST
    elif response.status == ResponseStatus.NOT_FOUND:
        status_code = status.HTTP_404_NOT_FOUND
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(content=response.model_dump(), status_code=status_code)
