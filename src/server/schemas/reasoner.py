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


class QueryRequest(BaseModel):
    """Schema for storing reasoner query response"""

    model_config = ConfigDict(extra="allow")

    reasoner_cognition_response_id: Optional[str] = Field(
        None,
        description="ID of the reasoner cognition response",
    )
    status: Optional[str] = Field(
        None,
        description="Status of the query execution",
    )
    reasoner_cognition_request_id: Optional[str] = Field(
        None,
        description="ID of the reasoner cognition request",
    )
    query_input: Optional[str] = Field(
        None,
        description="The input query string",
    )
    records: Optional[List[Dict[str, Any]]] = Field(
        None,
        description="Records from the query response",
    )
    meta: Optional[Dict[str, Any]] = Field(
        None,
        description="Metadata about the query",
    )


class QueryResponse(BaseModel):
    """Schema for query storage response"""

    id: str = Field(..., description="Unique identifier for the stored query")
    reasoner_id: str = Field(..., description="ID of the reasoner")
    workspace_id: str = Field(..., description="ID of the workspace")
    created_at: datetime = Field(..., description="Timestamp when query was stored")


class QueryHistoryItem(BaseModel):
    """Schema for a single query history item"""

    id: str = Field(..., description="Unique identifier for the stored query")
    reasoner_id: str = Field(..., description="ID of the reasoner")
    workspace_id: str = Field(..., description="ID of the workspace")
    request_id: Optional[str] = Field(None, description="Request ID")
    response_id: Optional[str] = Field(None, description="Response ID")
    response_data: Dict[str, Any] = Field(..., description="Complete response data")
    created_at: datetime = Field(..., description="Timestamp when query was stored")


class QueryHistory(BaseModel):
    """Schema for query history list"""

    records: List[QueryHistoryItem] = Field(..., description="List of query history records")
    total: int = Field(..., description="Total number of records")


class QueryEvent(BaseModel):
    """Schema for a query event"""

    id: str = Field(..., description="Unique identifier for the query event")
    reasoner_id: str = Field(..., description="ID of the reasoner")
    workspace_id: str = Field(..., description="ID of the workspace")
    request_id: Optional[str] = Field(None, description="Request ID")
    response_id: Optional[str] = Field(None, description="Response ID")
    created_at: datetime = Field(..., description="Timestamp when query was stored")
    created_by: Optional[str] = Field(None, description="User who created the query")
    query_input: Optional[str] = Field(None, description="The input query string")


class QueryEvents(BaseModel):
    """Schema for list of query events"""

    records: List[QueryEvent] = Field(..., description="List of query events")
    total: int = Field(..., description="Total number of records")


class QueryEventFilter(BaseModel):
    """Schema for filtering query events"""

    reasoner_id: Optional[str] = Field(
        None,
        description="Filter by reasoner ID",
    )
    request_id: Optional[str] = Field(
        None,
        description="Filter by request ID",
    )
    response_id: Optional[str] = Field(
        None,
        description="Filter by response ID",
    )
    created_by: Optional[str] = Field(
        None,
        description="Filter by user who created the query",
    )
    start_date: Optional[datetime] = Field(
        None,
        description="Filter queries created on or after this date (ISO 8601 format)",
    )
    end_date: Optional[datetime] = Field(
        None,
        description="Filter queries created on or before this date (ISO 8601 format)",
    )
    limit: Optional[int] = Field(
        100,
        ge=1,
        le=1000,
        description="Maximum number of records to return (default: 100, max: 1000)",
    )
    offset: Optional[int] = Field(
        0,
        ge=0,
        description="Number of records to skip (default: 0)",
    )
