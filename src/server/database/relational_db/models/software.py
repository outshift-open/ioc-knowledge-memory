from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, String, DateTime, JSON, text, Index
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

Base = declarative_base()


class Software(Base):
    __tablename__ = "software"

    # Primary key - UUID as string, auto-generated in database
    id = Column(
        String(36),
        primary_key=True,
        server_default=text("gen_random_uuid()::text")
    )

    # Required fields
    type = Column(String(90), nullable=False)
    config = Column(JSON, nullable=True)

    # Timestamp fields - auto-generated in database
    created_at = Column(
        DateTime,
        nullable=False,
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at = Column(
        DateTime,
        nullable=True,
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP")
    )

    # Soft delete field
    deleted_at = Column(DateTime, nullable=True)

    # Indexes
    __table_args__ = (
        Index('idx_software_type', 'type'),
        Index('idx_software_deleted_at', 'deleted_at'),
    )

    def __repr__(self):
        return f"<Software(id='{self.id}', name='{self.name}', type='{self.type}')>"
