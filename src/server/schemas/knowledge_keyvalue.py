# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from enum import Enum
from typing import Dict, List, Optional, Any
from uuid import uuid4
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class ScopeType(str, Enum):
    """Enum for key-value store scope types."""

    MAS = "mas"
    CE = "ce"


def validate_uuid_format(value: str, field_name: str) -> str:
    """
    Validate that a string is in proper UUID format (with hyphens).

    Args:
        value: The UUID string to validate
        field_name: Name of the field for error messages

    Returns:
        str: The validated UUID string

    Raises:
        ValueError: If the UUID format is invalid
    """
    if not value:
        return value

    # UUID pattern: 8-4-4-4-12 hexadecimal digits separated by hyphens
    uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

    if not re.match(uuid_pattern, value.lower()):
        raise ValueError(f"{field_name} must be a valid UUID format (e.g., 123e4567-e89b-12d3-a456-426614174000)")

    return value


def validate_scope_requirements(model_instance):
    """
    Shared validation helper for scope-based field requirements.
    Used for data operations (store, delete, query) that require specific fields.

    Validation rules:
    - For MAS scope: wksp_id and mas_id are required
    - For CE scope: ce_id is required
    - agent_id is always optional

    Args:
        model_instance: Pydantic model instance with scope, wksp_id, mas_id, ce_id attributes

    Returns:
        model_instance: The validated model instance

    Raises:
        ValueError: If required fields are missing for the specified scope
    """
    if model_instance.scope == ScopeType.MAS:
        if not getattr(model_instance, "wksp_id", None):
            raise ValueError("wksp_id is required for MAS scope")
        if not getattr(model_instance, "mas_id", None):
            raise ValueError("mas_id is required for MAS scope")
    elif model_instance.scope == ScopeType.CE:
        if not getattr(model_instance, "ce_id", None):
            raise ValueError("ce_id is required for CE scope")
    return model_instance


class ResponseStatus(str, Enum):
    """Enum for response status values used across knowledge key-value endpoints."""

    SUCCESS = "success"
    FAILURE = "failure"
    VALIDATION_ERROR = "validation error"
    NOT_FOUND = "not found"


class KnowledgeKVPRecord(BaseModel):
    """
    Represents a knowledge KVP record in the KVP knowledge store.

    Attributes:
        key: Key as a JSON object
        value: Value as a JSON object
        created_at: Timestamp of record creation in epoch time (optional)
        updated_at: Timestamp of record last update in epoch time (optional)
    """

    model_config = ConfigDict(exclude_none=True)

    key: Dict[str, Any] = Field(..., description="Key as a JSON object")
    value: Dict[str, Any] = Field(..., description="Value as a JSON object")
    created_at: Optional[int] = Field(None, description="Timestamp of record creation in epoch time")
    updated_at: Optional[int] = Field(None, description="Timestamp of record last update in epoch time")


class KnowledgeKVPStoreOnboardRequest(BaseModel):
    """
    Represents a request to setup the KVP store for storing and managing knowledge key-value pair data.
    Creates essential entities for the KVP store to function and provide partitioning by workspace.

    Attributes:
        request_id: Auto-generated UUID for request tracking used if not passed in request
        scope: Type of scope (MAS or CE)
    """

    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Auto-generated UUID for request tracking used if not passed in request",
    )
    scope: ScopeType = Field(..., description="Type of scope (MAS or CE)")

