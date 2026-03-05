import os
from enum import Enum
from typing import Dict, List, Literal, Optional, Any, Annotated
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator, model_serializer

EMBEDDING_VECTOR_SIZE_DEFAULT = 384


def get_embedding_vector_size() -> int:
    """
    Get the embedding vector size from environment variable or use default.

    Returns:
        int: Embedding vector size
    """
    try:
        env_size = os.getenv("EMBEDDING_VECTOR_SIZE")
        if env_size is not None:
            return int(env_size)
    except (ValueError, TypeError):
        pass
    return EMBEDDING_VECTOR_SIZE_DEFAULT


EMBEDDING_VECTOR_SIZE = get_embedding_vector_size()


class ResponseStatus(str, Enum):
    """Enum for response status values used across knowledge vector endpoints."""

    SUCCESS = "success"
    FAILURE = "failure"
    VALIDATION_ERROR = "validation error"
    NOT_FOUND = "not found"


class KnowledgeVectorStoreOnboardRequest(BaseModel):
    """
    Represents a request to setup the Vector store for storing and managing knowledge vector data.
    Creates essential entities for the vector store to function and provide partiioning by workspace.

    Attributes:
        request_id: Optional UUID for request tracking
        wksp_id: ID for the Workspace
    """

    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Auto-generated UUID for request tracking used if not passed in request",
    )


class KnowledgeVectorStoreOnboardResponse(BaseModel):
    """
    Represents a response from the create Container request.

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
        """Override model_dump to ensure exclude_none is always applied."""
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)


class KnowledgeVectorStoreOnboardDeleteRequest(BaseModel):
    """
    Represents a request to delete the Container used for storing and managing knowledge vector data.
    Container is a workspace schema and the table for storing and managing knowledge vector data.

    Attributes:
        request_id: Optional UUID for request tracking
        wksp_id: ID for the Workspace
    """

    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Auto-generated UUID for request tracking used if not passed in request",
    )


class KnowledgeVectorStoreOnboardDeleteResponse(BaseModel):
    """
    Represents a response from the delete Container request.

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
        """Override model_dump to ensure exclude_none is always applied."""
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)


class EmbeddingConfig(BaseModel):
    """Configuration for embeddings in the store."""

    data: List[float] = Field(default_factory=list, description="Embedding vector data")

    @field_validator("data")
    @classmethod
    def validate_embedding_size(cls, v):
        """Validate that embedding data matches the expected vector size."""
        if len(v) != EMBEDDING_VECTOR_SIZE:
            raise ValueError(f"Embedding data must have exactly {EMBEDDING_VECTOR_SIZE} dimensions, got {len(v)}")
        return v


class KnowledgeVectorStoreRequestRecord(BaseModel):
    """Represents a vector in the knowledge vector store."""

    id: str = Field(..., description="Unique identifier")
    content: str = Field(..., description="content in plain text")
    embedding: EmbeddingConfig = Field(..., description="Embedding")


class KnowledgeVectorStoreRequest(BaseModel):
    """
    Represents a request to the Store for storing and managing knowledge vector data.
    Either all records are upserted or None (Runs as a transaction)

    Attributes:
        request_id: Optional UUID for request tracking
        wksp_id: ID for the Workspace
        mas_id: ID for the MAS (Multi-Agent System)
        records: List of KnowledgeVectorStoreRequestRecord
    """

    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Auto-generated UUID for request tracking used if not passed in request",
    )
    wksp_id: str = Field(min_length=1, description="ID for the Multi-Agent System Workspace")
    mas_id: str = Field(min_length=1, description="ID for the Multi-Agent System")
    records: List[KnowledgeVectorStoreRequestRecord] = Field(default_factory=list, description="List of vector records")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "request_id": "bbc2fea0-5e6c-4cf9-b7b4-fe6418c041a0",
                    "wksp_id": "123e4567-e89b-12d3-a456-426614174001",
                    "mas_id": "223e4567-e89b-12d3-a456-426614174001",
                    "records": [
                        {
                            "id": "123e4567-e89b-12d3-a456-426614174001",
                            "content": "content in plain text",
                            "embedding": {"data": [0.1, 0.2, 0.3]},
                        },
                        {
                            "id": "223e4567-e89b-12d3-a456-426614174001",
                            "content": "content in plain text",
                            "embedding": {"data": [0.3]},
                        },
                    ],
                }
            ]
        }
    )

    @model_validator(mode="after")
    def validate_mas_and_wksp_id(self) -> "KnowledgeVectorStoreRequest":
        """Validate that both mas_id or wksp_id is provided."""
        if not self.mas_id or not self.wksp_id:
            raise ValueError("Both 'mas_id' and 'wksp_id' must be provided")
        return self

    @model_validator(mode="after")
    def validate_records_structure(self) -> "KnowledgeVectorStoreRequest":
        if not self.records:
            return self

        if not isinstance(self.records, list):
            raise ValueError("Records must be a list")

        for i, record in enumerate(self.records):
            if not hasattr(record, "id") or not hasattr(record, "embedding"):
                raise ValueError(f"Record at index {i} must have 'id' and 'embeddings' fields")

        return self


