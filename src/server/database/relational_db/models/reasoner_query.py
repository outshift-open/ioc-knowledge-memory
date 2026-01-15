from sqlalchemy import Column, String, DateTime, text, Index, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB

from server.database.relational_db.models import Base


class ReasonerHistory(Base):
    __tablename__ = "reasoner_history"

    id = Column(String(36), primary_key=True, server_default=text("gen_random_uuid()::text"))

    workspace_id = Column(String(36), ForeignKey("workspace.id"), nullable=False)
    reasoner_id = Column(String(36), ForeignKey("reasoner.id"), nullable=False)

    # Query metadata
    request_id = Column(String(255), nullable=True)
    response_id = Column(String(255), nullable=True)
    query_input = Column(String(2000), nullable=True)

    # Query response data (the JSON response from the reasoner)
    response_data = Column(JSONB, nullable=False)

    created_at = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    created_by = Column(String(255), nullable=True)

    __table_args__ = (
        Index("idx_reasoner_history_workspace_id", "workspace_id"),
        Index("idx_reasoner_history_reasoner_id", "reasoner_id"),
        Index("idx_reasoner_history_created_at", "created_at"),
    )

    def __repr__(self):
        return (
            f"<ReasonerHistory(id='{self.id}', reasoner_id='{self.reasoner_id}', "
            f"workspace_id='{self.workspace_id}', response_id='{self.response_id}')>"
        )
