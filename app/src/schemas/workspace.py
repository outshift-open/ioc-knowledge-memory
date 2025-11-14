from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class WorkspaceCreate(BaseModel):
    name: str = Field(..., description="Name of the workspace", min_length=1, max_length=100)


class WorkspaceResponse(BaseModel):
    id: str = Field(..., description="Unique identifier for the workspace")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000"
            }
        }


class WorkspaceUpdate(BaseModel):
    name: Optional[str] = Field(None, description="Updated name of the workspace", min_length=1, max_length=100)


class WorkspaceDetail(BaseModel):
    id: str
    name: str
    created_at: datetime
    users: List[str] = []
    api_keys: List[str] = []
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "name": "My Workspace",
                "created_at": "2024-11-14T10:30:00Z",
                "users": [],
                "api_keys": []
            }
        }


class WorkspaceList(BaseModel):
    workspaces: List[WorkspaceDetail]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "workspaces": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440000",
                        "name": "My Workspace",
                        "created_at": "2024-11-14T10:30:00Z",
                        "users": [],
                        "api_keys": []
                    }
                ],
                "total": 1
            }
        }