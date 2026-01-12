from typing import Dict, List, Literal, Optional, Any, Annotated
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, BeforeValidator
from uuid import UUID, uuid4


class EmbeddingConfig(BaseModel):
    """Configuration for embeddings in the TKF store."""

    name: str = Field(..., description="Name of the embedding model (e.g., huggingface model name)")
    data: List[float] = Field(default_factory=list, description="Embedding vector data")


class Concept(BaseModel):
    """Represents a concept in the knowledge graph."""

    id: str = Field(..., description="Unique identifier for the concept")
    name: str = Field(..., description="Name of the concept")
    description: Optional[str] = Field(None, description="Detailed description of the concept")
    attributes: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional attributes for the concept"
    )
    embeddings: Optional[EmbeddingConfig] = Field(None, description="Embedding configuration for the concept")
    tags: Optional[List[str]] = Field(default_factory=list, description="Optional list of tags for categorization")


class Relation(BaseModel):
    """Represents a relationship between concepts."""

    id: str = Field(..., description="Unique identifier for the relation")
    relation: str = Field(..., description="Type of relationship between nodes")
    node_ids: Annotated[
        List[str], Field(..., min_length=2, description="List of node IDs this relation connects (minimum 2)")
    ]
    attributes: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional attributes for the relation"
    )
    embeddings: Optional[EmbeddingConfig] = Field(None, description="Embedding configuration for the relation")

    @field_validator("node_ids", mode="after")
    @classmethod
    def validate_node_count(cls, v: List[str]) -> List[str]:
        if len(v) < 2:
            raise ValueError("A relation must connect at least 2 nodes")
        return v


class TkfStoreRequest(BaseModel):
    """
    Represents a request to the TKF Store for storing and managing knowledge graph data.

    Attributes:
        request_id: Optional UUID for request tracking
        records: Dictionary containing concepts and relations
        memory_type: Type of memory (Semantic, Procedural, or Episodic)
        mas_id: ID for the MAS (Multi-Agent System)
        wksp_id: ID for the Workspace
    """

    request_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Auto-generated UUID for request tracking"
    )
    records: Dict[Literal["concepts", "relations"], Any] = Field(
        ..., description="Dictionary containing concepts and relations"
    )

    memory_type: Literal["Semantic", "Procedural", "Episodic"] = Field(..., description="Type of memory being stored")
    mas_id: Optional[str] = Field(
        default=None, min_length=1, description="ID for the Multi-Agent System (Not required for Global Knowledge)"
    )
    wksp_id: str = Field(..., min_length=1, description="Mandatory ID for the Multi-Agent System Workspace")
    force_replace: bool = Field(False, description="Force replace existing nodes and edges")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "request_id": "bbc2fea0-5e6c-4cf9-b7b4-fe6418c041a0",
                    "mas_id": "test-mas",
                    "wksp_id": "test-wksp",
                    "memory_type": "Semantic",
                    "force_replace": False,
                    "records": {
                        "concepts": [
                            {
                                "id": "123e4567-e89b-12d3-a456-426614174001",
                                "name": "Artificial Intelligence",
                                "description": "AI technology",
                                "tags": ["AI", "ML"],
                                "attributes": {"key": "value"},
                                "embeddings": {"name": "text-embedding-ada-002", "data": [0.1, 0.2, 0.3]},
                            },
                            {
                                "id": "223e4567-e89b-12d3-a456-426614174001",
                                "name": "Machine Learning",
                                "description": "Machine Learning",
                                "embeddings": {"name": "text-embedding-ada-002", "data": [0.3]},
                            },
                        ],
                        "relations": [
                            {
                                "id": "223e4567-e89b-12d3-a456-426614174002",
                                "relation": "HAS_SUBCONCEPT",
                                "node_ids": [
                                    "123e4567-e89b-12d3-a456-426614174001",
                                    "223e4567-e89b-12d3-a456-426614174001",
                                ],
                                "attributes": {"dynamic_key": "dynamic_value"},
                            }
                        ],
                    },
                }
            ]
        }
    )

    @model_validator(mode="after")
    def validate_records_structure(self) -> "TkfStoreRequest":
        if not isinstance(self.records, dict):
            raise ValueError("Records must be a dictionary")

        if not isinstance(self.records.get("concepts"), list):
            raise ValueError("'concepts' must be a list of concept nodes")

        if not isinstance(self.records.get("relations"), list):
            raise ValueError("'relations' must be a list of relations")

        # Get all concept IDs for reference
        concept_ids = {concept.get("id") for concept in self.records.get("concepts", [])}

        # Validate that all node_ids in relations exist in concepts
        for relation in self.records.get("relations", []):
            if not isinstance(relation, dict):
                continue

            node_ids = relation.get("node_ids", [])
            if not isinstance(node_ids, list):
                continue

            # validate that edges only contain nodes specified in this requests nodes
            # to avoid connecting edges between nodes with
            # different metadata (eg wksp_id, mas_id, memory_type)
            for node_id in node_ids:
                if node_id not in concept_ids:
                    raise ValueError(
                        f"Relation {relation.get('id', 'unknown')} references non-existent node ID '{node_id}'. "
                        f"Node IDs must be present in the 'concepts' list. "
                        f"Available concept IDs: {', '.join(map(str, sorted(concept_ids))) or 'None'}"
                    )

        return self


