# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import Dict, List, Literal, Optional, Any, Annotated, Union, ClassVar
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from server.schemas.knowledge_graph_utils import validate_uuid_field

# Constants
DEFAULT_PROPERTY_KEY_SEPARATOR = "$"


class FilterOperation(str, Enum):
    """Enum for filter operations used in concept queries."""
    EQSTR = "eqstr"
    EQ = "eq" 
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    RANGE = "range"


class FilterCategory(str, Enum):
    """Enum for filter categories."""
    CUSTOM = "custom"     # For custom attributes (Eg. computes attributes)
    DYNAMIC = "dynamic"   # For dynamic attributes
    INTERNAL = "internal" # For internal attributes


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

class InternalAttributes(BaseModel):
    """Represents a internal attribute in the knowledge graph."""
    owner: str = Field(..., description="Identifier for the attribute owner (must be a valid UUID)")
    attributes: Optional[Dict[str, Union[str, int, float]]] = Field(
        default_factory=dict, description="Additional attributes for the concept (strings and numbers only)"
    )
    
    @field_validator("owner")
    @classmethod
    def validate_owner_is_uuid(cls, v: str) -> str:
        """Validate that owner is a valid UUID."""
        return validate_uuid_field(v, "owner")

class Concept(BaseModel):
    """Represents a concept in the knowledge graph."""
    
    model_config = ConfigDict(exclude_none=True)

    id: str = Field(..., description="Unique identifier for the concept")
    name: str = Field(..., description="Name of the concept")
    description: Optional[str] = Field(None, description="Detailed description of the concept")
    attributes: Optional[Dict[str, Union[str, int, float]]] = Field(
        default_factory=dict, description="Additional attributes for the concept (strings and numbers only)"
    )
    embeddings: Optional[EmbeddingConfig] = Field(None, description="Embedding configuration for the concept")
    tags: Optional[List[str]] = Field(default_factory=list, description="Optional list of tags for categorization")
    internal_attributes: Optional[List[InternalAttributes]] = Field(None, description="Internal attributes for the concept")


class Relation(BaseModel):
    """Represents a relationship between concepts."""
    
    model_config = ConfigDict(exclude_none=True)

    id: str = Field(..., description="Unique identifier for the relation")
    relation: str = Field(..., description="Type of relationship between nodes")
    node_ids: Annotated[
        List[str], Field(..., min_length=2, description="List of node IDs this relation connects (minimum 2)")
    ]
    attributes: Optional[Dict[str, Union[str, int, float]]] = Field(
        default_factory=dict, description="Additional attributes for the relation (strings and numbers only)"
    )
    embeddings: Optional[EmbeddingConfig] = Field(None, description="Embedding configuration for the relation")
    internal_attributes: Optional[List[InternalAttributes]] = Field(None, description="Internal attributes for the relation")

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
    incremental_update: bool = Field(
        False,
        description="Indicates an incremental update where relations may reference nodes already present in the graph.",
    )

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
            # different metadata (eg wksp_id, mas_id, memory_type).
            # Skipped for incremental updates where relations may reference existing graph nodes.
            if not self.incremental_update:
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


class KnowledgeGraphFetchResponse(BaseModel):
    """Response containing all nodes and edges in a knowledge graph."""

    model_config = ConfigDict(exclude_none=True)

    status: ResponseStatus = Field(..., description="Status of the request")
    message: Optional[str] = Field(None, description="Optional message")
    graph_name: Optional[str] = Field(None, description="Name of the graph")
    nodes: Optional[List[Concept]] = Field(default=None, description="All nodes in the graph")
    relations: Optional[List[Relation]] = Field(default=None, description="All edges in the graph")

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)


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


# Similarity search models


class KnowledgeGraphSimilaritySearchRequest(BaseModel):
    """Request for vector similarity search over graph nodes."""

    request_id: str = Field(
        default_factory=lambda: str(uuid4()), description="Auto-generated UUID for request tracking"
    )
    mas_id: Optional[str] = Field(default=None, min_length=1, description="ID for the Multi-Agent System")
    wksp_id: Optional[str] = Field(default=None, min_length=1, description="The workspace ID for the request")
    embedding: List[float] = Field(..., description="Query embedding vector")
    limit: int = Field(default=10, ge=1, le=100, description="Maximum number of results to return")
    metric: Literal["cosine", "l2", "inner-product"] = Field(default="l2", description="Distance metric")

    @model_validator(mode="after")
    def validate_mas_or_wksp_id(self) -> "KnowledgeGraphSimilaritySearchRequest":
        if not self.mas_id and not self.wksp_id:
            raise ValueError("Either 'mas_id' or 'wksp_id' or both must be provided")
        return self


