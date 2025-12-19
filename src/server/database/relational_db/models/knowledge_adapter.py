from sqlalchemy import Column, String, DateTime, text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from server.database.relational_db.models import Base


class KnowledgeAdapter(Base):
    __tablename__ = "knowledge_adapters"

    id = Column(String(36), primary_key=True, server_default=text("gen_random_uuid()::text"))

    workspace_id = Column(String(36), ForeignKey("workspaces.id"), nullable=False)
    name = Column(String(255), nullable=False)
    mas_ids = Column(JSONB, nullable=False)
    type = Column(String(50), nullable=False)
    software_type = Column(String(90), nullable=False)

    software_config = Column(JSONB, nullable=True)

    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    updated_at = Column(
        DateTime, nullable=True, server_default=text("CURRENT_TIMESTAMP"), onupdate=text("CURRENT_TIMESTAMP")
    )

    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)

    deleted_at = Column(DateTime, nullable=True)

    __table_args__ = (
        Index("idx_kep_workspace_id", "workspace_id"),
        Index("idx_kep_software_type", "software_type"),
        Index("idx_kep_deleted_at", "deleted_at"),
    )

    def __repr__(self):
        return (
            f"<KnowledgeAdapter(id='{self.id}', name='{self.name}', "
            f"type='{self.type}', workspace_id='{self.workspace_id}')>"
        )
