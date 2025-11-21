from pydantic import BaseModel, Field, ConfigDict, field_validator
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class SoftwareType(str, Enum):
  REASONER = "Reasoner"
  KEP_ADAPTER = "KEP Adapter"

class SoftwareConfig(BaseModel):
    """Base model for software configuration"""
    reasoning_engine: Optional[str] = None
    endpoint_url: Optional[str] = None
    timeout: Optional[int] = None
    max_retries: Optional[int] = None


class SoftwareCreate(BaseModel):
  name: str = Field(..., description="Name of the software", min_length=1)
  type: str = Field(..., description="Type of the software (Reasoner or KEP Adapter)")
  config: Optional[SoftwareConfig] = Field(
    default=None, description="Software-specific configuration"
  )

  @field_validator('type')
  @classmethod
  def validate_type(cls, v):
      if v not in [SoftwareType.REASONER.value, SoftwareType.KEP_ADAPTER.value]:
          raise ValueError(f'type must be either "{SoftwareType.REASONER.value}" or "{SoftwareType.KEP_ADAPTER.value}"')
      return v


class SoftwareResponse(BaseModel):
  """Model for software response"""

  id: str = Field(description="Software UUID")
  name: str = Field(description="Software name")
  type: str = Field(description="Software type")
  config: Optional[Dict[str, Any]] = Field(description="Software configuration")
  workspace_id: str = Field(description="Workspace UUID")
  api_key_id: Optional[str] = Field(
    default=None, description="Associated API key UUID"
  )
  created_at: datetime = Field(description="Creation timestamp")
  
  model_config = ConfigDict(
    json_schema_extra={
      "example": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "My Software",
        "type": "Reasoner",
        "config": {
          "reasoning_engine": "Reasoner",
          "endpoint_url": "http://localhost:8000",
          "timeout": 30,
          "max_retries": 3
        },
        "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
        "api_key_id": "550e8400-e29b-41d4-a716-446655440000", # legit:ignore
        "created_at": "2024-11-14T10:30:00Z"
      }
    }
  )

class SoftwareUpdate(BaseModel):
  name: Optional[str] = Field(None, description="Updated name of the software", min_length=1)

class SoftwareDetail(BaseModel):
  id: str = Field(description="Software UUID")
  type: str = Field(description="Software type")
  name: str = Field(description="Software name")
  config: Optional[SoftwareConfig] = Field(default=None, description="Software configuration")
  workspace_id: str = Field(description="Workspace UUID")
  created_at: datetime = Field(description="Creation timestamp")
  
  model_config = ConfigDict(
    json_schema_extra={
      "example": {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "type": "reasoner",
        "name": "My Software",
        "config": {
          "reasoning_engine": "Reasoner",
          "endpoint_url": "http://localhost:8000",
          "timeout": 30,
          "max_retries": 3
        },
        "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
        "created_at": "2024-11-14T10:30:00Z"
      }
    }
  )

class SoftwareList(BaseModel):
  softwares: List[SoftwareDetail] = Field(description="List of software items")
  
  model_config = ConfigDict(
    json_schema_extra={
      "example": {
        "softwares": [
          {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "type": "reasoner",
            "name": "My Software",
            "config": {
              "reasoning_engine": "Reasoner",
              "endpoint_url": "http://localhost:8000",
              "timeout": 30,
              "max_retries": 3
            },
            "workspace_id": "550e8400-e29b-41d4-a716-446655440000",
            "created_at": "2024-11-14T10:30:00Z"
          }
        ],
        "total": 1
      }
    }
  )