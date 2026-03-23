# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""
Knowledge Vector - Direct function interface to knowledge vector operations.

Direct, in-process interface to vector operations without HTTP overhead.

Usage:
    from knowledge_memory import onboard_vector_store, upsert_vector_store

    onboard_vector_store(store_id="my-store")
    response = upsert_vector_store(
        wksp_id="workspace-1",
        mas_id="agent-1",
        records=[{"id": "v1", "content": "Text", "embedding": {"data": [0.1, ...]}}]
    )
"""

from typing import List, Dict, Any, Optional, Literal
from uuid import uuid4
from pydantic import ValidationError as PydanticValidationError

try:
    # Try namespaced import (works when installed as wheel)
    from knowledge_memory.server.services.knowledge_vector import knowledge_vector_service
    from knowledge_memory.server.schemas.knowledge_vector import (
        KnowledgeVectorStoreOnboardRequest,
        KnowledgeVectorStoreOnboardResponse,
        KnowledgeVectorStoreRequest,
        KnowledgeVectorStoreResponse,
        KnowledgeVectorQueryRequest,
        KnowledgeVectorQueryResponse,
        KnowledgeVectorDeleteRequest,
        KnowledgeVectorDeleteResponse,
        KnowledgeVectorStoreOnboardDeleteRequest,
        KnowledgeVectorStoreOnboardDeleteResponse,
    )
except (ImportError, ModuleNotFoundError):
    # Fallback for development (when src/ is in path)
    try:
        from server.services.knowledge_vector import knowledge_vector_service
        from server.schemas.knowledge_vector import (
            KnowledgeVectorStoreOnboardRequest,
            KnowledgeVectorStoreOnboardResponse,
            KnowledgeVectorStoreRequest,
            KnowledgeVectorStoreResponse,
            KnowledgeVectorQueryRequest,
            KnowledgeVectorQueryResponse,
            KnowledgeVectorDeleteRequest,
            KnowledgeVectorDeleteResponse,
            KnowledgeVectorStoreOnboardDeleteRequest,
            KnowledgeVectorStoreOnboardDeleteResponse,
        )
    except (ImportError, AttributeError) as e:
        raise ImportError(
            f"Failed to import from 'server' module: {e}. "
            "This likely means you have a conflicting 'server' module. "
            "For development: ensure 'src/' is in PYTHONPATH with both "
            "'knowledge_memory' and 'server' directories available."
        ) from e
from knowledge_memory.exceptions import (
    ValidationError,
    NotFoundError,
    OperationFailedError,
    check_response_status,
)


def onboard_vector_store(
    store_id: str,
    request_id: Optional[str] = None,
) -> KnowledgeVectorStoreOnboardResponse:
    """
    Onboard (initialize) a vector store for a workspace.

    This creates the necessary database schema and tables for storing vector data.
    Must be called before upserting vectors to a new store.

    Args:
        store_id: Unique identifier for the vector store (typically workspace ID)
        request_id: Optional request ID for tracking (auto-generated if not provided)

    Returns:
        KnowledgeVectorStoreOnboardResponse: Response object with status and message

    Raises:
        ValidationError: If request validation fails
        OperationFailedError: If operation fails

    Example:
        response = onboard_vector_store(store_id="workspace-123")
    """
    request_id = request_id or str(uuid4())

    request = KnowledgeVectorStoreOnboardRequest(request_id=request_id)
    response = knowledge_vector_service.onboard(store_id, request)
    check_response_status(response, "Onboard vector store")

    return response


def upsert_vector_store(
    wksp_id: str,
    mas_id: str,
    records: List[Dict[str, Any]],
    request_id: Optional[str] = None,
) -> KnowledgeVectorStoreResponse:
    """
    Upsert (create or update) vector records in the vector store.

    Args:
        wksp_id: Workspace ID (must already be onboarded)
        mas_id: Multi-Agent System ID
        records: List of vector record dictionaries with keys:
            - id (str): Unique identifier for the vector
            - content (str): Text content
            - embedding (dict): Dictionary with 'data' key containing list of floats
        request_id: Optional request ID for tracking (auto-generated if not provided)

    Returns:
        KnowledgeVectorStoreResponse: Response object with status and message

    Raises:
        ValidationError: If request validation fails
        NotFoundError: If workspace not found (needs onboarding first)
        OperationFailedError: If operation fails

    Example:
        response = upsert_vector_store(
            wksp_id="workspace-123",
            mas_id="agent-1",
            records=[
                {
                    "id": "vec1",
                    "content": "Python is a programming language",
                    "embedding": {"data": [0.1, 0.2, 0.3, ..., 0.384]}  # 384 dimensions
                },
                {
                    "id": "vec2",
                    "content": "FastAPI is a web framework",
                    "embedding": {"data": [0.2, 0.3, 0.4, ..., 0.384]}
                }
            ]
        )
    """
    request_id = request_id or str(uuid4())

    try:
        request = KnowledgeVectorStoreRequest(
            request_id=request_id,
            wksp_id=wksp_id,
            mas_id=mas_id,
            records=records
        )
    except PydanticValidationError as e:
        raise ValidationError(f"Request validation failed: {str(e)}")

    response = knowledge_vector_service.create_vector_store(request)
    check_response_status(response, "Upsert vector store")

    return response


def query_vector_store(
    wksp_id: str,
    mas_id: str,
    query_type: Literal[
        "get_by_id",
        "distance_l2",
        "distance_cosine",
        "list_by_wksp_id",
        "list_by_mas_id"
    ],
    vector_id: Optional[str] = None,
    embedding: Optional[List[float]] = None,
    limit: Optional[int] = None,
    request_id: Optional[str] = None,
) -> KnowledgeVectorQueryResponse:
    """
    Query vectors from the vector store.

    Args:
        wksp_id: Workspace ID
        mas_id: Multi-Agent System ID
        query_type: Type of query to execute:
            - "get_by_id": Retrieve specific vector by ID (requires vector_id)
            - "distance_l2": L2 distance similarity search (requires embedding)
            - "distance_cosine": Cosine similarity search (requires embedding)
            - "list_by_wksp_id": List all vectors in workspace
            - "list_by_mas_id": List all vectors in MAS
        vector_id: Vector ID (required for "get_by_id" query type)
        embedding: Embedding vector as list of floats (required for similarity queries)
        limit: Maximum number of results to return
        request_id: Optional request ID for tracking (auto-generated if not provided)

    Returns:
        KnowledgeVectorQueryResponse: Response with query results

    Raises:
        ValidationError: If request validation fails
        NotFoundError: If workspace not found
        OperationFailedError: If operation fails

    Examples:
        # Get vector by ID
        response = query_vector_store(
            wksp_id="workspace-123",
            mas_id="agent-1",
            query_type="get_by_id",
            vector_id="vec1"
        )

        # Similarity search using L2 distance
        response = query_vector_store(
            wksp_id="workspace-123",
            mas_id="agent-1",
            query_type="distance_l2",
            embedding=[0.1, 0.2, 0.3, ..., 0.384],
            limit=5
        )

        # List all vectors in workspace
        response = query_vector_store(
            wksp_id="workspace-123",
            mas_id="agent-1",
            query_type="list_by_wksp_id",
            limit=10
        )
    """
    request_id = request_id or str(uuid4())
    query_criteria = {"query_type": query_type, "limit": limit}

    if vector_id is not None:
        query_criteria["id"] = vector_id
    if embedding is not None:
        query_criteria["embedding"] = {"data": embedding}

    request = KnowledgeVectorQueryRequest(
        request_id=request_id,
        wksp_id=wksp_id,
        mas_id=mas_id,
        query_criteria=query_criteria
    )

    response = knowledge_vector_service.query_vector_store(request)
    check_response_status(response, "Query vector store")

    return response


def delete_vector(
    wksp_id: str,
    mas_id: str,
    vector_id: str,
    soft_delete: bool = True,
    request_id: Optional[str] = None,
) -> KnowledgeVectorDeleteResponse:
    """
    Delete a vector from the vector store.

    Args:
        wksp_id: Workspace ID
        mas_id: Multi-Agent System ID
        vector_id: ID of the vector to delete
        soft_delete: If True, mark as deleted but keep data; if False, permanently delete
        request_id: Optional request ID for tracking (auto-generated if not provided)

    Returns:
        KnowledgeVectorDeleteResponse: Response object with status and message

    Raises:
        ValidationError: If request validation fails
        NotFoundError: If workspace or vector not found
        OperationFailedError: If operation fails

    Example:
        # Soft delete (mark as deleted)
        response = delete_vector(
            wksp_id="workspace-123",
            mas_id="agent-1",
            vector_id="vec1",
            soft_delete=True
        )

        # Hard delete (permanently remove)
        response = delete_vector(
            wksp_id="workspace-123",
            mas_id="agent-1",
            vector_id="vec1",
            soft_delete=False
        )
    """
    request_id = request_id or str(uuid4())

    request = KnowledgeVectorDeleteRequest(
        request_id=request_id,
        wksp_id=wksp_id,
        mas_id=mas_id,
        id=vector_id,
        soft_delete=soft_delete
    )

    response = knowledge_vector_service.delete_vector_store(request)
    check_response_status(response, "Delete vector")

    return response


def delete_vector_store_internal(
    store_id: str,
    request_id: Optional[str] = None,
) -> KnowledgeVectorStoreOnboardDeleteResponse:
    """
    Internal operation to delete an entire vector store (including schema and all data).

    WARNING: This is a destructive operation that permanently deletes the entire store.

    Args:
        store_id: Store ID to delete (typically workspace ID)
        request_id: Optional request ID for tracking (auto-generated if not provided)

    Returns:
        KnowledgeVectorStoreOnboardDeleteResponse: Response object with status and message

    Raises:
        ValidationError: If request validation fails
        NotFoundError: If store not found
        OperationFailedError: If operation fails

    Example:
        response = delete_vector_store_internal(store_id="workspace-123")
    """
    request_id = request_id or str(uuid4())

    request = KnowledgeVectorStoreOnboardDeleteRequest(request_id=request_id)
    response = knowledge_vector_service.internal_delete_vector_store(store_id, request)
    check_response_status(response, "Delete vector store (internal)")

    return response
