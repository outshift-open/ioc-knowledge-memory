from fastapi import APIRouter, HTTPException, status
from typing import Optional

from server.schemas.software import SoftwareList
from server.database.relational_db.models.software import Software
from server.database.relational_db.db import RelationalDB

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
    try:
        # Get database instance
        db = RelationalDB()

        # Get database session
        session = db.get_session()

        try:
            # Build query
            query = session.query(Software).filter(Software.deleted_at.is_(None))

            # Apply type filter if provided
            if type:
                query = query.filter(Software.type == type)

            # Execute query
            software_records = query.all()

            # Convert to list of dictionaries
            result = []
            for software in software_records:
                software_dict = {
                    "id": software.id,
                    "type": software.type,
                    "config": software.config,
                    "created_at": software.created_at.isoformat() if software.created_at else None,
                    "updated_at": software.updated_at.isoformat() if software.updated_at else None,
                }
                result.append(software_dict)

            return result

        finally:
            session.close()

    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")