class KnowledgeVectorStoreResponse(BaseModel):
    """
    Represents a response from the Store after storing and managing knowledge vector data.

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
        """Override model_dump to ensure exclude_none is always applied."""
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)


# Deletion models


class KnowledgeVectorDeleteRequest(BaseModel):
    """
    Represents a request to delete a store.

    Attributes:
        request_id: UUID for request tracking
        records: Dictionary containing 'vectors' keys with ids
    """

    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Auto-generated UUID for request tracking used if not passed in request",
    )
    wksp_id: str = Field(min_length=1, description="The workspace ID for the request")
    mas_id: str = Field(min_length=1, description="ID for the Multi-Agent System")
    id: str = Field(min_length=1, description="ID of vector to delete")
    soft_delete: bool = Field(default=True, description="Soft delete the vector")

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "request_id": "bbc2fea0-5e6c-4cf9-b7b4-fe6418c041a0",
                    "wksp_id": "123e4567-e89b-12d3-a456-426614174001",
                    "mas_id": "223e4567-e89b-12d3-a456-426614174001",
                    "id": "123e4567-e89b-12d3-a456-426614174001",
                }
            ]
        }
    )

    @model_validator(mode="after")
    def validate_mas_and_wksp_id(self) -> "KnowledgeVectorDeleteRequest":
        """Validate that both mas_id or wksp_id is provided."""
        if not self.mas_id or not self.wksp_id:
            raise ValueError("Both 'mas_id' and 'wksp_id' must be provided")
        return self


class KnowledgeVectorDeleteResponse(BaseModel):
    """
    Represents a response from the Store after deleting knowledge vector data.

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
        """Override model_dump to ensure exclude_none is always applied."""
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)


# Query models

# Generic Internal queries
QUERY_TYPE_INTERNAL_LIST_BY_WKSP_ID = "list_by_wksp_id"
QUERY_TYPE_INTERNAL_LIST_BY_MAS_ID = "list_by_mas_id"
# External queries
QUERY_TYPE_GET_BY_ID = "get_by_id"
QUERY_TYPE_DISTANCE_L2 = "distance_l2"
QUERY_TYPE_DISTANCE_COSINE = "distance_cosine"


class KnowledgeVectorQueryCriteria(BaseModel):
    query_type: str = Field(None, description="Type of query to execute")
    id: Optional[str] = Field(None, description="ID of vector to query")
    embedding: Optional[EmbeddingConfig] = Field(None, description="Embedding for query")
    limit: Optional[int] = Field(default=None, description="limit used by queries")


