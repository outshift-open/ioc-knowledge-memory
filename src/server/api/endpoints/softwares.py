from fastapi import APIRouter, HTTPException, status
from datetime import datetime

from server.schemas.software import (
    SoftwareCreate,
    SoftwareResponse,
    SoftwareDetail,
    SoftwareUpdate,
    SoftwareList,
    SoftwareConfig,
)
from server.models.software import Software

router = APIRouter()

@router.get("/", response_model=SoftwareList)
def list_softwares(type: str = None):
  """
  List all softwares, optionally filtered by type

  Args:
      type: Optional software type to filter by

  Returns:
      List of software items, filtered by type if specified
  """
  #return software_service.list_softwares(type=type)