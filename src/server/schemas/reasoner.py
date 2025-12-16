from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional, Dict, Any, List


class ReasonerRequest(BaseModel):
    """Schema for creating a new Reasoner"""

    name: str = Field(
        ...,
        description="Friendly name for the reasoner",
        min_length=1,
        max_length=255,
    )
    mas_id: str = Field(
        ...,
        description="UUID of the multi-agentic system this reasoner belongs to",
    )
    config: Optional[Dict[str, Any]] = Field(
        None,
        description="Configuration object",
    )


class ReasonerResponse(BaseModel):
    """Schema for reasoner creation response"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "friendly-name for a Reasoner",
            }
        }
    )

    id: str = Field(..., description="Unique identifier for the reasoner")
    name: str = Field(..., description="Name of the reasoner")


class Reasoner(BaseModel):
    """Schema for detailed reasoner information"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "workspace_id": "660e8400-e29b-41d4-a716-446655440000",
                "mas_id": "770e8400-e29b-41d4-a716-446655440000",
                "name": "friendly-name for a Reasoner",
                "config": {"reasoning_engine": "gpt-4", "max_iterations": 10},
                "created_at": "2024-12-11T10:30:00Z",
                "updated_at": "2024-12-11T10:30:00Z",
            }
        }
    )

    id: str
    workspace_id: str
    mas_id: str
    name: str
    config: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None
    updated_by: Optional[str] = None


class Reasoners(BaseModel):
    """Schema for listing reasoners"""

    reasoners: List[Reasoner] = Field(..., description="List of reasoners in the workspace")