class TkfStoreResponse(BaseModel):
    """
    Represents a response from the TKF Store after storing and managing knowledge graph data.

    Attributes:
        request_id: UUID for request tracking
        status: Status of the request (success or failure)
        message: Optional message providing additional information
    """

    request_id: str = Field(..., description="UUID for request tracking")
    status: Literal["success", "failure"] = Field(..., description="Status of the request")
    message: Optional[str] = Field(None, description="Optional message providing additional information")


class TkfDeleteRequest(BaseModel):
    """
    Represents a request to delete a TKF store.

    Attributes:
        request_id: UUID for request tracking
        records: Dictionary containing 'concepts' keys with ids
        (Realtionships will be deleted as part of deleting Concepts)
    """

    request_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Auto-generated UUID for request tracking"
    )
    records: Dict[Literal["concepts"], Any] = Field(..., description="Dictionary containing 'concepts' keys")
    mas_id: Optional[str] = Field(
        default=None, min_length=1, description="ID for the Multi-Agent System (Not required for Global Knowledge)"
    )
    wksp_id: str = Field(..., description="The workspace ID for the request")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "request_id": "bbc2fea0-5e6c-4cf9-b7b4-fe6418c041a0",
                    "mas_id": "test-mas",
                    "wksp_id": "test-wksp",
                    "records": {
                        "concepts": [
                            {"id": "123e4567-e89b-12d3-a456-426614174001"},
                            {"id": "223e4567-e89b-12d3-a456-426614174001"},
                        ]
                    },
                }
            ]
        }
    )


class TkfDeleteResponse(BaseModel):
    """
    Represents a response from the TKF Store after deleting knowledge graph data.

    Attributes:
        request_id: UUID for request tracking
        status: Status of the request (success or failure)
        message: Optional message providing additional information
    """

    request_id: str = Field(..., description="UUID for request tracking")
    status: Literal["success", "failure"] = Field(..., description="Status of the request")
    message: Optional[str] = Field(None, description="Optional message providing additional information")


# TKF Query models

QUERY_TYPE_NEIGHBOUR = "neighbour"


class QueryCriteria(BaseModel):
    depth: Optional[int] = Field(default=1, description="Depth of the query (number of hops)")  # Unused
    limit: Optional[int] = Field(
        default=None,
        description="Maximum number of results to return. "  # Unused
        "Unspecified will return all results",
    )
    query_type: str = Field(default=QUERY_TYPE_NEIGHBOUR, description="Type of query to execute")


class TkfQueryRequest(BaseModel):
    """
    Represents a request to query the TKF store.

    Attributes:
        request_id: UUID for request tracking
        records: Dictionary containing 'concepts' keys
        memory_type: Optional Type of memory (Semantic, Procedural, or Episodic)
        mas_id: Optional ID for the MAS (Multi-Agent System)
        wksp_id: Optional ID for the Workspace
        query_criteria: Query criteria
    """

    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Auto-generated UUID for request tracking used if not passed in request",
    )
    records: Dict[Literal["concepts"], Any] = Field(..., description="Dictionary containing 'concepts' keys")
    memory_type: Optional[str] = Field(default=None, min_length=1, description="Memory type")
    mas_id: Optional[str] = Field(default=None, min_length=1, description="ID for the Multi-Agent System")
    wksp_id: Optional[str] = Field(default=None, min_length=1, description="ID for the Workspace")
    query_criteria: Optional[QueryCriteria] = Field(
        default_factory=QueryCriteria,  # This will create a new QueryCriteria with default values
        description="Query criteria",
    )


class TkfQueryResponseRecord(BaseModel):
    queried_concept: Optional[Concept] = None
    # empty if no results
    relationships: List[Relation] = Field(default_factory=list)
    concepts: List[Concept] = Field(default_factory=list)


class TkfQueryResponse(BaseModel):
    """
    Represents a response from the TKF Store after querying knowledge graph data.

    Attributes:
        request_id: UUID for request tracking
        status: Status of the request (success or failure)
        message: Optional message providing additional information
    """

    request_id: str = Field(..., description="UUID for request tracking")
    status: Literal["success", "failure"] = Field(..., description="Status of the request")
    message: Optional[str] = Field(None, description="Optional message providing additional information")
    records: List[TkfQueryResponseRecord] = Field(default_factory=list)
