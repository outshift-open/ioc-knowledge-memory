from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timezone
import uuid

from server.schemas.workspace import (
    WorkspaceCreate, 
    WorkspaceResponse, 
    WorkspaceDetail, 
    WorkspaceUpdate,
    WorkspaceList
)
from server.models.workspace import Workspace
from server.storage.memory import storage

router = APIRouter()


@router.post("/", response_model=WorkspaceResponse, status_code=status.HTTP_201_CREATED)
def create_workspace(workspace_data: WorkspaceCreate):
    """
    Create a new workspace
    
    - **name**: Name of the workspace (required)
    
    Returns the UUID of the created workspace
    """
    workspace_id = str(uuid.uuid4())
    
    workspace = Workspace(
        id=workspace_id,
        name=workspace_data.name,
        created_at=datetime.now(timezone.utc)
    )
    
    storage.create_workspace(workspace)
    
    return WorkspaceResponse(id=workspace_id)


@router.get("/", response_model=WorkspaceList)
def list_workspaces():
    """
    List all workspaces
    
    Returns a list of all workspaces in the system
    """
    workspaces_dict = storage.list_workspaces()
    workspaces = [
        WorkspaceDetail(
            id=ws.id,
            name=ws.name,
            created_at=ws.created_at,
            users=ws.users,
            api_keys=ws.api_keys
        )
        for ws in workspaces_dict.values()
    ]
    
    return WorkspaceList(
        workspaces=workspaces,
        total=len(workspaces)
    )


@router.get("/{workspace_id}", response_model=WorkspaceDetail)
def get_workspace(workspace_id: str):
    """
    Get a specific workspace by ID
    
    - **workspace_id**: UUID of the workspace
    
    Returns detailed workspace information
    """
    workspace = storage.get_workspace(workspace_id)
    if not workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    return WorkspaceDetail(
        id=workspace.id,
        name=workspace.name,
        created_at=workspace.created_at,
        users=workspace.users,
        api_keys=workspace.api_keys
    )


@router.put("/{workspace_id}", response_model=WorkspaceDetail)
def update_workspace(workspace_id: str, workspace_data: WorkspaceUpdate):
    """
    Update a workspace
    
    - **workspace_id**: UUID of the workspace
    - **name**: New name for the workspace (optional)
    
    Returns the updated workspace details
    """
    existing_workspace = storage.get_workspace(workspace_id)
    if not existing_workspace:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    if workspace_data.name is not None:
        existing_workspace.name = workspace_data.name
    
    storage.update_workspace(workspace_id, existing_workspace)
    
    return WorkspaceDetail(
        id=existing_workspace.id,
        name=existing_workspace.name,
        created_at=existing_workspace.created_at,
        users=existing_workspace.users,
        api_keys=existing_workspace.api_keys
    )


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workspace(workspace_id: str):
    """
    Delete a workspace
    
    - **workspace_id**: UUID of the workspace
    
    Removes the workspace and all associated data
    """
    if not storage.workspace_exists(workspace_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    storage.delete_workspace(workspace_id)
    
