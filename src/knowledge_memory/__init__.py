"""
Knowledge Memory - Python Library

Direct, in-process access to knowledge memory operations without HTTP overhead.

Modules:
    - knowledge_graph: Graph operations (concepts and relations)
    - knowledge_vector: Vector operations (embeddings and similarity search)

Usage:
    from knowledge_memory import upsert_knowledge_graph, query_knowledge_graph
    from knowledge_memory import onboard_vector_store, upsert_vector_store

For HTTP API (external clients), use REST API at /api/knowledge/*
"""

from knowledge_memory.exceptions import (
    KnowledgeMemoryError,
    ValidationError,
    NotFoundError,
    OperationFailedError,
)

from knowledge_memory.knowledge_graph import (
    upsert_knowledge_graph,
    query_knowledge_graph,
    delete_knowledge_graph,
    delete_knowledge_graph_internal,
)

from knowledge_memory.knowledge_vector import (
    onboard_vector_store,
    upsert_vector_store,
    query_vector_store,
    delete_vector,
    delete_vector_store_internal,
)

__all__ = [
    # Exceptions
    "KnowledgeMemoryError",
    "ValidationError",
    "NotFoundError",
    "OperationFailedError",
    # Knowledge Graph
    "upsert_knowledge_graph",
    "query_knowledge_graph",
    "delete_knowledge_graph",
    "delete_knowledge_graph_internal",
    # Knowledge Vector
    "onboard_vector_store",
    "upsert_vector_store",
    "query_vector_store",
    "delete_vector",
    "delete_vector_store_internal",
]

__version__ = "1.0.0"
