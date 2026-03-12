"""
Integration tests for knowledge_memory library.

Tests the library interface with actual database operations.
Requires: Database running (task docker-compose-up)

Run: pytest tests/test_knowledge_memory.py -v
"""

import pytest
import sys
import os
from uuid import uuid4

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from knowledge_memory import (
    # Graph operations
    upsert_knowledge_graph,
    query_knowledge_graph,
    delete_knowledge_graph,
    # Vector operations
    onboard_vector_store,
    upsert_vector_store,
    query_vector_store,
    delete_vector,
    # Exceptions
    ValidationError,
    NotFoundError,
    OperationFailedError,
)


# Test fixtures
@pytest.fixture
def test_ids():
    """Generate unique IDs for test isolation."""
    return {
        "mas_id": str(uuid4()),
        "wksp_id": str(uuid4()),
    }


@pytest.fixture
def vector_store_id():
    """Generate unique vector store ID."""
    return str(uuid4())


# ============================================================================
# Knowledge Graph Tests
# ============================================================================


def test_graph_create_concepts(test_ids):
    """Test creating concepts in knowledge graph."""
    response = upsert_knowledge_graph(
        mas_id=test_ids["mas_id"],
        wksp_id=test_ids["wksp_id"],
        memory_type="Semantic",
        concepts=[
            {"id": "python", "name": "Python", "description": "Programming language"},
            {"id": "fastapi", "name": "FastAPI", "description": "Web framework"},
        ],
    )
    assert response.status == "success"
    assert "successfully" in response.message.lower()


def test_graph_create_with_relations(test_ids):
    """Test creating concepts with relationships."""
    response = upsert_knowledge_graph(
        mas_id=test_ids["mas_id"],
        wksp_id=test_ids["wksp_id"],
        concepts=[
            {"id": "python", "name": "Python"},
            {"id": "django", "name": "Django"},
        ],
        relations=[
            {"id": "r1", "relation": "BUILT_WITH", "node_ids": ["django", "python"]}
        ],
    )
    assert response.status == "success"


def test_graph_query_concept(test_ids):
    """Test querying a specific concept."""
    # Create concept first
    upsert_knowledge_graph(
        mas_id=test_ids["mas_id"],
        wksp_id=test_ids["wksp_id"],
        concepts=[{"id": "test-concept", "name": "Test", "description": "Testing"}],
    )

    # Query it
    response = query_knowledge_graph(
        mas_id=test_ids["mas_id"],
        wksp_id=test_ids["wksp_id"],
        concepts=[{"id": "test-concept"}],
        query_type="concept",
    )
    assert response.status == "success"
    assert len(response.records) > 0
    assert response.records[0].concepts[0].name == "Test"


def test_graph_query_neighbours(test_ids):
    """Test querying neighbors of a concept."""
    # Create connected concepts
    upsert_knowledge_graph(
        mas_id=test_ids["mas_id"],
        wksp_id=test_ids["wksp_id"],
        concepts=[
            {"id": "center", "name": "Center"},
            {"id": "neighbor", "name": "Neighbor"},
        ],
        relations=[{"id": "r1", "relation": "CONNECTS", "node_ids": ["center", "neighbor"]}],
    )

    # Query neighbors
    response = query_knowledge_graph(
        mas_id=test_ids["mas_id"],
        wksp_id=test_ids["wksp_id"],
        concepts=[{"id": "center"}],
        query_type="neighbour",
    )
    assert response.status == "success"
    assert len(response.records) > 0


def test_graph_delete_concepts(test_ids):
    """Test deleting concepts."""
    # Create concept
    upsert_knowledge_graph(
        mas_id=test_ids["mas_id"],
        wksp_id=test_ids["wksp_id"],
        concepts=[{"id": "to-delete", "name": "Delete Me"}],
    )

    # Delete it
    response = delete_knowledge_graph(
        mas_id=test_ids["mas_id"],
        wksp_id=test_ids["wksp_id"],
        concepts=[{"id": "to-delete"}],
    )
    assert response.status == "success"


def test_graph_validation_error():
    """Test that missing required fields raises ValidationError."""
    with pytest.raises(ValidationError):
        upsert_knowledge_graph(
            # Missing both mas_id and wksp_id
            concepts=[{"id": "test", "name": "Test"}]
        )


def test_graph_not_found_error():
    """Test that querying non-existent data raises NotFoundError."""
    with pytest.raises(NotFoundError):
        query_knowledge_graph(
            mas_id="nonexistent-mas",
            wksp_id="nonexistent-wksp",
            concepts=[{"id": "nonexistent"}],
            query_type="concept",
        )


# ============================================================================
# Knowledge Vector Tests
# ============================================================================


def test_vector_onboard_store(vector_store_id):
    """Test onboarding a new vector store."""
    response = onboard_vector_store(store_id=vector_store_id)
    assert response.status == "success"


