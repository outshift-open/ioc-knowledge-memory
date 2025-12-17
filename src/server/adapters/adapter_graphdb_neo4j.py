import logging
from typing import Tuple, List, Dict, Any, Optional

from server.database.graph_db.neo4j.models.node import Node
from server.database.graph_db.neo4j.models.edge import Edge

MAS_LABEL_PREFIX = "MAS_"
WKSP_LABEL_PREFIX = "WKSP_"
MEM_TYPE_LABEL_PREFIX = "MEM_TYPE_"


class Adapter_GraphDB_Neo4j:
    """Adapter for converting TKF models to GraphDB models for Neo4j"""

    def __init__(self):
        # Get logger instance (logging is setup in main.py)
        self.logger = logging.getLogger(__name__)

    def convert_to_models(self, data: Dict[str, Any]) -> Tuple[List[Node], List[Edge]]:
        """Convert TkfStoreRequest JSON to Node and Edge objects.

        Args:
            data: The parsed JSON data from TkfStoreRequest

        Returns:
            tuple: (list of Node objects, list of Edge objects)

        Raises:
            ValueError: If input data is invalid or conversion fails
        """
        nodes = []
        relationships = []

        try:
            self._validate_input_data(data)

            # Extract common metadata
            mas_id = data.get("mas_id", "")
            wksp_id = data.get("wksp_id", "")
            memory_type = data.get("memory_type", "")

            # Process nodes
            if "concepts" in data["records"] and data["records"]["concepts"]:
                self.logger.info(f"Processing {len(data['records']['concepts'])} concepts")
                nodes = self._process_concepts(data["records"]["concepts"], mas_id, wksp_id, memory_type)

            # Process relationships
            if "relations" in data["records"] and data["records"]["relations"]:
                self.logger.info(f"Processing {len(data['records']['relations'])} relations")
                relationships = self._process_relations(data["records"]["relations"], mas_id, wksp_id, memory_type)

            self.logger.info(f"Successfully converted to {len(nodes)} nodes and {len(relationships)} edges")
            self.logger.info(f"Nodes: {nodes}")
            self.logger.info(f"Relationships: {relationships}")
            return nodes, relationships

        except Exception as e:
            self.logger.error(f"Error converting data to models: {str(e)}", exc_info=True)
            raise  # Re-raise to allow caller to handle the error

    def _validate_input_data(self, data: Dict[str, Any]) -> None:
        """Validate the input data structure."""
        if not isinstance(data, dict):
            raise ValueError("Input data must be a dictionary")

        if "records" not in data:
            self.logger.error("Input data must contain 'records' key")
            raise ValueError("Input data must contain 'records' key")

        if not isinstance(data["records"], dict):
            raise ValueError("'records' must be a dictionary")

    def _generate_labels(self, concept: Dict, mas_id: str, wksp_id: str, memory_type: str) -> List[str]:
        """Generate labels for a node."""
        labels = ["Concept"]  # Default label

        # Add metadata labels
        if mas_id:
            labels.append(f"{MAS_LABEL_PREFIX}{mas_id}")
        if wksp_id:
            labels.append(f"{WKSP_LABEL_PREFIX}{wksp_id}")
        if memory_type:
            labels.append(f"{MEM_TYPE_LABEL_PREFIX}{memory_type}")

        # Add tags as labels
        for tag in concept.get("tags", []):
            if tag and str(tag).strip():
                labels.append(str(tag).strip())

        return labels

    def _process_embeddings(self, embedding_data: Dict, properties: Dict) -> None:
        """Process embedding data into properties."""
        try:
            if "data" in embedding_data:
                properties["embedding_vector"] = embedding_data["data"]
            if "name" in embedding_data:
                properties["embedding_model"] = embedding_data["name"]
        except Exception as e:
            self.logger.error(f"Failed to process embeddings: {str(e)}")

    def _process_concepts(self, concepts: List[Dict], mas_id: str, wksp_id: str, memory_type: str) -> List[Node]:
        """Process concept data into Node objects."""
        nodes = []
        for concept in concepts:
            try:
                properties = {
                    "name": concept.get("name", ""),
                    "description": concept.get("description", ""),
                    **concept.get("attributes", {}),
                }

                # Handle embeddings
                if "embeddings" in concept and concept["embeddings"]:
                    self._process_embeddings(concept["embeddings"], properties)

                # Create node with appropriate labels
                labels = self._generate_labels(concept, mas_id, wksp_id, memory_type)

                node = Node(
                    id=concept["id"],
                    labels=labels,
                    properties=properties,
                )
                nodes.append(node)

            except KeyError as ke:
                self.logger.error(f"Missing required field in concept: {ke}")
                raise
            except Exception as e:
                self.logger.error(f"Error processing concept {concept.get('id', 'unknown')}: {str(e)}")
                raise

        return nodes

    def _process_relations(self, relations: List[Dict], mas_id: str, wksp_id: str, memory_type: str) -> List[Edge]:
        """Process relation data into Edge objects."""
        edges = []
        for rel_data in relations:
            try:
                # Initialize properties with node_ids and any existing attributes
                properties = {"node_ids": rel_data.get("node_ids", []), **rel_data.get("attributes", {})}

                # Handle embeddings
                if "embeddings" in rel_data and rel_data["embeddings"]:
                    self._process_embeddings(rel_data["embeddings"], properties)

                # Add metadata
                # todo do we need these on the edges for the queries
                # or just having them on the nodes is ok
                if mas_id:
                    properties["mas_id"] = mas_id
                if wksp_id:
                    properties["wksp_id"] = wksp_id
                if memory_type:
                    properties["memory_type"] = memory_type

                edge = Edge(
                    id=rel_data["id"],
                    node_ids=rel_data["node_ids"],
                    relation=rel_data["relation"],
                    properties=properties,
                )
                edges.append(edge)

            except KeyError as ke:
                self.logger.error(f"Missing required field in relation: {ke}")
                raise
            except Exception as e:
                self.logger.error(f"Error processing relation {rel_data.get('id', 'unknown')}: {str(e)}")
                raise

        return edges
