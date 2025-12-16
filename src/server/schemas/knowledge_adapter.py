from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class AdapterType(str, Enum):
    """Type of knowledge adapter data flow"""

    push = "push"
    pull = "pull"
    both = "both"


class KnowledgeAdapterRequest(BaseModel):
    """Schema for creating a new Knowledge Adapter (KEP)"""

    name: str = Field(
        ...,
        description="Friendly name for the knowledge adapter instance",
        min_length=1,
        max_length=255,
    )
    mas_ids: List[str] = Field(
        ...,
        description="List of MAS UUIDs this adapter serves",
        min_length=1,
    )
    type: AdapterType = Field(
        ...,
        description="Data flow type: push (adapter sends data), pull (adapter is queried), or both",
    )
    software_type: str = Field(
        ...,
        description="Software type from software table (e.g., 'otel', 'info-extraction')",
        min_length=1,
        max_length=90,
    )
    software_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Configuration object",
    )


class KnowledgeAdapterResponse(BaseModel):
    """Schema for knowledge adapter creation response"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "friendly-name for a KEP instance",
            }
        }
    )

    id: str = Field(..., description="Unique identifier for the knowledge adapter")
    name: str = Field(..., description="Name of the knowledge adapter")


class KnowledgeAdapter(BaseModel):
    """Schema for detailed knowledge adapter information"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "workspace_id": "660e8400-e29b-41d4-a716-446655440000",
                "name": "friendly-name for a KEP instance",
                "mas_ids": ["770e8400-e29b-41d4-a716-446655440000"],
                "type": "push",
                "software_type": "otel",
                "software_config": {"endpoint": "http://otel-collector:4317"},
                "created_at": "2024-12-11T10:30:00Z",
                "updated_at": "2024-12-11T10:30:00Z",
            }
        }
    )

    id: str
    workspace_id: str
    name: str
    mas_ids: List[str]
    type: AdapterType
    software_type: str
    software_config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class KnowledgeAdapters(BaseModel):
    """Schema for listing knowledge adapters"""

    knowledge_adapters: List[KnowledgeAdapter] = Field(..., description="List of knowledge adapters in the workspace")
