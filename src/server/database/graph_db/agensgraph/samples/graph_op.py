#!/usr/bin/env python3
"""
Graph Operations Example
 ioc-knowledge-memory-svc % python -m server.database.graph_db.agensgraph.samples.graph_op

This script demonstrates basic graph operations using the GraphDB class:
- Creating a graph
- Getting graph information
- Deleting a graph
"""
import logging
import sys
from pathlib import Path

from app_logging import setup_logging

# Add the project root to the Python path
project_root = Path(__file__).resolve().parents[3]
sys.path.append(str(project_root))

from src.server.database.graph_db.agensgraph.src.db import GraphDB
from src.server.database.graph_db.agensgraph.models.node import Node
from src.server.database.graph_db.agensgraph.models.edge import Edge

# Configure logging
# logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
# logger = logging.getLogger(__name__)

# Setup logging using the application's logging configuration
setup_logging("test_graph_op")
logger = logging.getLogger(__name__)


def setup_database():
    """Initialize and return a GraphDB instance with environment variables."""
    db = GraphDB()
    db.init()
    return db


def create_graph(db, graph_name):
    """Create a new graph.

    Args:
        db: GraphDB instance
        graph_name: Name of the graph to create
    """
    try:
        logger.info(f"Creating graph: {graph_name}")
        result = db.create_graph(graph_name)
        if result:
            logger.info(f"Successfully created graph: {graph_name}")
        return result
    except Exception as e:
        logger.error(f"Error creating graph {graph_name}: {str(e)}")
        raise


def get_graph_info(db, graph_name):
    """Get information about a graph.

    Args:
        db: GraphDB instance
        graph_name: Name of the graph to query
    """
    try:
        logger.info(f"Getting information for graph: {graph_name}")
        graph_info = db.get_graph(graph_name)
        if graph_info:
            logger.info(f"Graph info: {graph_info}")
        else:
            logger.info(f"Graph '{graph_name}' not found")
        return graph_info
    except Exception as e:
        logger.error(f"Error getting graph info for {graph_name}: {str(e)}")
        raise


def delete_graph(db, graph_name, soft_delete):
    """Delete a graph.

    Args:
        db: GraphDB instance
        graph_name: Name of the graph to delete
    """
    try:
        logger.info(f"Deleting graph: {graph_name}")
        result = db.delete_graph(graph_name, soft_delete)
        if result:
            logger.info(f"Successfully deleted graph: {graph_name}")
        return result
    except Exception as e:
        logger.error(f"Error deleting graph {graph_name}: {str(e)}")
        raise


def query_neighbors(db, graph_name, node_id):
    """Query neighbors of a specific node.

    Args:
        db: GraphDB instance
        graph_name: Name of the graph to query
        node_id: ID of the node to find neighbors for
    """
    try:
        logger.info(f"Querying neighbors for node {node_id} in graph: {graph_name}")

        # Create a node object for the query
        query_node = Node(id=node_id, labels=["Person"])

        # Execute the neighbor query
        success, results, message = db.query_type_neighbor(graph=graph_name, nodes=[query_node])

        if success:
            logger.info(f"Query successful: {message}")
            logger.info(f"Found {len(results)} result entries")
            logger.info(results)

            # Log the results
            for i, result_entry in enumerate(results):
                logger.info(f"Result entry {i + 1}:")
                if result_entry.get("nodes"):
                    logger.info(f"  - Found {len(result_entry['nodes'])} neighbor nodes:")
                    for node in result_entry["nodes"]:
                        logger.info(f"    - Node: {node}")

                if result_entry.get("edges"):
                    logger.info(f"  - Found {len(result_entry['edges'])} relationships:")
                    for edge in result_entry["edges"]:
                        logger.info(f"    - Edge: {edge}")
        else:
            logger.warning(f"Query failed: {message}")

        return success, results, message

    except Exception as e:
        logger.error(f"Error querying neighbors for node {node_id}: {str(e)}")
        raise


def query_paths(db, graph_name, source_node_id, dest_node_id, depth: int = None):
    """Query paths between two specific nodes.

    Args:
        db: GraphDB instance
        graph_name: Name of the graph to query
        source_node_id: ID of the source node
        dest_node_id: ID of the destination node
        depth: Maximum path depth/length
    """
    try:
        logger.info(f"Querying paths from {source_node_id} to {dest_node_id} in graph: {graph_name}")

        # Create node objects for the query
        source_node = Node(id=source_node_id, labels=["Person"])
        dest_node = Node(id=dest_node_id, labels=["Person"])

        # Execute the path query
        success, results, message = db.query_type_path(graph=graph_name, nodes=[source_node, dest_node], depth=depth)

        if success:
            logger.info(f"Query successful: {message}")
            logger.info(f"Found {len(results)} path result entries")

            # Debug: Print raw results structure
            logger.info(f"Raw results: {results}")
        else:
            logger.warning(f"Query failed: {message}")

        return success, results, message

    except Exception as e:
        logger.error(f"Error querying paths from {source_node_id} to {dest_node_id}: {str(e)}")
        raise


def main():
    """Main function to demonstrate graph operations."""
    graph_name = "test_graph"

    try:
        # Initialize database connection
        db = setup_database()

        # Create a graph
        create_graph(db, graph_name)

        # Get graph information
        get_graph_info(db, graph_name)

        # Delete the graph (uncomment to enable deletion)
        delete_graph(db, graph_name, soft_delete=False)
        # delete_graph(db, graph_name, soft_delete=True)

        # Create some nodes and edges to form a small network
        node1 = Node(id="1", labels=["Person"], properties={"name": "Alice"})
        node2 = Node(id="2", labels=["Person"], properties={"name": "Bob"})
        node3 = Node(id="3", labels=["Person"], properties={"name": "Charlie"})

        edge1 = Edge(id="1", node_ids=["1", "2"], relation="KNOWS", properties={"since": "2023"})
        edge2 = Edge(id="2", node_ids=["2", "3"], relation="KNOWS", properties={"since": "2024"})

        # Save them to a specific graph
        success, message = db.save(
            graph=graph_name,  # This graph will be created if it doesn't exist
            nodes=[node1, node2, node3],
            edges=[edge1, edge2],
            force_replace=True,
        )
        print(message)

        # Query neighbors of node1 (Alice)
        if success:
            logger.info("Querying neighbors of Alice (node 1)...")
            query_neighbors(db, graph_name, "1")

            # Query paths between Alice and Charlie (should go through Bob)
            logger.info("Querying paths from Alice (node 1) to Charlie (node 3)...")
            query_paths(db, graph_name, "1", "1")

    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        return 1
    finally:
        # Clean up resources
        if "db" in locals():
            db.close()

    return 0


if __name__ == "__main__":
    sys.exit(main())
