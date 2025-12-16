from fastapi import APIRouter
from typing import Optional

from server.schemas.software import SoftwareList
from server.services import software_service

router = APIRouter()


@router.get("/", response_model=SoftwareList)
def list_softwares(type: Optional[str] = None):
    """
    List all softwares, optionally filtered by type

    Args:
        type: Optional software type to filter by

    Returns:
        List of software items, filtered by type if specified
    """
    return software_service.list_softwares(type)
