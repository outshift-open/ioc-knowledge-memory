"""Knowledge Adapter service - Business logic for KEP operations"""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from server.schemas.knowledge_adapter import (
    KnowledgeAdapterRequest,
    KnowledgeAdapterResponse,
    KnowledgeAdapter as KnowledgeAdapterSchema,
    KnowledgeAdapters,
)
from server.database.relational_db.models.knowledge_adapter import KnowledgeAdapter as KnowledgeAdapterModel
from server.database.relational_db.models.mas import MultiAgenticSystem
from server.database.relational_db.models.software import Software
from server.database.relational_db.db import RelationalDB
from server.services.workspace import workspace_service


class KnowledgeAdapterService:
    """Service layer for knowledge adapter business logic"""

    def create_knowledge_adapter(
        self, workspace_id: str, kep_data: KnowledgeAdapterRequest
    ) -> KnowledgeAdapterResponse:
        # Validate workspace exists
        if not workspace_service.workspace_exists(workspace_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found",
            )

        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                # Verify all MAS exist in the workspace - collect all invalid IDs
                invalid_mas_ids = []
                for mas_id in kep_data.mas_ids:
                    mas = (
                        session.query(MultiAgenticSystem)
                        .filter(
                            MultiAgenticSystem.id == mas_id,
                            MultiAgenticSystem.workspace_id == workspace_id,
                            MultiAgenticSystem.deleted_at.is_(None),
                        )
                        .first()
                    )

                    if not mas:
                        invalid_mas_ids.append(mas_id)

                if invalid_mas_ids:
                    if len(invalid_mas_ids) == 1:
                        detail = f"Multi-agentic system with id '{invalid_mas_ids[0]}' not found in this workspace"
                    else:
                        detail = f"Multi-agentic systems with ids {invalid_mas_ids} not found in this workspace"
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=detail,
                    )

                # Verify software type exists
                software = (
                    session.query(Software)
                    .filter(
                        Software.type == "KnowledgeAdapterTemplates",
                        Software.config.op("->")(kep_data.software_type).isnot(None),
                        Software.deleted_at.is_(None),
                    )
                    .first()
                )

                if not software:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Software template '{kep_data.software_type}' not found",
                    )

                # Create new knowledge adapter
                new_kep = KnowledgeAdapterModel(
                    workspace_id=workspace_id,
                    name=kep_data.name,
                    mas_ids=kep_data.mas_ids,
                    type=kep_data.type.value,
                    software_type=kep_data.software_type,
                    software_config=kep_data.software_config,
                )

                session.add(new_kep)
                session.commit()
                session.refresh(new_kep)

                return KnowledgeAdapterResponse(
                    id=new_kep.id,
                    name=new_kep.name,
                )

            except HTTPException:
                session.rollback()
                raise
            except IntegrityError as e:
                session.rollback()
                if "idx_kep_workspace_name_unique" in str(e):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Knowledge adapter with name '{kep_data.name}' already exists in this workspace",
                    )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Database integrity error: {str(e)}",
                )
            except Exception as e:
                session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create knowledge adapter: {str(e)}",
                )
            finally:
                session.close()

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create knowledge adapter: {str(e)}",
            )

    def list_knowledge_adapters(self, workspace_id: str) -> KnowledgeAdapters:
        # Validate workspace exists
        if not workspace_service.workspace_exists(workspace_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found",
            )

        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                keps = (
                    session.query(KnowledgeAdapterModel)
                    .filter(
                        KnowledgeAdapterModel.workspace_id == workspace_id,
                        KnowledgeAdapterModel.deleted_at.is_(None),
                    )
                    .all()
                )

                kep_responses = [
                    KnowledgeAdapterSchema(
                        id=kep.id,
                        workspace_id=kep.workspace_id,
                        mas_ids=kep.mas_ids,
                        name=kep.name,
                        type=kep.type,
                        software_type=kep.software_type,
                        software_config=kep.software_config,
                        created_at=kep.created_at,
                        updated_at=kep.updated_at,
                    )
                    for kep in keps
                ]

                return KnowledgeAdapters(knowledge_adapters=kep_responses)

            finally:
                session.close()

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve knowledge adapters: {str(e)}",
            )

    def get_knowledge_adapter(self, workspace_id: str, kep_id: str) -> KnowledgeAdapterSchema:
        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                kep = (
                    session.query(KnowledgeAdapterModel)
                    .filter(
                        KnowledgeAdapterModel.id == kep_id,
                        KnowledgeAdapterModel.workspace_id == workspace_id,
                        KnowledgeAdapterModel.deleted_at.is_(None),
                    )
                    .first()
                )

                if not kep:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Knowledge adapter not found",
                    )

                return KnowledgeAdapterSchema(
                    id=kep.id,
                    workspace_id=kep.workspace_id,
                    name=kep.name,
                    mas_ids=kep.mas_ids,
                    type=kep.type,
                    software_type=kep.software_type,
                    software_config=kep.software_config,
                    created_at=kep.created_at,
                    updated_at=kep.updated_at,
                    created_by=kep.created_by,
                    updated_by=kep.updated_by,
                )

            finally:
                session.close()

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve knowledge adapter: {str(e)}",
            )

    def delete_knowledge_adapter(self, workspace_id: str, kep_id: str, _purge: bool = False) -> dict:
        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                # Find the knowledge adapter
                kep = (
                    session.query(KnowledgeAdapterModel)
                    .filter(
                        KnowledgeAdapterModel.id == kep_id,
                        KnowledgeAdapterModel.workspace_id == workspace_id,
                        KnowledgeAdapterModel.deleted_at.is_(None),
                    )
                    .first()
                )

                if not kep:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Knowledge adapter not found",
                    )

                if _purge:
                    # Hard delete - actually remove from database
                    session.delete(kep)
                    message = "Knowledge adapter permanently deleted"
                else:
                    # Soft delete by setting deleted_at timestamp
                    kep.deleted_at = datetime.now(timezone.utc)
                    message = "Knowledge adapter deleted successfully"

                session.commit()

                return {"message": message}

            finally:
                session.close()

        except HTTPException:
            # Re-raise HTTPExceptions (like 404 not found)
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete knowledge adapter: {str(e)}",
            )


# Global service instance
knowledge_adapter_service = KnowledgeAdapterService()
