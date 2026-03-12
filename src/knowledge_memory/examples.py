"""
Knowledge Memory - Example Usage

Examples demonstrating direct, in-process access to knowledge memory operations.

Run: python examples.py
Requires: Database running (task docker-compose-up)
"""

import sys
import os
import random

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

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


def example_knowledge_graph():
    """Example: Knowledge Graph operations."""
    print("\n" + "=" * 60)
    print("KNOWLEDGE GRAPH EXAMPLES")
    print("=" * 60)

    # Example 1: Create knowledge graph with concepts and relations
    print("\n1. Creating knowledge graph...")
    try:
        response = upsert_knowledge_graph(
            mas_id="example-agent",
            wksp_id="example-workspace",
            memory_type="Semantic",
            concepts=[
                {
                    "id": "python",
                    "name": "Python",
                    "description": "A high-level programming language",
                    "tags": ["programming", "language"],
                    "attributes": {"category": "technology", "year": 1991}
                },
                {
                    "id": "fastapi",
                    "name": "FastAPI",
                    "description": "Modern web framework for Python",
                    "tags": ["framework", "web"],
                    "attributes": {"category": "technology"}
                },
                {
                    "id": "uvicorn",
                    "name": "Uvicorn",
                    "description": "ASGI web server",
                    "tags": ["server", "asgi"]
                }
            ],
            relations=[
                {
                    "id": "rel1",
                    "relation": "BUILT_WITH",
                    "node_ids": ["fastapi", "python"],
                    "attributes": {"strength": "high"}
                },
                {
                    "id": "rel2",
                    "relation": "RUNS_ON",
                    "node_ids": ["fastapi", "uvicorn"]
                }
            ]
        )
        print(f"✓ Status: {response.status}")
        print(f"✓ Message: {response.message}")
    except (ValidationError, OperationFailedError) as e:
        print(f"✗ Error: {e}")

    # Example 2: Query neighbors
    print("\n2. Querying neighbors of 'fastapi'...")
    try:
        response = query_knowledge_graph(
            mas_id="example-agent",
            wksp_id="example-workspace",
            concepts=[{"id": "fastapi"}],
            query_type="neighbour"
        )
        print(f"✓ Status: {response.status}")
        if response.records:
            for record in response.records:
                print(f"  - Found {len(record.concepts)} concepts")
                for concept in record.concepts:
                    print(f"    • {concept.name} ({concept.id})")
                print(f"  - Found {len(record.relationships)} relationships")
                for rel in record.relationships:
                    print(f"    • {rel.relation}: {rel.node_ids}")
    except NotFoundError as e:
        print(f"✗ Not found: {e}")
    except OperationFailedError as e:
        print(f"✗ Error: {e}")

    # Example 3: Query path between two concepts
    print("\n3. Finding path from 'python' to 'uvicorn'...")
    try:
        response = query_knowledge_graph(
            mas_id="example-agent",
            wksp_id="example-workspace",
            concepts=[{"id": "python"}, {"id": "uvicorn"}],
            query_type="path",
            depth=5
        )
        print(f"✓ Status: {response.status}")
        print(f"✓ Message: {response.message}")
        if response.records:
            print(f"  - Path found with {len(response.records)} segments")
    except NotFoundError as e:
        print(f"✗ Not found: {e}")

    # Example 4: Query specific concept
    print("\n4. Getting concept details for 'python'...")
    try:
        response = query_knowledge_graph(
            mas_id="example-agent",
            wksp_id="example-workspace",
            concepts=[{"id": "python"}],
            query_type="concept"
        )
        print(f"✓ Status: {response.status}")
        if response.records and response.records[0].concepts:
            concept = response.records[0].concepts[0]
            print(f"  - Name: {concept.name}")
            print(f"  - Description: {concept.description}")
            print(f"  - Tags: {concept.tags}")
    except NotFoundError as e:
        print(f"✗ Not found: {e}")

    # Example 5: Delete specific concepts
    print("\n5. Deleting concept 'uvicorn'...")
    try:
        response = delete_knowledge_graph(
            mas_id="example-agent",
            wksp_id="example-workspace",
            concepts=[{"id": "uvicorn"}]
        )
        print(f"✓ Status: {response.status}")
        print(f"✓ Message: {response.message}")
    except OperationFailedError as e:
        print(f"✗ Error: {e}")


