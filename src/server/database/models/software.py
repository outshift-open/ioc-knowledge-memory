from sqlalchemy.orm import Mapped, mapped_column, DeclarativeBase
from sqlalchemy import String, DateTime, JSON, text
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class Base(DeclarativeBase):
    pass


class Software(Base):
    __tablename__ = "software"
    
    # Primary key - UUID as string, auto-generated in database
    id: Mapped[str] = mapped_column(
        String(36), 
        primary_key=True, 
        server_default=text("gen_random_uuid()::text")
    )
    
    # Required fields
    type: Mapped[str] = mapped_column(String(60), nullable=False)
    name: Mapped[str] = mapped_column(String(60), nullable=False)
    workspace_id: Mapped[str] = mapped_column(String(36), nullable=False)
    api_key_id: Mapped[str] = mapped_column(String(36), nullable=False)

    # Optional config field as JSON
    config: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    
    # Timestamp fields - auto-generated in database
    created_at: Mapped[datetime] = mapped_column(
        DateTime, 
        nullable=False, 
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, 
        nullable=True, 
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=text("CURRENT_TIMESTAMP")
    )
    
    # Soft delete field
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Software(id='{self.id}', name='{self.name}', type='{self.type}')>"