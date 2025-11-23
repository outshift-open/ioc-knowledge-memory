from pydantic import BaseModel, Field, EmailStr, ConfigDict
from datetime import datetime


class UserCreate(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "John Doe",
                "email": "john.doe@company.com",
            }
        }
    )

    name: str = Field(..., description="Name of the user", min_length=1, max_length=100)
    email: EmailStr = Field(..., description="Email address of the user")


class UserResponse(BaseModel):
    model_config = ConfigDict(json_schema_extra={"example": {"id": "550e8400-e29b-41d4-a716-446655440001"}})

    id: str = Field(..., description="Unique identifier for the user")


class UserDetail(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "John Doe",
                "email": "john.doe@company.com",
                "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
                "workspace_name": "Development Team",
                "created_at": "2024-11-14T10:30:00Z",
            }
        }
    )

    id: str
    name: str
    email: str
    workspace_id: str
    workspace_name: str
    created_at: datetime
