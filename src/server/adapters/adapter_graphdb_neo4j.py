import logging
from typing import Tuple, List, Dict, Any

from server.schemas.tkf import EmbeddingConfig

from server.database.graph_db.neo4j.models.node import Node
from server.database.graph_db.neo4j.models.edge import Edge
from server.schemas.tkf import TkfQueryResponseRecord, Concept, Relation

MAS_LABEL_PREFIX = "MAS_"
WKSP_LABEL_PREFIX = "WKSP_"
MEM_TYPE_LABEL_PREFIX = "MEM_TYPE_"


class Adapter_GraphDB_Neo4j:
    """Adapter for converting TKF models to GraphDB models for Neo4j
    and vice versa."""

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

                # Add metadata to properties too
                if mas_id:
                    properties["mas_id"] = mas_id
                if wksp_id:
                    properties["wksp_id"] = wksp_id
                if memory_type:
                    properties["memory_type"] = memory_type

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
                if mas_id:
                    properties["mas_id"] = mas_id
                if wksp_id:
                    properties["wksp_id"] = wksp_id
                if memory_type:
                    properties["memory_type"] = memory_type
                # persist relation in properties so it can be retrieved
                if rel_data.get("relation"):
                    properties["relation"] = rel_data["relation"]

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

    def convert_query_to_models(self, data: Dict[str, Any]) -> List[Node]:
        """
        Convert a TkfQueryRequest into a list of Node objects for querying.

        Args:
            data: Dictionary containing the query request data following TkfQueryRequest schema

        Returns:
            List of Node objects to be used for querying
        """
        nodes = []

        # Extract concepts from the request
        concepts = data.get("records", {}).get("concepts", [])
        if not isinstance(concepts, list):
            concepts = [concepts]

        # Create Node objects for each concept
        for concept in concepts:
            if not isinstance(concept, dict):
                continue

            # Prepare properties
            properties = {
                "name": concept.get("name", ""),
                "description": concept.get("description", ""),
                **concept.get("attributes", {}),
            }

            # Handle embeddings
            if "embeddings" in concept and concept["embeddings"]:
                self._process_embeddings(concept["embeddings"], properties)

            # Add metadata
            if "mas_id" in data:
                properties["mas_id"] = data["mas_id"]
            if "wksp_id" in data:
                properties["wksp_id"] = data["wksp_id"]
            if "memory_type" in data:
                properties["memory_type"] = data["memory_type"]

            # Create node with appropriate labels
            labels = self._generate_labels(
                concept, data.get("mas_id", ""), data.get("wksp_id", ""), data.get("memory_type", "")
            )

            node = Node(id=concept.get("id", ""), labels=labels, properties=properties)
            nodes.append(node)

        return nodes

    def convert_models_to_query_response_records(
        self, db_results: List[Dict[str, Any]]
    ) -> List[TkfQueryResponseRecord]:
        """
        Convert database query results to a list of TkfQueryResponseRecord objects.

        This method transforms the neo4j results into a structured format that matches
        the TkfQueryResponseRecord schema.

        Args:
            db_results: List of query results from the database. Each result should be a dictionary
                      containing 'node', 'relationships', and 'neighbors' keys.

        Returns:
            List[TkfQueryResponseRecord]: A list of response records containing the converted data

        Example:
            db_results = [
                {
                    'node': {'id': '1', 'name': 'Node1', ...},
                    'relationships': [{'id': 'r1', 'type': 'RELATES_TO', ...}],
                    'neighbors': [{'id': '2', 'name': 'Node2', ...}]
                }
            ]
            records = adapter.convert_models_to_query_response_records(db_results)
        """
        records = []

        for result in db_results:
            if "error" in result:
                # Skip failed queries
                self.logger.warning(f"Skipping failed query result: {result.get('error')}")
                continue

            # Extract node data
            node_data = result.get("node", {})
            relationships_data = result.get("relationships", [])
            neighbors_data = result.get("neighbors", [])

            # Create Concept for the queried node
            queried_concept = None
            if node_data:
                # Initialize embeddings as None, only create EmbeddingConfig if we have embedding data
                embeddings = None
                if "embedding_vector" in node_data or "embedding_model" in node_data:
                    embeddings = EmbeddingConfig(
                        data=node_data.get("embedding_vector", []), name=node_data.get("embedding_model", "")
                    )

                # Create attributes
                attributes = dict(node_data)
                for field in ["id", "name", "description", "embedding_vector", "embedding_model", "embeddings", "tags"]:
                    attributes.pop(field, None)

                queried_concept = Concept(
                    id=node_data.get("id"),
                    name=node_data.get("name", ""),
                    description=node_data.get("description"),
                    attributes=attributes,
                    embeddings=embeddings,
                    tags=node_data.get("tags", []),
                )

            # Create Relation objects
            relations = []
            for rel in relationships_data:
                # Create Relation with required fields and handle potential None values
                self.logger.info(f"Converting model to Relation for response: {rel}")

                # Get relation from edge property 'relation'
                relation = rel.get("relation")
                # Initialize embeddings as None, only create EmbeddingConfig if we have embedding data
                embeddings = None
                if "embedding_vector" in rel or "embedding_model" in rel:
                    embeddings = EmbeddingConfig(
                        data=rel.get("embedding_vector", []), name=rel.get("embedding_model", "")
                    )

                # Create attributes without the embedding fields
                rel_attributes = {
                    k: v
                    for k, v in rel.items()
                    if k not in ["id", "node_ids", "relation", "embedding_vector", "embedding_model", "embeddings"]
                }

                relations.append(
                    Relation(
                        id=rel.get("id", ""),
                        relation=relation,
                        node_ids=rel.get("node_ids", []),
                        attributes=rel_attributes,
                        embeddings=embeddings,
                    )
                )
            self.logger.info(f"Created {len(relations)} relations")

            # Create Concept objects for neighbor nodes
            neighbor_concepts = []
            for neighbor in neighbors_data:
                self.logger.info(f"Converting model to Concept for response: {neighbor}")

                # Initialize neighbor_embeddings as None, only create EmbeddingConfig if we have embedding data
                neighbor_embeddings = None
                if "embedding_vector" in neighbor or "embedding_model" in neighbor:
                    neighbor_embeddings = EmbeddingConfig(
                        data=neighbor.get("embedding_vector", []), name=neighbor.get("embedding_model", "")
                    )

                # Create attributes
                neighbor_attributes = dict(neighbor)
                for field in ["id", "name", "description", "embedding_vector", "embedding_model", "embeddings", "tags"]:
                    neighbor_attributes.pop(field, None)

                neighbor_concepts.append(
                    Concept(
                        id=neighbor.get("id"),
                        name=neighbor.get("name", ""),
                        description=neighbor.get("description"),
                        attributes=neighbor_attributes,
                        embeddings=neighbor_embeddings,
                        tags=neighbor.get("tags", []),
                    )
                )
            self.logger.info(f"Created {len(neighbor_concepts)} neighbor concepts")

            # Create the response record
            records.append(
                TkfQueryResponseRecord(
                    queried_concept=queried_concept, relationships=relations, concepts=neighbor_concepts
                )
            )

        self.logger.info(f"Converted {len(records)} records to TkfQueryResponseRecord objects")
        return records
