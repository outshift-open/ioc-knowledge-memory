"""Workspace service - Business logic for workspace operations"""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_

from server.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceDetail,
    WorkspaceUpdate,
    WorkspaceList,
)
from server.database.relational_db.models.workspace import Workspace as WorkspaceModel
from server.database.relational_db.db import RelationalDB


class WorkspaceService:
    """Service layer for workspace business logic"""

    def create_workspace(self, workspace_data: WorkspaceCreate) -> WorkspaceResponse:
        """Create a new workspace"""
        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                new_workspace = WorkspaceModel(
                    name=workspace_data.name,
                    users=workspace_data.users or [],
                    config=workspace_data.config,
                )

                session.add(new_workspace)
                session.commit()
                session.refresh(new_workspace)

                return WorkspaceResponse(id=new_workspace.id)

            finally:
                session.close()

        except IntegrityError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Workspace creation failed due to data conflict: {str(e)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create workspace: {str(e)}",
            )

    def list_workspaces(self) -> WorkspaceList:
        """List all active workspaces"""
        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                workspaces = session.query(WorkspaceModel).filter(WorkspaceModel.deleted_at.is_(None)).all()

                workspace_details = [
                    WorkspaceDetail(
                        id=workspace.id,
                        name=workspace.name,
                        created_at=workspace.created_at,
                        users=workspace.users or [],
                        config=workspace.config,
                    )
                    for workspace in workspaces
                ]

                return WorkspaceList(workspaces=workspace_details, total=len(workspace_details))

            finally:
                session.close()

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list workspaces: {str(e)}",
            )

    def get_workspace(self, workspace_id: str) -> WorkspaceDetail:
        """Get a specific workspace by ID"""
        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                workspace = (
                    session.query(WorkspaceModel)
                    .filter(
                        and_(
                            WorkspaceModel.id == workspace_id,
                            WorkspaceModel.deleted_at.is_(None),
                        )
                    )
                    .first()
                )

                if not workspace:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Workspace not found",
                    )

                return WorkspaceDetail(
                    id=workspace.id,
                    name=workspace.name,
                    created_at=workspace.created_at,
                    users=workspace.users or [],
                    config=workspace.config,
                )

            finally:
                session.close()

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get workspace: {str(e)}",
            )

    def update_workspace(self, workspace_id: str, workspace_data: WorkspaceUpdate) -> WorkspaceDetail:
        """Update a workspace"""
        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                workspace = (
                    session.query(WorkspaceModel)
                    .filter(
                        and_(
                            WorkspaceModel.id == workspace_id,
                            WorkspaceModel.deleted_at.is_(None),
                        )
                    )
                    .first()
                )

                if not workspace:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Workspace not found",
                    )

                # Update only provided fields
                if workspace_data.name is not None:
                    workspace.name = workspace_data.name

                workspace.updated_at = datetime.now(timezone.utc)

                session.commit()
                session.refresh(workspace)

                return WorkspaceDetail(
                    id=workspace.id,
                    name=workspace.name,
                    created_at=workspace.created_at,
                    users=workspace.users or [],
                    config=workspace.config,
                )

            finally:
                session.close()

        except HTTPException:
            raise
        except IntegrityError as e:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Workspace update failed due to data conflict: {str(e)}",
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update workspace: {str(e)}",
            )

    def delete_workspace(self, workspace_id: str, _purge: bool = False) -> dict:
        """Delete a workspace (soft delete by default, hard delete if purge=True)"""
        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                workspace = (
                    session.query(WorkspaceModel)
                    .filter(
                        and_(
                            WorkspaceModel.id == workspace_id,
                            WorkspaceModel.deleted_at.is_(None),
                        )
                    )
                    .first()
                )

                if not workspace:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Workspace not found",
                    )

                if _purge:
                    session.delete(workspace)
                    message = "Workspace permanently deleted"
                else:
                    workspace.deleted_at = datetime.now(timezone.utc)
                    message = "Workspace deleted successfully"

                session.commit()

                return {"message": message}

            finally:
                session.close()

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete workspace: {str(e)}",
            )

    def workspace_exists(self, workspace_id: str) -> bool:
        """Check if a workspace exists"""
        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                workspace = (
                    session.query(WorkspaceModel)
                    .filter(
                        and_(
                            WorkspaceModel.id == workspace_id,
                            WorkspaceModel.deleted_at.is_(None),
                        )
                    )
                    .first()
                )

                return workspace is not None

            finally:
                session.close()

        except Exception:
            return False


# Create singleton instance
workspace_service = WorkspaceService()