class KnowledgeVectorQueryRequest(BaseModel):
    """
    Represents a request to query the store.

    Attributes:
        request_id: UUID for request tracking
        wksp_id: ID for the Workspace
        mas_id: ID for the MAS (Multi-Agent System)
        embedding: Embedding for query
        query_criteria: Query criteria
    """

    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Auto-generated UUID for request tracking used if not passed in request",
    )
    wksp_id: str = Field(min_length=1, description="ID for the Workspace")
    mas_id: str = Field(min_length=1, description="ID for the Multi-Agent System")
    query_criteria: KnowledgeVectorQueryCriteria = Field(
        default_factory=KnowledgeVectorQueryCriteria,  # This will create a new QueryCriteria with default values
        description="Query criteria",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "description": "List all vectors by workspace",
                    "request_id": "bbc2fea0-5e6c-4cf9-b7b4-fe6418c041a0",
                    "wksp_id": "9f136aa0-143c-46a6-82f2-249eac489e52",
                    "mas_id": "223e4567-e89b-12d3-a456-426614174001",
                    "query_criteria": {"query_type": "list_by_wksp_id", "limit": 10},
                },
                {
                    "description": "List all vectors by MAS",
                    "request_id": "cbc2fea0-5e6c-4cf9-b7b4-fe6418c041a1",
                    "wksp_id": "9f136aa0-143c-46a6-82f2-249eac489e52",
                    "mas_id": "223e4567-e89b-12d3-a456-426614174001",
                    "query_criteria": {"query_type": "list_by_mas_id", "limit": 5},
                },
                {
                    "description": "Get specific vector by ID",
                    "request_id": "dbc2fea0-5e6c-4cf9-b7b4-fe6418c041a2",
                    "wksp_id": "9f136aa0-143c-46a6-82f2-249eac489e52",
                    "mas_id": "223e4567-e89b-12d3-a456-426614174001",
                    "query_criteria": {"query_type": "get_by_id", "id": "123e4567-e89b-12d3-a456-426614174001"},
                },
                {
                    "description": "L2 distance similarity search",
                    "request_id": "ebc2fea0-5e6c-4cf9-b7b4-fe6418c041a3",
                    "wksp_id": "9f136aa0-143c-46a6-82f2-249eac489e52",
                    "mas_id": "223e4567-e89b-12d3-a456-426614174001",
                    "query_criteria": {"query_type": "distance_l2", "embedding": {"data": [0.1, 0.2, 0.3]}, "limit": 5},
                },
                {
                    "description": "Cosine similarity search",
                    "request_id": "fbc2fea0-5e6c-4cf9-b7b4-fe6418c041a4",
                    "wksp_id": "9f136aa0-143c-46a6-82f2-249eac489e52",
                    "mas_id": "223e4567-e89b-12d3-a456-426614174001",
                    "query_criteria": {
                        "query_type": "distance_cosine",
                        "embedding": {"data": [0.4, 0.5, 0.6]},
                        "limit": 3,
                    },
                },
            ]
        }
    )

    @model_validator(mode="after")
    def validate_mas_and_wksp_id(self) -> "KnowledgeVectorQueryRequest":
        """Validate that both mas_id or wksp_id is provided."""
        if not self.mas_id or not self.wksp_id:
            raise ValueError("Both 'mas_id' and 'wksp_id' must be provided")
        return self

    @model_validator(mode="after")
    def validate_query_criteria(self) -> "KnowledgeVectorQueryRequest":
        """Validate query_criteria based on query_type."""
        if not self.query_criteria:
            return self

        query_type = self.query_criteria.query_type

        # Similarity search queries require embedding
        if query_type in [QUERY_TYPE_DISTANCE_L2, QUERY_TYPE_DISTANCE_COSINE]:
            if not self.query_criteria.embedding or not self.query_criteria.embedding.data:
                raise ValueError(f"Query type '{query_type}' requires embedding data")

        # Get by ID query requires id
        elif query_type == QUERY_TYPE_GET_BY_ID:
            if not self.query_criteria.id:
                raise ValueError(f"Query type '{query_type}' requires id field")

        # List queries don't require additional fields but validate query_type is valid
        elif query_type not in [QUERY_TYPE_INTERNAL_LIST_BY_WKSP_ID, QUERY_TYPE_INTERNAL_LIST_BY_MAS_ID]:
            raise ValueError(f"Invalid query_type: '{query_type}'")

        return self


class KnowledgeVectorQueryResponseRecord(BaseModel):
    id: str = Field(..., description="Unique identifier")
    content: str = Field(..., description="content in plain text")
    embedding: EmbeddingConfig = Field(..., description="Embedding configuration")
    distance: Optional[float] = Field(default=None, description="Distance between query and record")
    created_at: Optional[int] = Field(default=None, description="Timestamp of record creation in epoch time")
    updated_at: Optional[int] = Field(default=None, description="Timestamp of record update in epoch time")

    @model_serializer
    def serialize_model(self) -> Dict[str, Any]:
        """Custom serializer to exclude None fields."""
        data = {"id": self.id, "content": self.content, "embedding": self.embedding}
        if self.distance is not None:
            data["distance"] = self.distance
        if self.created_at is not None:
            data["created_at"] = self.created_at
        if self.updated_at is not None:
            data["updated_at"] = self.updated_at
        return data


class KnowledgeVectorQueryResponse(BaseModel):
    """
    Represents a response from the Store after querying knowledge vector data.

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
    records: Optional[List[KnowledgeVectorQueryResponseRecord]] = Field(
        default=None, description="Query response records (only included for success status)"
    )

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Override model_dump to ensure exclude_none is always applied."""
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)