class KnowledgeKVPStoreOnboardResponse(BaseModel):
    """
    Represents a response from the create KVP store request.

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


class KnowledgeKVPStoreOnboardDeleteRequest(BaseModel):
    """
    Represents a request to delete the KVP store used for storing and managing knowledge key-value pair data.

    Attributes:
        request_id: Auto-generated UUID for request tracking used if not passed in request
        scope: Type of scope (MAS or CE)
    """

    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Auto-generated UUID for request tracking used if not passed in request",
    )
    scope: ScopeType = Field(..., description="Type of scope (MAS or CE)")

class KnowledgeKVPStoreRequest(BaseModel):
    """
    Request to the Store for storing and managing knowledge KVP data.

    Attributes:
        request_id: Auto-generated UUID for request tracking used if not passed in request
        scope: Type of scope (MAS or CE)
        wksp_id: ID for the Multi-Agent System Workspace
        mas_id: ID for the Multi-Agent System (required for MAS scope)
        agent_id: ID for the specific Agent within the MAS (optional)
        ce_id: ID for the Cognition Engine (required for CE scope)
        records: List of KVP records
    """

    model_config = ConfigDict(exclude_none=True)

    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Auto-generated UUID for request tracking used if not passed in request",
    )
    scope: ScopeType = Field(..., description="Type of scope (MAS or CE)")
    wksp_id: Optional[str] = Field(
        None, min_length=1, description="ID for the Multi-Agent System Workspace (required for MAS scope)"
    )
    mas_id: Optional[str] = Field(
        None, min_length=1, description="ID for the Multi-Agent System (required for MAS scope)"
    )
    agent_id: Optional[str] = Field(
        None, min_length=1, description="ID for the specific Agent within the MAS (optional, required for MAS scope when storing Agent specific knowledge)"
    )
    ce_id: Optional[str] = Field(None, min_length=1, description="ID for the Cognition Engine (required for CE scope)")
    records: List[KnowledgeKVPRecord] = Field(default_factory=list, description="List of KVP records")

    @field_validator("wksp_id")
    @classmethod
    def validate_wksp_id_format(cls, v):
        if v is not None:
            return validate_uuid_format(v, "wksp_id")
        return v

    @field_validator("mas_id")
    @classmethod
    def validate_mas_id_format(cls, v):
        if v is not None:
            return validate_uuid_format(v, "mas_id")
        return v

    @field_validator("records")
    @classmethod
    def validate_records(cls, v):
        if not isinstance(v, list):
            raise ValueError("records must be a list")
        return v

    @model_validator(mode="after")
    def validate_scope_requirements_model(self):
        return validate_scope_requirements(self)


class KnowledgeKVPStoreResponse(BaseModel):
    """
    Response from the Store after storing and managing knowledge KVP data.

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


class KnowledgeKVPDeleteRequest(BaseModel):
    """
    Request to delete a KVP from the store.

    Attributes:
        request_id: Auto-generated UUID for request tracking used if not passed in request
        scope: Type of scope (MAS or CE)
        wksp_id: The workspace ID for the request
        mas_id: ID for the Multi-Agent System (required for MAS scope)
        agent_id: ID for the specific Agent within the MAS (optional)
        ce_id: ID for the Cognition Engine (required for CE scope)
        key: Key of KVP to delete (as JSON object)
        soft_delete: Soft delete the KVP
    """

    model_config = ConfigDict(exclude_none=True)

    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Auto-generated UUID for request tracking used if not passed in request",
    )
    scope: ScopeType = Field(..., description="Type of scope (MAS or CE)")
    wksp_id: Optional[str] = Field(
        None, min_length=1, description="The workspace ID for the request (required for MAS scope)"
    )
    mas_id: Optional[str] = Field(
        None, min_length=1, description="ID for the Multi-Agent System (required for MAS scope)"
    )
    agent_id: Optional[str] = Field(
        None, min_length=1, description="ID for the specific Agent within the MAS (optional)"
    )
    ce_id: Optional[str] = Field(None, min_length=1, description="ID for the Cognition Engine (required for CE scope)")
    key: Dict[str, Any] = Field(..., description="Key of KVP to delete (as JSON object)")
    soft_delete: bool = Field(True, description="Soft delete the KVP")

    @field_validator("wksp_id")
    @classmethod
    def validate_wksp_id_format(cls, v):
        if v is not None:
            return validate_uuid_format(v, "wksp_id")
        return v

    @field_validator("mas_id")
    @classmethod
    def validate_mas_id_format(cls, v):
        if v is not None:
            return validate_uuid_format(v, "mas_id")
        return v

    @model_validator(mode="after")
    def validate_scope_requirements_model(self):
        return validate_scope_requirements(self)


