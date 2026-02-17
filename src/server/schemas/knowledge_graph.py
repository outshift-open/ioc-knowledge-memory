from typing import Dict, List, Literal, Optional, Any, Annotated
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, computed_field, BeforeValidator
from uuid import UUID, uuid4
from enum import Enum


class ResponseStatus(str, Enum):
    """Enum for response status values used across knowledge graph endpoints."""

    SUCCESS = "success"
    FAILURE = "failure"
    VALIDATION_ERROR = "validation error"
    NOT_FOUND = "not found"


class EmbeddingConfig(BaseModel):
    """Configuration for embeddings in the store."""

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


class KnowledgeGraphStoreRequest(BaseModel):
    """
    Represents a request to the Store for storing and managing knowledge graph data.

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
    records: Optional[Dict[Literal["concepts", "relations"], Any]] = Field(
        None, description="Dictionary containing concepts and relations"
    )

    memory_type: Optional[Literal["Semantic", "Procedural", "Episodic"]] = Field(
        None, description="Type of memory being stored"
    )
    mas_id: Optional[str] = Field(
        default=None, min_length=1, description="ID for the Multi-Agent System (Not required for Global Knowledge)"
    )
    wksp_id: Optional[str] = Field(default=None, min_length=1, description="ID for the Multi-Agent System Workspace")
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
    def validate_mas_or_wksp_id(self) -> "KnowledgeGraphStoreRequest":
        """Validate that either mas_id or wksp_id is provided."""
        if not self.mas_id and not self.wksp_id:
            raise ValueError("Either 'mas_id' or 'wksp_id' or both must be provided")
        return self

    @model_validator(mode="after")
    def validate_records_structure(self) -> "KnowledgeGraphStoreRequest":
        if self.records is None:
            return self

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


class KnowledgeGraphStoreResponse(BaseModel):
    """
    Represents a response from the Store after storing and managing knowledge graph data.

    Attributes:
        request_id: UUID for request tracking
        status: Status of the request
        message: Optional message providing additional information
    """

    model_config = ConfigDict(exclude_none=True)

    request_id: Optional[str] = Field(None, description="UUID for request tracking")
    status: ResponseStatus = Field(..., description="Status of the request")
    message: Optional[str] = Field(None, description="Optional message providing additional information")

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Override model_dump to conditionally exclude request_id field."""
        data = super().model_dump(**kwargs)

        # Remove request_id field if it's None
        if self.request_id is None and "request_id" in data:
            del data["request_id"]

        return data


class KnowledgeGraphDeleteRequest(BaseModel):
    """
    Represents a request to delete a store.

    Attributes:
        request_id: UUID for request tracking
        records: Dictionary containing 'concepts' keys with ids
        (Realtionships will be deleted as part of deleting Concepts)
    """

    request_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Auto-generated UUID for request tracking"
    )
    records: Optional[Dict[Literal["concepts"], Any]] = Field(None, description="Dictionary containing concepts")
    mas_id: Optional[str] = Field(
        default=None, min_length=1, description="ID for the Multi-Agent System (Not required for Global Knowledge)"
    )
    wksp_id: Optional[str] = Field(default=None, min_length=1, description="The workspace ID for the request")

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

    @model_validator(mode="after")
    def validate_mas_or_wksp_id(self) -> "KnowledgeGraphDeleteRequest":
        """Validate that either mas_id or wksp_id is provided."""
        if not self.mas_id and not self.wksp_id:
            raise ValueError("Either 'mas_id' or 'wksp_id' or both must be provided")
        return self


