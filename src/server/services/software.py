"""Software service - Business logic for software catalog operations"""

from typing import Optional

from fastapi import HTTPException, status

from server.schemas.software import SoftwareList
from server.database.relational_db.models.software import Software
from server.database.relational_db.db import RelationalDB
from server.services.audit import AuditEventType, ResourceType, audit_service, AuditRequest


class SoftwareService:
    """Service layer for software catalog/business logic"""

    def list_softwares(self, type: Optional[str] = None) -> SoftwareList:
        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                query = session.query(Software).filter(Software.deleted_at.is_(None))
                if type:
                    query = query.filter(Software.type == type)

                software_records = query.all()

                result = []
                for software in software_records:
                    result.append(
                        {
                            "id": software.id,
                            "type": software.type,
                            "config": software.config,
                            "created_at": software.created_at.isoformat() if software.created_at else None,
                            "updated_at": software.updated_at.isoformat() if software.updated_at else None,
                        }
                    )

                return SoftwareList(result)

            finally:
                session.close()

        except Exception as e:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Database error: {str(e)}")


# Global service instance
software_service = SoftwareService()