class KnowledgeKVPDeleteResponse(BaseModel):
    """
    Response from the Store after deleting knowledge KVP data.

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


class KnowledgeKVPQueryCriteria(BaseModel):
    """
    Query criteria for KVP search operations.

    Attributes:
        query_type: Type of query to execute
        key: Key to query for (required for get_by_key)
        limit: Limit used by queries
    """

    model_config = ConfigDict(exclude_none=True)

    query_type: str = Field("get_by_key", description="Type of query to execute")
    key: Optional[Dict[str, Any]] = Field(None, description="Key to query for (required for get_by_key)")
    limit: Optional[int] = Field(None, ge=1, description="Limit used by queries")

    @field_validator("query_type")
    @classmethod
    def validate_query_type(cls, v):
        allowed_types = ["get_by_key"]
        if v not in allowed_types:
            raise ValueError(f"query_type must be one of {allowed_types}")
        return v

    @field_validator("key")
    @classmethod
    def validate_key_for_query_type(cls, v, info):
        query_type = info.data.get("query_type")
        if query_type == "get_by_key" and v is None:
            raise ValueError("key is required for get_by_key query type")
        return v


class KnowledgeKVPQueryRequest(BaseModel):
    """
    Request to query the KVP store.

    Attributes:
        request_id: Auto-generated UUID for request tracking used if not passed in request
        scope: Type of scope (MAS or CE)
        wksp_id: ID for the Workspace
        mas_id: ID for the Multi-Agent System (required for MAS scope)
        agent_id: ID for the specific Agent within the MAS (optional)
        ce_id: ID for the Cognition Engine (required for CE scope)
        query_criteria: Query criteria for the search
    """

    model_config = ConfigDict(exclude_none=True)

    request_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Auto-generated UUID for request tracking used if not passed in request",
    )
    scope: ScopeType = Field(..., description="Type of scope (MAS or CE)")
    wksp_id: Optional[str] = Field(None, min_length=1, description="ID for the Workspace (required for MAS scope)")
    mas_id: Optional[str] = Field(
        None, min_length=1, description="ID for the Multi-Agent System (required for MAS scope)"
    )
    agent_id: Optional[str] = Field(
        None, min_length=1, description="ID for the specific Agent within the MAS (optional)"
    )
    ce_id: Optional[str] = Field(None, min_length=1, description="ID for the Cognition Engine (required for CE scope)")
    query_criteria: KnowledgeKVPQueryCriteria = Field(..., description="Query criteria for the search")

    @field_validator("wksp_id")
    @classmethod
    def validate_wksp_id_format(cls, v):
        if v is not None:
            return validate_uuid_format(v, "wksp_id")
        return v

    @field_validator("mas_id")
    @classmethod
    def validate_mas_id_format(cls, v):
        if v is not None:
            return validate_uuid_format(v, "mas_id")
        return v

    @model_validator(mode="after")
    def validate_scope_requirements_model(self):
        return validate_scope_requirements(self)


class KnowledgeKVPQueryResponse(BaseModel):
    """
    Response from the Store after querying knowledge KVP data.

    Attributes:
        request_id: UUID for request tracking
        status: Status of the request
        message: Optional message providing additional information
        records: Query response records (only included for success status)
    """

    model_config = ConfigDict(exclude_none=True)

    request_id: Optional[str] = Field(None, description="UUID for request tracking")
    status: ResponseStatus = Field(..., description="Status of the request")
    message: Optional[str] = Field(None, description="Optional message providing additional information")
    records: List[KnowledgeKVPRecord] = Field(
        default_factory=list, description="Query response records (only included for success status)"
    )

    def model_dump(self, **kwargs) -> Dict[str, Any]:
        """Override model_dump to ensure exclude_none is always applied."""
        kwargs.setdefault("exclude_none", True)
        return super().model_dump(**kwargs)


# Query type constants for easier usage
QUERY_TYPE_GET_BY_KEY = "get_by_key"
