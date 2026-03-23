import json
import logging
from typing import Tuple, List, Dict, Any

from knowledge_memory.server.database.graph_db.agensgraph.models.edge import Edge
from knowledge_memory.server.database.graph_db.agensgraph.models.node import Node
from knowledge_memory.server.schemas.knowledge_graph import EmbeddingConfig
from knowledge_memory.server.schemas.knowledge_graph import KnowledgeGraphQueryResponseRecord, Concept, Relation


class AdapterGraphdbAgensgraph:
    """Adapter for converting knowledge graph models to GraphDB models
    and vice versa."""

    def __init__(self):
        # Get logger instance (logging is setup in main.py)
        self.logger = logging.getLogger(__name__)

    def _parse_json_field(self, value, default=None):
        """Parse JSON string back to Python object if needed."""
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return default if default is not None else []
        return value

    def get_graph_name(self, data: Dict[str, Any]) -> str:
        """Get the graph name from the data.

        Priority: mas_id > wksp_id > error if both empty
        """
        try:
            # Extract common metadata
            mas_id = data.get("mas_id", "")
            wksp_id = data.get("wksp_id", "")

            # Priority: mas_id first, then wksp_id, error if both empty
            if mas_id:
                # Convert hyphens to underscores for valid graph name
                graph_id = mas_id.replace("-", "_")
                return f"graph_{graph_id}"
            elif wksp_id:
                # Convert hyphens to underscores for valid graph name
                graph_id = wksp_id.replace("-", "_")
                return f"graph_{graph_id}"
            else:
                raise ValueError(
                    "Both mas_id and wksp_id are empty. At least one must be provided for graph name generation."
                )
        except Exception as e:
            self.logger.error(f"Error getting graph name: {str(e)}")
            raise

    def convert_to_models(self, data: Dict[str, Any]) -> Tuple[List[Node], List[Edge]]:
        """Convert KnowledgeGraphStoreRequest JSON to Node and Edge objects.

        Args:
            data: The parsed JSON data from KnowledgeGraphStoreRequest

        Returns:
            tuple: (list of Node objects, list of Edge objects)

        Raises:
            ValueError: If input data is invalid or conversion fails
        """
        nodes = []
        relationships = []

        try:
            # Extract common metadata
            mas_id = data.get("mas_id", "")
            wksp_id = data.get("wksp_id", "")
            memory_type = data.get("memory_type", "")

            # Process nodes
            if data.get("records") and "concepts" in data["records"] and data["records"]["concepts"]:
                self.logger.info(f"Processing {len(data['records']['concepts'])} concepts")
                nodes = self._process_concepts(data["records"]["concepts"], mas_id, wksp_id, memory_type)

            # Process relationships
            if data.get("records") and "relations" in data["records"] and data["records"]["relations"]:
                self.logger.info(f"Processing {len(data['records']['relations'])} relations")
                relationships = self._process_relations(data["records"]["relations"], mas_id, wksp_id, memory_type)

            self.logger.info(f"Successfully converted to {len(nodes)} nodes and {len(relationships)} edges")
            self.logger.debug(f"Nodes: {nodes}")
            self.logger.debug(f"Relationships: {relationships}")
            return nodes, relationships

        except Exception as e:
            self.logger.error(f"Error converting data to models: {str(e)}", exc_info=True)
            raise  # Re-raise to allow caller to handle the error

    def _generate_labels(self) -> List[str]:
        """Generate labels for a node."""
        # agensgraph supports single label only
        labels = ["Concept"]  # Default label
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

                # Add tags as property
                if "tags" in concept and concept["tags"]:
                    properties["tags"] = concept["tags"]

                # Handle embeddings
                if "embeddings" in concept and concept["embeddings"]:
                    self._process_embeddings(concept["embeddings"], properties)

                # Create node with default label
                labels = self._generate_labels()

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
        Convert a KnowledgeGraphQueryRequest into a list of Node objects for querying.

        Args:
            data: Dictionary containing the query request data following KnowledgeGraphQueryRequest schema

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

            # Add tags as property
            if "tags" in concept and concept["tags"]:
                properties["tags"] = concept["tags"]

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

            # Create node with default label
            labels = self._generate_labels()

            node = Node(id=concept.get("id", ""), labels=labels, properties=properties)
            nodes.append(node)

        return nodes

    def convert_models_to_query_response_records(
        self, db_results: List[Dict[str, Any]]
    ) -> List[KnowledgeGraphQueryResponseRecord]:
        """
        Convert database query results to a list of KnowledgeGraphQueryResponseRecord objects.

        This method transforms the neo4j results into a structured format that matches
        the KnowledgeGraphQueryResponseRecord schema.

        Args:
            db_results: List of query results from the database. Each result should be a dictionary
                      containing 'node', 'relationships', and 'neighbors' keys.

        Returns:
            List[KnowledgeGraphQueryResponseRecord]: A list of response records containing the converted data

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

            # Extract data
            edges_data = result.get("edges", [])
            nodes_data = result.get("nodes", [])

            # Create Relation objects
            relations = []
            for edge in edges_data:
                # Create Relation with required fields and handle potential None values
                self.logger.info(f"Converting model to Relation for response: {edge}")

                # Extract properties from edge - they might be nested in 'properties' key
                edge_props = edge.get("properties", edge)

                # Get relation from edge property 'relation'
                relation = edge_props.get("relation")
                # Parse node_ids JSON string back to list if needed
                node_ids = self._parse_json_field(edge_props.get("node_ids", []))

                # Skip invalid relations - relation must be a non-empty string and node_ids must have at least 2 items
                if not relation or not isinstance(relation, str) or len(node_ids) < 2:
                    self.logger.warning(f"Skipping invalid relation: relation='{relation}', node_ids={node_ids}")
                    continue

                # Initialize embeddings as None, only create EmbeddingConfig if we have embedding data
                embeddings = None
                if "embedding_vector" in edge_props or "embedding_model" in edge_props:
                    # Parse JSON string back to list if needed
                    embedding_vector = self._parse_json_field(edge_props.get("embedding_vector", []))

                    embeddings = EmbeddingConfig(data=embedding_vector, name=edge_props.get("embedding_model", ""))

                # Create attributes without the embedding fields
                edge_attributes = {
                    k: v
                    for k, v in edge_props.items()
                    if k not in ["id", "node_ids", "relation", "embedding_vector", "embedding_model", "embeddings"]
                }

                relations.append(
                    Relation(
                        id=edge_props.get("id", ""),
                        relation=relation,
                        node_ids=node_ids,
                        attributes=edge_attributes,
                        embeddings=embeddings,
                    )
                )
            self.logger.debug(f"Created {len(relations)} relations")

            # Create Concept objects for neighbor nodes
            concepts = []
            for node in nodes_data:
                self.logger.debug(f"Converting model to Concept for response: {node}")

                # Extract properties from node - they might be nested in 'properties' key
                node_props = node.get("properties", node)

                # Initialize embeddings as None, only create EmbeddingConfig if we have embedding data
                node_embeddings = None
                if "embedding_vector" in node_props or "embedding_model" in node_props:
                    # Parse JSON string back to list if needed
                    embedding_vector = self._parse_json_field(node_props.get("embedding_vector", []))

                    node_embeddings = EmbeddingConfig(data=embedding_vector, name=node_props.get("embedding_model", ""))

                # Create attributes without the embedding fields
                node_attributes = {
                    k: v
                    for k, v in node_props.items()
                    if k
                    not in ["id", "name", "description", "embedding_vector", "embedding_model", "embeddings", "tags"]
                }

                # Parse tags JSON string back to list if needed
                tags = self._parse_json_field(node_props.get("tags", []))

                concepts.append(
                    Concept(
                        id=node_props.get("id"),
                        name=node_props.get("name", ""),
                        description=node_props.get("description"),
                        attributes=node_attributes,
                        embeddings=node_embeddings,
                        tags=tags,
                    )
                )
            self.logger.debug(f"Created {len(concepts)} concepts")

            # Create the response record
            records.append(KnowledgeGraphQueryResponseRecord(relationships=relations, concepts=concepts))

        self.logger.debug(f"Converted {len(records)} records to KnowledgeGraphQueryResponseRecord objects")
        return records
