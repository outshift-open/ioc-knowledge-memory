from sqlalchemy import Column, String, DateTime, text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from server.database.relational_db.models import Base


class Reasoner(Base):
    __tablename__ = "reasoners"

    id = Column(String(36), primary_key=True, server_default=text("gen_random_uuid()::text"))

    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    mas_id = Column(String(36), ForeignKey("multi_agentic_systems.id"), nullable=False)
    name = Column(String(255), nullable=False)

    config = Column(JSONB, nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(
        DateTime, nullable=True, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP")
    )

    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)

    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_reasoners_workspace_id", "workspace_id"),
        Index("idx_reasoners_mas_id", "mas_id"),
        Index("idx_reasoners_deleted_at", "deleted_at"),
    )

    def __repr__(self):
        return (
            f"<Reasoner(id='{self.id}', name='{self.name}', "
            f"workspace_id='{self.workspace_id}', mas_id='{self.mas_id}')>"
        )