class KnowledgeGraphDeleteResponse(BaseModel):
    """
    Represents a response from the Store after deleting knowledge graph data.

    Attributes:
        request_id: UUID for request tracking
        status: Status of the request
        message: Optional message providing additional information
    """

    model_config = ConfigDict(exclude_none=True)

    request_id: Optional[str] = Field(None, description="UUID for request tracking")
    status: ResponseStatus = Field(..., description="Status of the request")
    message: Optional[str] = Field(None, description="Optional message providing additional information")

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Override model_dump to conditionally exclude request_id field."""
        data = super().model_dump(**kwargs)

        # Remove request_id field if it's None
        if self.request_id is None and "request_id" in data:
            del data["request_id"]

        return data


# Query models

QUERY_TYPE_NEIGHBOUR = "neighbour"
QUERY_TYPE_PATH = "path"
QUERY_TYPE_CONCEPT = "concept"


class KnowledgeGraphQueryCriteria(BaseModel):
    depth: Optional[int] = Field(
        default=1, description="Depth of the query (number of hops) to be used for path queries"
    )
    query_type: str = Field(default=QUERY_TYPE_NEIGHBOUR, description="Type of query to execute")


class KnowledgeGraphQueryRequest(BaseModel):
    """
    Represents a request to query the store.

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
    query_criteria: Optional[KnowledgeGraphQueryCriteria] = Field(
        default_factory=KnowledgeGraphQueryCriteria,  # This will create a new QueryCriteria with default values
        description="Query criteria",
    )

    @model_validator(mode="after")
    def validate_mas_or_wksp_id(self) -> "KnowledgeGraphQueryRequest":
        """Validate that either mas_id or wksp_id is provided."""
        if not self.mas_id and not self.wksp_id:
            raise ValueError("Either 'mas_id' or 'wksp_id' or both must be provided")
        return self

    @model_validator(mode="after")
    def validate_concepts_count_for_query_type(self) -> "KnowledgeGraphQueryRequest":
        """Validate that the number of concepts matches the query type requirements."""
        if not self.records or "concepts" not in self.records:
            raise ValueError("Records must exist with 'concepts' key")

        concepts = self.records.get("concepts", [])
        if not isinstance(concepts, list):
            raise ValueError("concepts must be a list")

        concepts_count = len(concepts)
        query_type = self.query_criteria.query_type if self.query_criteria else QUERY_TYPE_NEIGHBOUR

        if query_type == QUERY_TYPE_PATH:
            if concepts_count != 2:
                raise ValueError("Path queries require exactly 2 concepts (source and destination)")
        elif query_type == QUERY_TYPE_NEIGHBOUR:
            if concepts_count != 1:
                raise ValueError("Neighbor queries require exactly 1 concept")
        elif query_type == QUERY_TYPE_CONCEPT:
            if concepts_count != 1:
                raise ValueError("Concept queries require exactly 1 concept")
        else:
            # Default to neighbor query for QUERY_TYPE_NEIGHBOUR or any other type
            if concepts_count != 1:
                raise ValueError("Neighbor queries require exactly 1 concept")

        return self


class KnowledgeGraphQueryResponseRecord(BaseModel):
    relationships: List[Relation] = Field(default_factory=list)
    concepts: List[Concept] = Field(default_factory=list)


class KnowledgeGraphQueryResponse(BaseModel):
    """
    Represents a response from the Store after querying knowledge graph data.

    Attributes:
        request_id: UUID for request tracking
        status: Status of the request
        message: Optional message providing additional information
        records: Optional list of query response records (only included for success status)
    """

    model_config = ConfigDict(exclude_none=True)

    request_id: Optional[str] = Field(None, description="UUID for request tracking")
    status: ResponseStatus = Field(..., description="Status of the request")
    message: Optional[str] = Field(None, description="Optional message providing additional information")
    records: Optional[List[KnowledgeGraphQueryResponseRecord]] = Field(
        default=None, description="Query response records (only included for success status)"
    )

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Override model_dump to conditionally exclude records and request_id fields."""
        data = super().model_dump(**kwargs)

        # Remove records field if status is not success OR if records is None/empty
        if (self.records is None or (isinstance(self.records, list) and len(self.records) == 0)) and "records" in data:
            del data["records"]

        # Remove request_id field if it's None
        if self.request_id is None and "request_id" in data:
            del data["request_id"]

        return data
