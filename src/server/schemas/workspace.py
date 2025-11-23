from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import List, Optional


class WorkspaceCreate(BaseModel):
    name: str = Field(
        ...,
        description="Name of the workspace",
        min_length=1,
        max_length=100,
    )


class WorkspaceResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"id": "550e8400-e29b-41d4-a716-446655440000"}})

    id: str = Field(..., description="Unique identifier for the workspace")


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(
        None,
        description="Updated name of the workspace",
        min_length=1,
        max_length=100,
    )


class WorkspaceDetail(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "My Workspace",
                "created_at": "2024-11-14T10:30:00Z",
                "users": [],
                "api_keys": [],
            }
        }
    )

    id: str
    name: str
    created_at: datetime
    users: List[str] = []
    api_keys: List[str] = []


class WorkspaceList(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "workspaces": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "My Workspace",
                        "created_at": "2024-11-14T10:30:00Z",
                        "users": [],
                        "api_keys": [],
                    }
                ],
                "total": 1,
            }
        }
    )

    workspaces: List[WorkspaceDetail]
    total: int
