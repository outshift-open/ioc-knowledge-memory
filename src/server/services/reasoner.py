"""Reasoner service - Business logic for reasoner operations"""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from server.schemas.reasoner import (
    ReasonerRequest,
    ReasonerResponse,
    Reasoner as ReasonerSchema,
    Reasoners,
)
from server.database.relational_db.models.reasoner import Reasoner as ReasonerModel
from server.database.relational_db.models.mas import MultiAgenticSystem
from server.database.relational_db.db import RelationalDB
from server.services.workspace import workspace_service


class ReasonerService:
    """Service layer for reasoner business logic"""

    def create_reasoner(self, workspace_id: str, reasoner_data: ReasonerRequest) -> ReasonerResponse:
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
                # Verify MAS exists in the workspace
                mas = (
                    session.query(MultiAgenticSystem)
                    .filter(
                        MultiAgenticSystem.id == reasoner_data.mas_id,
                        MultiAgenticSystem.workspace_id == workspace_id,
                        MultiAgenticSystem.deleted_at.is_(None),
                    )
                    .first()
                )

                if not mas:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Multi-agentic system with id '{reasoner_data.mas_id}' not found in this workspace",
                    )

                # Create new reasoner
                new_reasoner = ReasonerModel(
                    workspace_id=workspace_id,
                    mas_id=reasoner_data.mas_id,
                    name=reasoner_data.name,
                    config=reasoner_data.config,
                )

                session.add(new_reasoner)
                session.commit()
                session.refresh(new_reasoner)

                return ReasonerResponse(
                    id=new_reasoner.id,
                    name=new_reasoner.name,
                )

            except HTTPException:
                session.rollback()
                raise
            except IntegrityError as e:
                session.rollback()
                if "idx_reasoners_workspace_name_unique" in str(e):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Reasoner with name '{reasoner_data.name}' already exists in this workspace",
                    )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Database integrity error: {str(e)}",
                )
            except Exception as e:
                session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create reasoner: {str(e)}",
                )
            finally:
                session.close()

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create reasoner: {str(e)}",
            )

    def list_reasoners(self, workspace_id: str) -> Reasoners:
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
                reasoners = (
                    session.query(ReasonerModel)
                    .filter(
                        ReasonerModel.workspace_id == workspace_id,
                        ReasonerModel.deleted_at.is_(None),
                    )
                    .all()
                )

                reasoner_responses = [
                    ReasonerSchema(
                        id=reasoner.id,
                        workspace_id=reasoner.workspace_id,
                        mas_id=reasoner.mas_id,
                        name=reasoner.name,
                        config=reasoner.config,
                        created_at=reasoner.created_at,
                        updated_at=reasoner.updated_at,
                    )
                    for reasoner in reasoners
                ]

                return Reasoners(reasoners=reasoner_responses)

            finally:
                session.close()

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve reasoners: {str(e)}",
            )

    def get_reasoner(self, workspace_id: str, reasoner_id: str) -> ReasonerSchema:
        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                reasoner = (
                    session.query(ReasonerModel)
                    .filter(
                        ReasonerModel.id == reasoner_id,
                        ReasonerModel.workspace_id == workspace_id,
                        ReasonerModel.deleted_at.is_(None),
                    )
                    .first()
                )

                if not reasoner:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Reasoner not found",
                    )

                return ReasonerSchema(
                    id=reasoner.id,
                    workspace_id=reasoner.workspace_id,
                    mas_id=reasoner.mas_id,
                    name=reasoner.name,
                    config=reasoner.config,
                    created_at=reasoner.created_at,
                    updated_at=reasoner.updated_at,
                    created_by=reasoner.created_by,
                    updated_by=reasoner.updated_by,
                )

            finally:
                session.close()

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve reasoner: {str(e)}",
            )

    def delete_reasoner(self, workspace_id: str, reasoner_id: str, _purge: bool = False) -> dict:
        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                reasoner = (
                    session.query(ReasonerModel)
                    .filter(
                        ReasonerModel.id == reasoner_id,
                        ReasonerModel.workspace_id == workspace_id,
                        ReasonerModel.deleted_at.is_(None),
                    )
                    .first()
                )

                if not reasoner:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Reasoner not found",
                    )

                if _purge:
                    session.delete(reasoner)
                    message = "Reasoner permanently deleted"
                else:
                    reasoner.deleted_at = datetime.now(timezone.utc)
                    message = "Reasoner deleted successfully"

                session.commit()

                return {"message": message}

            finally:
                session.close()

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete reasoner: {str(e)}",
            )


# Global service instance
reasoner_service = ReasonerService()