def example_knowledge_vector():
    """Example: Knowledge Vector operations."""
    print("\n" + "=" * 60)
    print("KNOWLEDGE VECTOR EXAMPLES")
    print("=" * 60)

    # Example 1: Onboard a vector store
    print("\n1. Onboarding vector store...")
    try:
        response = onboard_vector_store(store_id="example-store")
        print(f"✓ Status: {response.status}")
        print(f"✓ Message: {response.message}")
    except OperationFailedError as e:
        print(f"✓ Store might already exist: {e}")

    # Example 2: Upsert vectors
    print("\n2. Upserting vectors...")
    try:
        # Note: Using random embeddings for demonstration
        # In production, use real embeddings from a model
        def generate_embedding(seed):
            """Generate a deterministic 384-dimensional embedding."""
            random.seed(seed)
            return [random.random() for _ in range(384)]

        response = upsert_vector_store(
            wksp_id="example-store",
            mas_id="example-agent",
            records=[
                {
                    "id": "doc1",
                    "content": (
                        "Python is a versatile programming language used for "
                        "web development, data science, and automation."
                    ),
                    "embedding": {"data": generate_embedding(1)}
                },
                {
                    "id": "doc2",
                    "content": (
                        "FastAPI is a modern, fast web framework for building APIs "
                        "with Python based on standard type hints."
                    ),
                    "embedding": {"data": generate_embedding(2)}
                },
                {
                    "id": "doc3",
                    "content": (
                        "Machine learning models require large amounts of data and "
                        "computational resources for training."
                    ),
                    "embedding": {"data": generate_embedding(3)}
                }
            ]
        )
        print(f"✓ Status: {response.status}")
        print(f"✓ Message: {response.message}")
    except (NotFoundError, ValidationError, OperationFailedError) as e:
        print(f"✗ Error: {e}")

    # Example 3: Query by ID
    print("\n3. Getting vector by ID...")
    try:
        response = query_vector_store(
            wksp_id="example-store",
            mas_id="example-agent",
            query_type="get_by_id",
            vector_id="doc1"
        )
        print(f"✓ Status: {response.status}")
        if response.records:
            record = response.records[0]
            print(f"  - ID: {record.id}")
            print(f"  - Content: {record.content[:60]}...")
    except NotFoundError as e:
        print(f"✗ Not found: {e}")

    # Example 4: List all vectors
    print("\n4. Listing all vectors in workspace...")
    try:
        response = query_vector_store(
            wksp_id="example-store",
            mas_id="example-agent",
            query_type="list_by_wksp_id",
            limit=10
        )
        print(f"✓ Status: {response.status}")
        print(f"✓ Found {len(response.records)} vectors")
        for record in response.records:
            print(f"  - {record.id}: {record.content[:50]}...")
    except OperationFailedError as e:
        print(f"✗ Error: {e}")

    # Example 5: Similarity search using cosine distance
    print("\n5. Similarity search (cosine distance)...")
    try:
        random.seed(1.5)  # Similar to doc1
        query_embedding = [random.random() for _ in range(384)]

        response = query_vector_store(
            wksp_id="example-store",
            mas_id="example-agent",
            query_type="distance_cosine",
            embedding=query_embedding,
            limit=3
        )
        print(f"✓ Status: {response.status}")
        print(f"✓ Found {len(response.records)} similar vectors:")
        for record in response.records:
            print(f"  - {record.id} (distance: {record.distance:.4f})")
            print(f"    {record.content[:60]}...")
    except OperationFailedError as e:
        print(f"✗ Error: {e}")

    # Example 6: Delete a vector (soft delete)
    print("\n6. Soft deleting vector 'doc3'...")
    try:
        response = delete_vector(
            wksp_id="example-store",
            mas_id="example-agent",
            vector_id="doc3",
            soft_delete=True
        )
        print(f"✓ Status: {response.status}")
        print(f"✓ Message: {response.message}")
    except (NotFoundError, OperationFailedError) as e:
        print(f"✗ Error: {e}")


def example_error_handling():
    """Example: Error handling."""
    print("\n" + "=" * 60)
    print("ERROR HANDLING EXAMPLES")
    print("=" * 60)

    # Example 1: Validation error
    print("\n1. Triggering validation error (missing required field)...")
    try:
        upsert_knowledge_graph(
            # Missing both mas_id and wksp_id - should fail validation
            concepts=[{"id": "test", "name": "Test"}]
        )
    except ValidationError as e:
        print(f"✓ Caught ValidationError: {e}")

    # Example 2: Not found error
    print("\n2. Triggering not found error...")
    try:
        query_knowledge_graph(
            mas_id="nonexistent-agent",
            wksp_id="nonexistent-workspace",
            concepts=[{"id": "nonexistent"}],
            query_type="concept"
        )
    except NotFoundError as e:
        print(f"✓ Caught NotFoundError: {e}")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("KNOWLEDGE MEMORY - EXAMPLE USAGE")
    print("=" * 60)
    print("\nNOTE: Requires database running")
    print("Start with: task docker-compose-up")

    try:
        # Run examples
        example_knowledge_graph()
        example_knowledge_vector()
        example_error_handling()

        print("\n" + "=" * 60)
        print("✓ All examples completed!")
        print("=" * 60 + "\n")

    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
