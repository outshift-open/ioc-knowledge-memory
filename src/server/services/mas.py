"""Multi-Agentic System (MAS) service - Business logic for MAS operations"""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from server.schemas.multi_agentic_system import (
    MultiAgenticSystemRequest,
    MultiAgenticSystemResponse,
    MultiAgenticSystem as MultiAgenticSystemSchema,
    MultiAgenticSystems,
)
from server.database.relational_db.models.mas import MultiAgenticSystem as MultiAgenticSystemModel
from server.database.relational_db.db import RelationalDB
from server.services.workspace import workspace_service


class MultiAgenticSystemService:
    """Service layer for MAS business logic"""

    def create_multi_agentic_system(
        self, workspace_id: str, mas_data: MultiAgenticSystemRequest
    ) -> MultiAgenticSystemResponse:
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
                new_mas = MultiAgenticSystemModel(
                    workspace_id=workspace_id,
                    name=mas_data.name,
                    description=mas_data.description,
                    agents=mas_data.agents,
                    config=mas_data.config,
                )

                session.add(new_mas)
                session.commit()
                session.refresh(new_mas)

                return MultiAgenticSystemResponse(
                    id=new_mas.id,
                    name=new_mas.name,
                )

            except IntegrityError as e:
                session.rollback()
                if "idx_mas_workspace_name_unique" in str(e):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Multi-agentic system with name '{mas_data.name}' already exists in this workspace",
                    )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Database integrity error: {str(e)}",
                )
            except Exception as e:
                session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create multi-agentic system: {str(e)}",
                )
            finally:
                session.close()

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create multi-agentic system: {str(e)}",
            )

    def list_multi_agentic_systems(self, workspace_id: str) -> MultiAgenticSystems:
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
                systems = (
                    session.query(MultiAgenticSystemModel)
                    .filter(
                        MultiAgenticSystemModel.workspace_id == workspace_id,
                        MultiAgenticSystemModel.deleted_at.is_(None),
                    )
                    .all()
                )

                system_responses = [
                    MultiAgenticSystemSchema(
                        id=system.id,
                        workspace_id=system.workspace_id,
                        name=system.name,
                        description=system.description,
                        agents=system.agents,
                        config=system.config,
                        created_at=system.created_at,
                        updated_at=system.updated_at,
                    )
                    for system in systems
                ]

                return MultiAgenticSystems(systems=system_responses)

            finally:
                session.close()

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve multi-agentic systems: {str(e)}",
            )

    def get_multi_agentic_system(self, workspace_id: str, mas_id: str) -> MultiAgenticSystemSchema:
        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                mas = (
                    session.query(MultiAgenticSystemModel)
                    .filter(
                        MultiAgenticSystemModel.id == mas_id,
                        MultiAgenticSystemModel.workspace_id == workspace_id,
                        MultiAgenticSystemModel.deleted_at.is_(None),
                    )
                    .first()
                )

                if not mas:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Multi-agentic system not found",
                    )

                return MultiAgenticSystemSchema(
                    id=mas.id,
                    workspace_id=mas.workspace_id,
                    name=mas.name,
                    description=mas.description,
                    agents=mas.agents,
                    config=mas.config,
                    created_at=mas.created_at,
                    updated_at=mas.updated_at,
                    created_by=mas.created_by,
                    updated_by=mas.updated_by,
                )

            finally:
                session.close()

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve multi-agentic system: {str(e)}",
            )

    def delete_multi_agentic_system(self, workspace_id: str, mas_id: str, _purge: bool = False) -> dict:
        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                # Find the MAS
                mas = (
                    session.query(MultiAgenticSystemModel)
                    .filter(
                        MultiAgenticSystemModel.id == mas_id,
                        MultiAgenticSystemModel.workspace_id == workspace_id,
                        MultiAgenticSystemModel.deleted_at.is_(None),
                    )
                    .first()
                )

                if not mas:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Multi-agentic system not found",
                    )

                if _purge:
                    session.delete(mas)
                    message = "Multi-agentic system permanently deleted"
                else:
                    mas.deleted_at = datetime.now(timezone.utc)
                    message = "Multi-agentic system deleted successfully"

                session.commit()

                return {"message": message}

            finally:
                session.close()

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete multi-agentic system: {str(e)}",
            )


# Global service instance
mas_service = MultiAgenticSystemService()
