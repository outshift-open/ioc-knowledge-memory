from fastapi import APIRouter, status

from server.schemas.workspace import (
    WorkspaceCreate,
    WorkspaceResponse,
    WorkspaceDetail,
    WorkspaceUpdate,
    WorkspaceList,
)
from server.services.workspace import workspace_service

router = APIRouter()


@router.post(
    "/",
    response_model=WorkspaceResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_workspace(workspace_data: WorkspaceCreate):
    """
    Create a new workspace

    - **name**: Name of the workspace (required)
    - **users**: List of user IDs (optional)
    - **config**: Workspace configuration (optional)

    Returns the UUID of the created workspace
    """
    return workspace_service.create_workspace(workspace_data)


@router.get("/", response_model=WorkspaceList)
def list_workspaces():
    """
    List all workspaces

    Returns a list of all workspaces in the system
    """
    return workspace_service.list_workspaces()


@router.get("/{workspace_id}", response_model=WorkspaceDetail)
def get_workspace(workspace_id: str):
    """
    Get a specific workspace by ID

    - **workspace_id**: UUID of the workspace

    Returns detailed workspace information
    """
    return workspace_service.get_workspace(workspace_id)


@router.put("/{workspace_id}", response_model=WorkspaceDetail)
def update_workspace(workspace_id: str, workspace_data: WorkspaceUpdate):
    """
    Update a workspace

    - **workspace_id**: UUID of the workspace
    - **name**: New name for the workspace (optional)

    Returns the updated workspace details
    """
    return workspace_service.update_workspace(workspace_id, workspace_data)


@router.delete("/{workspace_id}", status_code=status.HTTP_200_OK)
def delete_workspace(workspace_id: str, _purge: bool = False):
    """
    Delete a workspace

    - **workspace_id**: UUID of the workspace
    - **_purge**: Optional query parameter. If false (default), performs soft
      delete. If true, performs hard delete.

    Returns success message
    """
    return workspace_service.delete_workspace(workspace_id, _purge)
