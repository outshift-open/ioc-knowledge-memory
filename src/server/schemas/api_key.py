from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import List


class ApiKeyResponse(BaseModel):
    """Response schema for API key creation - returns just the key string"""

    model_config = ConfigDict(
        json_schema_extra={"example": {"key": "tkf_1234567890abcdef1234567890abcdef"}}  # legit:ignore-secrets
    )

    key: str


class ApiKeyDetail(BaseModel):
    """Response schema for API key metadata (no actual key value)"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "key_preview": "tkf_1234...cdef",
                "created_at": "2024-11-14T10:30:00Z",
            }
        }
    )

    id: str
    key_preview: str
    created_at: datetime


class ApiKeyListResponse(BaseModel):
    """Response schema for listing API keys"""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "api_keys": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "key_preview": "tkf_1234...cdef",
                        "created_at": "2024-11-14T10:30:00Z",
                    }
                ],
                "total": 1,
            }
        }
    )

    api_keys: List[ApiKeyDetail]
    total: int
