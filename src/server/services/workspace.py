"""Workspace service - Business logic for workspace operations"""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_, exists

from server.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceDetail,
    WorkspaceUpdate,
    WorkspaceList,
)
from server.database.relational_db.models.workspace import Workspace as WorkspaceModel
from server.database.relational_db.models.mas import MultiAgenticSystem as MASModel
from server.database.relational_db.models.reasoner import Reasoner as ReasonerModel
from server.database.relational_db.models.knowledge_adapter import KnowledgeAdapter as KnowledgeAdapterModel
from server.database.relational_db.db import RelationalDB


class WorkspaceService:
    """Service layer for workspace business logic"""

    DEFAULT_WORKSPACE_NAME = "Default Workspace"

    def _get_dependency_status(self, session, workspace_id: str):
        """Check if workspace has dependent objects before deletion.
        Returns a tuple: (has_dependents: bool, detail: str)
        """
        mas_exists = session.query(
            exists().where(and_(MASModel.workspace_id == workspace_id, MASModel.deleted_at.is_(None)))
        ).scalar()

        reasoner_exists = session.query(
            exists().where(and_(ReasonerModel.workspace_id == workspace_id, ReasonerModel.deleted_at.is_(None)))
        ).scalar()

        kep_exists = session.query(
            exists().where(
                and_(
                    KnowledgeAdapterModel.workspace_id == workspace_id,
                    KnowledgeAdapterModel.deleted_at.is_(None),
                )
            )
        ).scalar()

        if not (mas_exists or reasoner_exists or kep_exists):
            return False, ""

        mas_count = (
            session.query(MASModel).filter(MASModel.workspace_id == workspace_id, MASModel.deleted_at.is_(None)).count()
        )
        reasoner_count = (
            session.query(ReasonerModel)
            .filter(ReasonerModel.workspace_id == workspace_id, ReasonerModel.deleted_at.is_(None))
            .count()
        )
        kep_count = (
            session.query(KnowledgeAdapterModel)
            .filter(
                KnowledgeAdapterModel.workspace_id == workspace_id,
                KnowledgeAdapterModel.deleted_at.is_(None),
            )
            .count()
        )

        found_parts = []
        if mas_count > 0:
            found_parts.append(f"{mas_count} MAS")
        if reasoner_count > 0:
            found_parts.append(f"{reasoner_count} {'reasoner' if reasoner_count == 1 else 'reasoners'}")
        if kep_count > 0:
            found_parts.append(f"{kep_count} {'knowledge adapter' if kep_count == 1 else 'knowledge adapters'}")
        return True, ", ".join(found_parts)

    def _purge_dependents(self, session, workspace_id: str):
        """Hard delete all dependent objects for a workspace during internal purge operations"""
        session.query(ReasonerModel).filter(ReasonerModel.workspace_id == workspace_id).delete(
            synchronize_session=False
        )
        session.query(KnowledgeAdapterModel).filter(KnowledgeAdapterModel.workspace_id == workspace_id).delete(
            synchronize_session=False
        )
        session.query(MASModel).filter(MASModel.workspace_id == workspace_id).delete(synchronize_session=False)

    def create_workspace(self, workspace_data: WorkspaceCreate) -> WorkspaceResponse:
        """Create a new workspace"""
        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                # Prevent duplicate active workspace names
                existing = (
                    session.query(WorkspaceModel)
                    .filter(
                        WorkspaceModel.name == workspace_data.name,
                        WorkspaceModel.deleted_at.is_(None),
                    )
                    .first()
                )
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Workspace with name '{workspace_data.name}' already exists",
                    )

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

        except HTTPException:
            raise
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

    def delete_workspace(self, workspace_id: str, _purge: bool = False, allow_default_delete: bool = False) -> dict:
        """Delete a workspace (soft delete by default, hard delete if purge=True)
        Blocks deletion of the default workspace.
        """
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

                # Block deletion of the Default Workspace in public paths
                if (not allow_default_delete) and (workspace.name == self.DEFAULT_WORKSPACE_NAME):
                    raise HTTPException(
                        status_code=status.HTTP_403_FORBIDDEN,
                        detail="Failed to delete workspace: Default Workspace cannot be deleted",
                    )

                # Validate dependent objects only for soft delete; for purge, hard-delete dependents first
                has_deps, found_detail = self._get_dependency_status(session, workspace_id)
                if has_deps and not _purge:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=(
                            "Workspace has dependent objects. "
                            "Delete all dependent objects before deleting the workspace. "
                            f"Found: {found_detail}."
                        ),
                    )

                if _purge:
                    # Hard delete dependents (including soft-deleted ones) to avoid FK violations
                    self._purge_dependents(session, workspace_id)
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