class KnowledgeGraphSimilaritySearchResult(BaseModel):
    """A single similarity search result."""

    score: float = Field(..., description="Distance from query vector")
    embedded_text: str = Field(..., description="Text that was embedded (concept name)")
    concept_id: str = Field(..., description="Concept node ID")
    concept_name: str = Field(..., description="Concept name")
    embedding_vector: Optional[List[float]] = Field(default=None, description="Embedding vector (only populated when include_embeddings=true)")


class KnowledgeGraphSimilaritySearchResponse(BaseModel):
    """Response for embedding vector similarity search."""

    model_config = ConfigDict(exclude_none=True)

    request_id: Optional[str] = Field(None, description="UUID for request tracking")
    status: ResponseStatus = Field(..., description="Status of the request")
    message: Optional[str] = Field(None, description="Optional message")
    results: Optional[List[KnowledgeGraphSimilaritySearchResult]] = Field(
        default=None, description="Similarity search results"
    )

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)


# Query models

QUERY_TYPE_NEIGHBOUR = "neighbour"
QUERY_TYPE_PATH = "path"
QUERY_TYPE_CONCEPT = "concept"
QUERY_TYPE_FULL_GRAPH = "full_graph"
QUERY_TYPE_CONCEPTS = "concepts"
QUERY_TYPE_RELATIONS = "relations"

class KnowledgeGraphQueryCriteriaFilter(BaseModel):
    """Generic key-operation-value filter for concept queries."""
    
    # Define allowed values as class constants
    CATEGORY_ALLOW: ClassVar[List[str]] = [e.value for e in FilterCategory]
    OPERATION_ALLOW: ClassVar[List[str]] = [e.value for e in FilterOperation]
    CONCEPTS_CUSTOM_KEY_ALLOW: ClassVar[List[str]] = ["id", "name", "relations_cnt"]
    RELATIONS_CUSTOM_KEY_ALLOW: ClassVar[List[str]] = ["id", "relation"]
    
    # Define specific key constants
    KEY_RELATIONS_CNT: ClassVar[str] = "relations_cnt"
    KEY_ID: ClassVar[str] = "id"
    KEY_NAME: ClassVar[str] = "name"
    KEY_RELATION: ClassVar[str] = "relation"
    
    category: FilterCategory = Field(..., description=f"Type of filter key ({', '.join(CATEGORY_ALLOW)})")
    
    key: str = Field(..., description=f"Key to filter on (custom: {', '.join(CONCEPTS_CUSTOM_KEY_ALLOW)}; dynamic: any property)")
    operation: FilterOperation = Field(..., description=f"Comparison operation ({', '.join(OPERATION_ALLOW)})")
    value: List[Union[int, str, float]] = Field(..., min_length=1, description="Value(s) to compare against")
    owner: Optional[str] = Field(None, description="Owner UUID for internal attributes (must be a valid UUID)")
    
    # Get query_type from outer context
    def get_query_type(self) -> Optional[str]:
        return getattr(self, '_query_type', None)

    @field_validator("value", mode="after")
    @classmethod
    def validate_value(cls, v: List[Union[int, str, float]], info) -> List[Union[int, str, float]]:
        """Validate value array based on operation."""
        if not v:
            raise ValueError("Value array cannot be empty")
        
        # Get operation from the model context
        operation = info.data.get("operation")
        
        # Validate value types based on operation
        if operation == FilterOperation.EQSTR:
            # eqstr operation should only have string values
            if not all(isinstance(x, str) for x in v):
                raise ValueError("eqstr operation requires string values only")
            if len(v) != 1:
                raise ValueError("eqstr operation requires exactly 1 value")
        else:
            # All other operations should have non-string values (numeric)
            if any(isinstance(x, str) for x in v):
                raise ValueError(f"Operation '{operation}' requires non-string values (numeric only)")
            
            if operation == FilterOperation.RANGE:
                if len(v) != 2:
                    raise ValueError("Range operation requires exactly 2 values")
                # Ensure min <= max for numeric ranges
                if v[0] > v[1]:
                    raise ValueError("Range: first value (min) must be <= second value (max)")
            else:
                if len(v) != 1:
                    raise ValueError(f"Operation '{operation}' requires exactly 1 value")
        
        return v
    
    @field_validator("category", mode="after")
    @classmethod
    def validate_category(cls, v: str) -> str:
        """Validate category is in allowed list."""
        if v not in cls.CATEGORY_ALLOW:
            raise ValueError(f"Category '{v}' not allowed. Must be one of: {cls.CATEGORY_ALLOW}")
        return v
    
    @field_validator("operation", mode="after")
    @classmethod
    def validate_operation(cls, v: str) -> str:
        """Validate operation is in allowed list."""
        if v not in cls.OPERATION_ALLOW:
            raise ValueError(f"Operation '{v}' not allowed. Must be one of: {cls.OPERATION_ALLOW}")
        return v
        
    @model_validator(mode="after")
    def validate_custom_key_allowlist(self) -> "KnowledgeGraphQueryCriteriaFilter":
        """Validate that custom category keys are in the allowed list."""
        query_type = self.get_query_type()

        if self.category == FilterCategory.CUSTOM and query_type == QUERY_TYPE_CONCEPTS and self.key not in self.CONCEPTS_CUSTOM_KEY_ALLOW:
            raise ValueError(f"Custom category key '{self.key}' not allowed. Must be one of: {self.CONCEPTS_CUSTOM_KEY_ALLOW}")
        if self.category == FilterCategory.CUSTOM and query_type == QUERY_TYPE_RELATIONS and self.key not in self.RELATIONS_CUSTOM_KEY_ALLOW:
            raise ValueError(f"Custom category key '{self.key}' not allowed. Must be one of: {self.RELATIONS_CUSTOM_KEY_ALLOW}")
        
        return self
    
    @model_validator(mode="after")
    def validate_operation_for_custom_keys(self) -> "KnowledgeGraphQueryCriteriaFilter":
        """Validate operations based on custom key types."""
        if self.category == FilterCategory.CUSTOM:
            # String-only keys: id, name, relation - only EQSTR allowed
            string_keys = [self.KEY_ID, self.KEY_NAME, self.KEY_RELATION]
            # Numeric-only keys: relations_cnt - EQSTR not allowed
            numeric_keys = [self.KEY_RELATIONS_CNT]
            
            if self.key in string_keys:
                if self.operation != FilterOperation.EQSTR:
                    raise ValueError(f"Custom key '{self.key}' only supports EQSTR operation, got '{self.operation}'")
            elif self.key in numeric_keys:
                if self.operation == FilterOperation.EQSTR:
                    raise ValueError(f"Custom key '{self.key}' does not support EQSTR operation, use numeric operations (eq, gt, gte, lt, lte, range)")
        
        return self
    
    @field_validator("owner")
    @classmethod
    def validate_owner(cls, v: Optional[str]) -> Optional[str]:
        """Validate that owner is a valid UUID when provided."""
        return validate_uuid_field(v, "owner")