def test_vector_upsert(vector_store_id, test_ids):
    """Test upserting vectors."""
    # Onboard first
    onboard_vector_store(store_id=vector_store_id)

    # Create simple embedding (384 dimensions)
    embedding = [0.1] * 384

    # Upsert vector with UUID
    vec_id = str(uuid4())
    response = upsert_vector_store(
        wksp_id=vector_store_id,
        mas_id=test_ids["mas_id"],
        records=[
            {
                "id": vec_id,
                "content": "Test content for vector",
                "embedding": {"data": embedding},
            }
        ],
    )
    assert response.status == "success"


def test_vector_query_by_id(vector_store_id, test_ids):
    """Test querying vector by ID."""
    # Onboard and insert
    onboard_vector_store(store_id=vector_store_id)
    embedding = [0.2] * 384
    vec_id = str(uuid4())

    upsert_vector_store(
        wksp_id=vector_store_id,
        mas_id=test_ids["mas_id"],
        records=[
            {
                "id": vec_id,
                "content": "Query test content",
                "embedding": {"data": embedding},
            }
        ],
    )

    # Query by ID
    response = query_vector_store(
        wksp_id=vector_store_id,
        mas_id=test_ids["mas_id"],
        query_type="get_by_id",
        vector_id=vec_id,
    )
    assert response.status == "success"
    assert len(response.records) == 1
    assert response.records[0].content == "Query test content"


def test_vector_similarity_search(vector_store_id, test_ids):
    """Test similarity search with cosine distance."""
    # Onboard and insert multiple vectors
    onboard_vector_store(store_id=vector_store_id)

    records = [
        {"id": str(uuid4()), "content": f"Document {i}", "embedding": {"data": [float(i) * 0.1] * 384}}
        for i in range(1, 4)
    ]

    upsert_vector_store(
        wksp_id=vector_store_id,
        mas_id=test_ids["mas_id"],
        records=records,
    )

    # Search with query embedding
    query_embedding = [0.15] * 384

    response = query_vector_store(
        wksp_id=vector_store_id,
        mas_id=test_ids["mas_id"],
        query_type="distance_cosine",
        embedding=query_embedding,
        limit=3,
    )
    assert response.status == "success"
    assert len(response.records) > 0
    # Should have distance scores
    assert all(hasattr(r, "distance") for r in response.records)


def test_vector_list_all(vector_store_id, test_ids):
    """Test listing all vectors in workspace."""
    # Onboard and insert
    onboard_vector_store(store_id=vector_store_id)
    embedding = [0.3] * 384

    upsert_vector_store(
        wksp_id=vector_store_id,
        mas_id=test_ids["mas_id"],
        records=[
            {
                "id": str(uuid4()),
                "content": "List test",
                "embedding": {"data": embedding},
            }
        ],
    )

    # List all
    response = query_vector_store(
        wksp_id=vector_store_id,
        mas_id=test_ids["mas_id"],
        query_type="list_by_wksp_id",
        limit=10,
    )
    assert response.status == "success"
    assert len(response.records) >= 1


def test_vector_delete(vector_store_id, test_ids):
    """Test deleting a vector."""
    # Onboard and insert
    onboard_vector_store(store_id=vector_store_id)
    embedding = [0.4] * 384
    vec_id = str(uuid4())

    upsert_vector_store(
        wksp_id=vector_store_id,
        mas_id=test_ids["mas_id"],
        records=[
            {
                "id": vec_id,
                "content": "To be deleted",
                "embedding": {"data": embedding},
            }
        ],
    )

    # Delete (soft delete)
    response = delete_vector(
        wksp_id=vector_store_id,
        mas_id=test_ids["mas_id"],
        vector_id=vec_id,
        soft_delete=True,
    )
    assert response.status == "success"


def test_vector_not_onboarded_error(test_ids):
    """Test that upserting to non-onboarded store raises NotFoundError."""
    with pytest.raises(NotFoundError):
        upsert_vector_store(
            wksp_id="never-onboarded",
            mas_id=test_ids["mas_id"],
            records=[
                {
                    "id": "test",
                    "content": "Test",
                    "embedding": {"data": [0.1] * 384},
                }
            ],
        )


def test_vector_invalid_embedding_size():
    """Test that invalid embedding size raises ValidationError."""
    with pytest.raises(ValidationError):
        # Try to create with wrong size (should be 384)
        upsert_vector_store(
            wksp_id="any-store",
            mas_id="any-mas",
            records=[
                {
                    "id": "test",
                    "content": "Test",
                    "embedding": {"data": [0.1, 0.2, 0.3]},  # Only 3 dimensions
                }
            ],
        )


# ============================================================================
# Import Tests
# ============================================================================


def test_imports_work():
    """Test that all library imports are accessible."""
    from knowledge_memory import (
        upsert_knowledge_graph,
        query_knowledge_graph,
        delete_knowledge_graph,
        onboard_vector_store,
        upsert_vector_store,
        query_vector_store,
        delete_vector,
        ValidationError,
        NotFoundError,
        OperationFailedError,
    )

    # All should be callable
    assert callable(upsert_knowledge_graph)
    assert callable(query_knowledge_graph)
    assert callable(onboard_vector_store)
    assert callable(upsert_vector_store)

    # Exceptions should be Exception subclasses
    assert issubclass(ValidationError, Exception)
    assert issubclass(NotFoundError, Exception)
    assert issubclass(OperationFailedError, Exception)
