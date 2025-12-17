import logging
from typing import Optional, Dict, Any
from pydantic import Field
from server.database.relational_db.models.audit import Audit
from server.database.relational_db.db import RelationalDB
from enum import Enum
from pydantic import BaseModel


class ResourceType(str, Enum):
    """Enum for different resource types in the system."""

    MAS_TKF = "MAS_TKF"
    WKSP_TKF = "WKSP_TKF"
    # Add other resource types as needed


class AuditEventType(str, Enum):
    """Enum for different audit event types."""

    CREATE_TKF = "CREATE_TKF"
    DELETE_TKF = "DELETE_TKF"
    # Add other audit event types as needed


class AuditRequest(BaseModel):
    request_id: Optional[str] = Field(None, description="Unique request ID")
    resource_type: ResourceType = Field(..., description="Type of the resource being audited")
    audit_type: AuditEventType = Field(..., description="Type of audit action")
    audit_resource_id: Optional[str] = Field(None, description="ID of the resource being audited")
    created_by: Optional[str] = Field(None, description="user who created the audit")
    updated_by: Optional[str] = Field(None, description="user who last updated the audit")
    deleted_by: Optional[str] = Field(None, description="user who deleted the audit")
    audit_information: Optional[Dict[str, Any]] = Field(
        None, description="Information about the audit as a JSON object"
    )
    audit_extra_information: Optional[str] = Field(None, description="Information about the audit as a string")


class AuditService:
    def __init__(self):
        # Get logger instance (logging is setup in main.py)
        self.logger = logging.getLogger(__name__)

    def create_audit(self, audit: AuditRequest) -> Audit:
        """Create a new audit entry.

        Args:
            audit: AuditRequest object containing audit details

        Returns:
            Audit: The created audit record
        """
        db = RelationalDB()
        session = db.get_session()
        self.logger.debug(f"Creating audit entry: {audit}")
        try:
            audit_entry = Audit(
                request_id=audit.request_id,
                resource_type=audit.resource_type,
                audit_type=audit.audit_type,
                audit_resource_id=audit.audit_resource_id,
                audit_information=audit.audit_information if audit.audit_information else None,
                audit_extra_information=audit.audit_extra_information,
                created_by=audit.created_by,
                updated_by=audit.updated_by,
                deleted_by=audit.deleted_by,
            )
            session.add(audit_entry)
            session.commit()
            self.logger.debug(f"Successfully created audit entry: {audit_entry}")
            return audit_entry
        except Exception as e:
            self.logger.error(f"Failed to create audit entry: {str(e)}")
            session.rollback()
            raise e
        finally:
            session.close()


# Global service instance
audit_service = AuditService()
