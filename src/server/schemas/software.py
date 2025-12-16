from pydantic import BaseModel, Field, RootModel
from typing import List, Dict, Any

# This will be a list of dictionaries (JSON objects)
SoftwareList = RootModel[List[Dict[str, Any]]]


class KnowledgeAdapterTemplatesResponse(BaseModel):
    """Response model for knowledge adapter templates"""

    softwares: List[Dict[str, Any]] = Field(
        ..., description="List of software templates where template name is the key"
    )
