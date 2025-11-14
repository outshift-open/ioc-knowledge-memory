from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional


class UserCreate(BaseModel):
    name: str = Field(..., description="Name of the user", min_length=1, max_length=100)
    email: EmailStr = Field(..., description="Email address of the user")

    class Config:
        json_schema_extra = {
            "example": {
                "name": "John Doe",
                "email": "john.doe@company.com"
            }
        }


class UserResponse(BaseModel):
    id: str = Field(..., description="Unique identifier for the user")

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001"
            }
        }


class UserDetail(BaseModel):
    id: str
    name: str
    email: str
    workspace_id: str
    workspace_name: str
    created_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "John Doe",
                "email": "john.doe@company.com", 
                "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
                "workspace_name": "Development Team",
                "created_at": "2024-11-14T10:30:00Z"
            }
        }