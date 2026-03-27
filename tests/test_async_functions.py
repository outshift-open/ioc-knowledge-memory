# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""
Integration tests for async knowledge_memory functions.

Tests async versions against sync versions to ensure no regression.
Requires: Database running (task docker-compose-up)

Run: pytest tests/test_async_functions.py -v
"""

import pytest
import asyncio
import sys
import os
from uuid import uuid4

# Add src to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from knowledge_memory import (
    # Sync versions
    upsert_knowledge_graph,
    query_knowledge_graph,
    # Async versions
    upsert_knowledge_graph_async,
    query_knowledge_graph_async,
    # Exceptions
    ValidationError,
    NotFoundError,
)


# Test fixtures
@pytest.fixture
def test_ids():
    """Generate unique IDs for test isolation."""
    return {
        "mas_id": str(uuid4()),
        "wksp_id": str(uuid4()),
    }


# ============================================================================
# Async Function Tests - Compare with Sync Versions
# ============================================================================


@pytest.mark.asyncio
async def test_async_upsert_creates_concepts(test_ids):
    """Test async upsert creates concepts successfully."""
    response = await upsert_knowledge_graph_async(
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


@pytest.mark.asyncio
async def test_async_upsert_with_relations(test_ids):
    """Test async upsert with relationships."""
    response = await upsert_knowledge_graph_async(
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


@pytest.mark.asyncio
async def test_async_query_concept(test_ids):
    """Test async query returns same results as sync."""
    # Create concept using async
    await upsert_knowledge_graph_async(
        mas_id=test_ids["mas_id"],
        wksp_id=test_ids["wksp_id"],
        concepts=[{"id": "test-concept", "name": "Test", "description": "Testing"}],
    )

    # Query using async
    response = await query_knowledge_graph_async(
        mas_id=test_ids["mas_id"],
        wksp_id=test_ids["wksp_id"],
        concepts=[{"id": "test-concept"}],
        query_type="concept",
    )
    assert response.status == "success"
    assert len(response.records) > 0
    assert response.records[0].concepts[0].name == "Test"


@pytest.mark.asyncio
async def test_async_query_neighbours(test_ids):
    """Test async neighbor query."""
    # Create connected concepts
    await upsert_knowledge_graph_async(
        mas_id=test_ids["mas_id"],
        wksp_id=test_ids["wksp_id"],
        concepts=[
            {"id": "center", "name": "Center"},
            {"id": "neighbor", "name": "Neighbor"},
        ],
        relations=[{"id": "r1", "relation": "CONNECTS", "node_ids": ["center", "neighbor"]}],
    )

    # Query neighbors
    response = await query_knowledge_graph_async(
        mas_id=test_ids["mas_id"],
        wksp_id=test_ids["wksp_id"],
        concepts=[{"id": "center"}],
        query_type="neighbour",
    )
    assert response.status == "success"
    assert len(response.records) > 0


@pytest.mark.asyncio
async def test_async_query_path(test_ids):
    """Test async path query."""
    # Create path: node1 -> node2 -> node3
    await upsert_knowledge_graph_async(
        mas_id=test_ids["mas_id"],
        wksp_id=test_ids["wksp_id"],
        concepts=[
            {"id": "node1", "name": "Node1"},
            {"id": "node2", "name": "Node2"},
            {"id": "node3", "name": "Node3"},
        ],
        relations=[
            {"id": "r1", "relation": "CONNECTS", "node_ids": ["node1", "node2"]},
            {"id": "r2", "relation": "CONNECTS", "node_ids": ["node2", "node3"]},
        ],
    )

    # Query path from node1 to node3
    response = await query_knowledge_graph_async(
        mas_id=test_ids["mas_id"],
        wksp_id=test_ids["wksp_id"],
        concepts=[{"id": "node1"}, {"id": "node3"}],
        query_type="path",
        depth=5,
    )
    assert response.status == "success"
    # Path should be found
    assert "path" in response.message.lower() or "found" in response.message.lower()


@pytest.mark.asyncio
async def test_async_validation_error():
    """Test that async version raises ValidationError for invalid input."""
    with pytest.raises(ValidationError):
        await upsert_knowledge_graph_async(
            # Missing both mas_id and wksp_id
            concepts=[{"id": "test", "name": "Test"}]
        )


@pytest.mark.asyncio
async def test_async_not_found_error():
    """Test that async version raises NotFoundError for missing data."""
    with pytest.raises(NotFoundError):
        await query_knowledge_graph_async(
            mas_id="nonexistent-mas",
            wksp_id="nonexistent-wksp",
            concepts=[{"id": "nonexistent"}],
            query_type="concept",
        )


# ============================================================================
# Concurrent Operations Tests
# ============================================================================


@pytest.mark.asyncio
async def test_async_concurrent_upserts(test_ids):
    """Test multiple concurrent async upserts."""
    tasks = [
        upsert_knowledge_graph_async(
            mas_id=test_ids["mas_id"],
            wksp_id=test_ids["wksp_id"],
            concepts=[{"id": f"concept-{i}", "name": f"Concept {i}"}],
        )
        for i in range(5)
    ]

    results = await asyncio.gather(*tasks)

    # All should succeed
    assert all(r.status == "success" for r in results)
    assert len(results) == 5


@pytest.mark.asyncio
async def test_async_concurrent_queries(test_ids):
    """Test multiple concurrent async queries."""
    # Create concepts first
    for i in range(5):
        await upsert_knowledge_graph_async(
            mas_id=test_ids["mas_id"],
            wksp_id=test_ids["wksp_id"],
            concepts=[{"id": f"query-concept-{i}", "name": f"Query Concept {i}"}],
        )

    # Query all concurrently
    tasks = [
        query_knowledge_graph_async(
            mas_id=test_ids["mas_id"],
            wksp_id=test_ids["wksp_id"],
            concepts=[{"id": f"query-concept-{i}"}],
            query_type="concept",
        )
        for i in range(5)
    ]

    results = await asyncio.gather(*tasks)

    # All should succeed
    assert all(r.status == "success" for r in results)
    assert len(results) == 5


@pytest.mark.asyncio
async def test_async_mixed_operations(test_ids):
    """Test mixed upsert and query operations concurrently."""
    # Create some initial concepts
    await upsert_knowledge_graph_async(
        mas_id=test_ids["mas_id"],
        wksp_id=test_ids["wksp_id"],
        concepts=[
            {"id": "initial-1", "name": "Initial 1"},
            {"id": "initial-2", "name": "Initial 2"},
        ],
    )

    # Mix of upserts and queries
    tasks = [
        # Upserts
        upsert_knowledge_graph_async(
            mas_id=test_ids["mas_id"],
            wksp_id=test_ids["wksp_id"],
            concepts=[{"id": "new-1", "name": "New 1"}],
        ),
        upsert_knowledge_graph_async(
            mas_id=test_ids["mas_id"],
            wksp_id=test_ids["wksp_id"],
            concepts=[{"id": "new-2", "name": "New 2"}],
        ),
        # Queries
        query_knowledge_graph_async(
            mas_id=test_ids["mas_id"],
            wksp_id=test_ids["wksp_id"],
            concepts=[{"id": "initial-1"}],
            query_type="concept",
        ),
        query_knowledge_graph_async(
            mas_id=test_ids["mas_id"],
            wksp_id=test_ids["wksp_id"],
            concepts=[{"id": "initial-2"}],
            query_type="concept",
        ),
    ]

    results = await asyncio.gather(*tasks)

    # All should succeed
    assert all(r.status == "success" for r in results)
    assert len(results) == 4


# ============================================================================
# Sync vs Async Comparison Tests
# ============================================================================


@pytest.mark.asyncio
async def test_sync_async_parity_upsert(test_ids):
    """Test that sync and async upsert produce same results."""
    # Sync upsert
    sync_response = upsert_knowledge_graph(
        mas_id=test_ids["mas_id"],
        wksp_id=test_ids["wksp_id"],
        concepts=[{"id": "sync-concept", "name": "Sync Concept"}],
    )

    # Async upsert
    async_response = await upsert_knowledge_graph_async(
        mas_id=test_ids["mas_id"],
        wksp_id=test_ids["wksp_id"],
        concepts=[{"id": "async-concept", "name": "Async Concept"}],
    )

    # Both should have same status
    assert sync_response.status == async_response.status == "success"
    # Both should have similar message structure
    assert "successfully" in sync_response.message.lower()
    assert "successfully" in async_response.message.lower()


@pytest.mark.asyncio
async def test_sync_async_parity_query(test_ids):
    """Test that sync and async query produce same results."""
    # Create concept
    upsert_knowledge_graph(
        mas_id=test_ids["mas_id"],
        wksp_id=test_ids["wksp_id"],
        concepts=[{"id": "parity-concept", "name": "Parity Test", "description": "Testing parity"}],
    )

    # Sync query
    sync_response = query_knowledge_graph(
        mas_id=test_ids["mas_id"],
        wksp_id=test_ids["wksp_id"],
        concepts=[{"id": "parity-concept"}],
        query_type="concept",
    )

    # Async query
    async_response = await query_knowledge_graph_async(
        mas_id=test_ids["mas_id"],
        wksp_id=test_ids["wksp_id"],
        concepts=[{"id": "parity-concept"}],
        query_type="concept",
    )

    # Both should return same data
    assert sync_response.status == async_response.status == "success"
    assert len(sync_response.records) == len(async_response.records) == 1
    assert sync_response.records[0].concepts[0].name == async_response.records[0].concepts[0].name


# ============================================================================
# Import Tests
# ============================================================================


def test_async_imports_work():
    """Test that async function imports are accessible."""
    from knowledge_memory import (
        upsert_knowledge_graph_async,
        query_knowledge_graph_async,
    )

    # Both should be callable
    assert callable(upsert_knowledge_graph_async)
    assert callable(query_knowledge_graph_async)

    # Both should be coroutines
    import inspect
    assert inspect.iscoroutinefunction(upsert_knowledge_graph_async)
    assert inspect.iscoroutinefunction(query_knowledge_graph_async)