class KnowledgeGraphQueryCriteria(BaseModel):
    depth: Optional[int] = Field(
        default=None, description="Depth of the query (number of hops) to be used for path queries"
    )
    use_direction: Optional[bool] = Field(
        default=True, description="Whether to use directed relationships in path queries"
    )
    query_type: str = Field(default=QUERY_TYPE_NEIGHBOUR, description="Type of query to execute")
    filters: Optional[List[KnowledgeGraphQueryCriteriaFilter]] = Field(
        default=None, description="List of structured filters for filtering concepts and relations"
    )
    
    @model_validator(mode="after")
    def validate_filter_count(self) -> "KnowledgeGraphQueryCriteria":
        """Validate that filters contains only a single filter entry."""
        if self.filters is not None:
            if len(self.filters) == 0:
                raise ValueError("Unsupported: filters list cannot be empty")
            elif len(self.filters) > 1:
                raise ValueError("Unsupported: only a single KnowledgeGraphQueryCriteriaFilter entry is allowed in the list")
        
        return self
    
    @model_validator(mode="after") 
    def validate_filter_with_query_type(self) -> "KnowledgeGraphQueryCriteria":
        """Pass query_type context to all filters for validation."""
        if self.filters is not None and len(self.filters) > 0:
            # Add query_type context to all filters for validation
            for filter_obj in self.filters:
                # Store query_type in a private attribute for each filter to access
                filter_obj._query_type = self.query_type
        
        return self


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
    records: Optional[Dict[Literal["concepts"], Any]] = Field(None, description="Dictionary containing 'concepts' keys. Not required for full_graph queries.")
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
        query_type = self.query_criteria.query_type if self.query_criteria else QUERY_TYPE_NEIGHBOUR

        if query_type == QUERY_TYPE_FULL_GRAPH:
            return self
        
        if query_type == QUERY_TYPE_CONCEPTS:
            return self
            
        if query_type == QUERY_TYPE_RELATIONS:
            return self

        if not self.records or "concepts" not in self.records:
            raise ValueError("Records must exist with 'concepts' key")

        concepts = self.records.get("concepts", [])
        if not isinstance(concepts, list):
            raise ValueError("concepts must be a list")

        concepts_count = len(concepts)

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
            if concepts_count != 1:
                raise ValueError("Neighbor queries require exactly 1 concept")

        return self


class KnowledgeGraphQueryResponseRecord(BaseModel):
    model_config = ConfigDict(exclude_none=True)
    
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
        kwargs.setdefault("exclude_none", True)
        data = super().model_dump(**kwargs)

        # Remove records field if status is not success OR if records is None/empty
        if (self.records is None or (isinstance(self.records, list) and len(self.records) == 0)) and "records" in data:
            del data["records"]

        # Remove request_id field if it's None
        if self.request_id is None and "request_id" in data:
            del data["request_id"]

        return data
