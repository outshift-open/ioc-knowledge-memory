"""
Knowledge Graph - Direct function interface to knowledge graph operations.

Direct, in-process interface to knowledge graph operations without HTTP overhead.

Usage:
    from knowledge_memory import upsert_knowledge_graph, query_knowledge_graph

    response = upsert_knowledge_graph(
        mas_id="agent-1",
        wksp_id="workspace-1",
        memory_type="Semantic",
        concepts=[{"id": "c1", "name": "Python"}],
        relations=[{"id": "r1", "relation": "USES", "node_ids": ["c1", "c2"]}]
    )
"""

from typing import List, Dict, Any, Optional, Literal
from uuid import uuid4
from pydantic import ValidationError as PydanticValidationError

try:
    # Try namespaced import (works when installed as wheel)
    from knowledge_memory.server.services.knowledge_graph import knowledge_graph_service
    from knowledge_memory.server.schemas.knowledge_graph import (
        KnowledgeGraphStoreRequest,
        KnowledgeGraphStoreResponse,
        KnowledgeGraphQueryRequest,
        KnowledgeGraphQueryResponse,
        KnowledgeGraphDeleteRequest,
        KnowledgeGraphDeleteResponse,
    )
except (ImportError, ModuleNotFoundError):
    # Fallback for development (when src/ is in path)
    try:
        from server.services.knowledge_graph import knowledge_graph_service
        from server.schemas.knowledge_graph import (
            KnowledgeGraphStoreRequest,
            KnowledgeGraphStoreResponse,
            KnowledgeGraphQueryRequest,
            KnowledgeGraphQueryResponse,
            KnowledgeGraphDeleteRequest,
            KnowledgeGraphDeleteResponse,
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


def upsert_knowledge_graph(
    mas_id: Optional[str] = None,
    wksp_id: Optional[str] = None,
    memory_type: Optional[Literal["Semantic", "Procedural", "Episodic"]] = None,
    concepts: Optional[List[Dict[str, Any]]] = None,
    relations: Optional[List[Dict[str, Any]]] = None,
    force_replace: bool = False,
    request_id: Optional[str] = None,
) -> KnowledgeGraphStoreResponse:
    """
    Create or update knowledge graph data.

    Args:
        mas_id: Multi-Agent System ID (optional, but either mas_id or wksp_id must be provided)
        wksp_id: Workspace ID (optional, but either mas_id or wksp_id must be provided)
        memory_type: Type of memory - "Semantic", "Procedural", or "Episodic"
        concepts: List of concept dictionaries with keys: id, name, description, attributes, embeddings, tags
        relations: List of relation dictionaries with keys: id, relation, node_ids, attributes, embeddings
        force_replace: If True, replace existing nodes and edges
        request_id: Optional request ID for tracking (auto-generated if not provided)

    Returns:
        KnowledgeGraphStoreResponse: Response object with status and message

    Raises:
        ValidationError: If request validation fails
        OperationFailedError: If operation fails

    Example:
        response = upsert_knowledge_graph(
            mas_id="agent-1",
            wksp_id="workspace-1",
            memory_type="Semantic",
            concepts=[
                {
                    "id": "c1",
                    "name": "Python",
                    "description": "Programming language",
                    "tags": ["language", "programming"]
                }
            ],
            relations=[
                {
                    "id": "r1",
                    "relation": "BUILT_WITH",
                    "node_ids": ["c1", "c2"]
                }
            ]
        )
    """
    request_id = request_id or str(uuid4())
    records = {"concepts": concepts or [], "relations": relations or []} if (concepts or relations) else None

    try:
        request = KnowledgeGraphStoreRequest(
            request_id=request_id,
            records=records,
            memory_type=memory_type,
            mas_id=mas_id,
            wksp_id=wksp_id,
            force_replace=force_replace
        )
    except PydanticValidationError as e:
        raise ValidationError(f"Request validation failed: {str(e)}")

    response = knowledge_graph_service.create_graph_store(request)
    check_response_status(response, "Upsert knowledge graph")

    return response


def query_knowledge_graph(
    mas_id: Optional[str] = None,
    wksp_id: Optional[str] = None,
    concepts: List[Dict[str, str]] = None,
    query_type: Literal["neighbour", "path", "concept"] = "neighbour",
    memory_type: Optional[str] = None,
    depth: Optional[int] = None,
    use_direction: bool = True,
    request_id: Optional[str] = None,
) -> KnowledgeGraphQueryResponse:
    """
    Query knowledge graph data.

    Args:
        mas_id: Multi-Agent System ID (optional, but either mas_id or wksp_id must be provided)
        wksp_id: Workspace ID (optional, but either mas_id or wksp_id must be provided)
        concepts: List of concept dictionaries with 'id' key
            - For "neighbour" queries: exactly 1 concept required
            - For "path" queries: exactly 2 concepts required (source and destination)
            - For "concept" queries: exactly 1 concept required
        query_type: Type of query - "neighbour", "path", or "concept"
        memory_type: Optional memory type filter
        depth: Optional depth for path queries (number of hops)
        use_direction: Whether to use directed relationships in path queries
        request_id: Optional request ID for tracking (auto-generated if not provided)

    Returns:
        KnowledgeGraphQueryResponse: Response with query results

    Raises:
        ValidationError: If request validation fails
        NotFoundError: If concepts or graph not found
        OperationFailedError: If operation fails

    Example:
        # Query neighbors of a concept
        response = query_knowledge_graph(
            mas_id="agent-1",
            wksp_id="workspace-1",
            concepts=[{"id": "c1"}],
            query_type="neighbour"
        )

        # Query path between two concepts
        response = query_knowledge_graph(
            mas_id="agent-1",
            wksp_id="workspace-1",
            concepts=[{"id": "c1"}, {"id": "c2"}],
            query_type="path",
            depth=5
        )
    """
    request_id = request_id or str(uuid4())
    concepts = concepts or []

    try:
        request = KnowledgeGraphQueryRequest(
            request_id=request_id,
            records={"concepts": concepts},
            memory_type=memory_type,
            mas_id=mas_id,
            wksp_id=wksp_id,
            query_criteria={
                "query_type": query_type,
                "depth": depth,
                "use_direction": use_direction
            }
        )
    except PydanticValidationError as e:
        raise ValidationError(f"Request validation failed: {str(e)}")

    response = knowledge_graph_service.query_graph_store(request)
    check_response_status(response, "Query knowledge graph")

    return response


def delete_knowledge_graph(
    mas_id: Optional[str] = None,
    wksp_id: Optional[str] = None,
    concepts: Optional[List[Dict[str, str]]] = None,
    request_id: Optional[str] = None,
) -> KnowledgeGraphDeleteResponse:
    """
    Delete knowledge graph concepts and their relationships.

    Args:
        mas_id: Multi-Agent System ID (optional, but either mas_id or wksp_id must be provided)
        wksp_id: Workspace ID (optional, but either mas_id or wksp_id must be provided)
        concepts: Optional list of concept dictionaries with 'id' key to delete specific concepts.
                 If not provided, deletes all concepts in the graph.
        request_id: Optional request ID for tracking (auto-generated if not provided)

    Returns:
        KnowledgeGraphDeleteResponse: Response object with status and message

    Raises:
        ValidationError: If request validation fails
        OperationFailedError: If operation fails

    Example:
        # Delete specific concepts
        response = delete_knowledge_graph(
            mas_id="agent-1",
            wksp_id="workspace-1",
            concepts=[{"id": "c1"}, {"id": "c2"}]
        )
    """
    request_id = request_id or str(uuid4())
    records = {"concepts": concepts} if concepts else None

    request = KnowledgeGraphDeleteRequest(
        request_id=request_id,
        records=records,
        mas_id=mas_id,
        wksp_id=wksp_id
    )

    response = knowledge_graph_service.delete_graph_store(request)
    check_response_status(response, "Delete knowledge graph")

    return response


def delete_knowledge_graph_internal(
    mas_id: Optional[str] = None,
    wksp_id: Optional[str] = None,
    request_id: Optional[str] = None,
) -> KnowledgeGraphDeleteResponse:
    """
    Internal operation to delete an entire knowledge graph (including schema).

    WARNING: This is a destructive operation that deletes the entire graph.

    Args:
        mas_id: Multi-Agent System ID (optional, but either mas_id or wksp_id must be provided)
        wksp_id: Workspace ID (optional, but either mas_id or wksp_id must be provided)
        request_id: Optional request ID for tracking (auto-generated if not provided)

    Returns:
        KnowledgeGraphDeleteResponse: Response object with status and message

    Raises:
        ValidationError: If request validation fails
        OperationFailedError: If operation fails
    """
    request_id = request_id or str(uuid4())

    request = KnowledgeGraphDeleteRequest(
        request_id=request_id,
        mas_id=mas_id,
        wksp_id=wksp_id
    )

    response = knowledge_graph_service.delete_graph_store_internal(request)
    check_response_status(response, "Delete knowledge graph (internal)")

    return response
