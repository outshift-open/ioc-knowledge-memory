from pydantic import BaseModel
from datetime import datetime
from typing import List


class ApiKeyResponse(BaseModel):
    """Response schema for API key creation - returns just the key string"""
    key: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "key": "tkf_1234567890abcdef1234567890abcdef"
            }
        }


class ApiKeyDetail(BaseModel):
    """Response schema for API key metadata (no actual key value)"""
    id: str
    key_preview: str
    created_at: datetime
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "key_preview": "tkf_1234...cdef",
                "created_at": "2024-11-14T10:30:00Z"
            }
        }


class ApiKeyListResponse(BaseModel):
    """Response schema for listing API keys"""
    api_keys: List[ApiKeyDetail]
    total: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "api_keys": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "key_preview": "tkf_1234...cdef", 
                        "created_at": "2024-11-14T10:30:00Z"
                    }
                ],
                "total": 1
            }
        }