from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timezone
import uuid

from server.schemas.user import UserCreate, UserResponse, UserDetail
from server.models.user import User
from server.storage.memory import storage

router = APIRouter()


@router.post("/{workspace_id}/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def create_user_in_workspace(workspace_id: str, user_data: UserCreate):
    """
    Create a new user in a workspace
    
    - **workspace_id**: UUID of the workspace
    - **name**: Name of the user (required)
    - **email**: Email address of the user (required)
    
    Returns the UUID of the created user
    """
    if not storage.workspace_exists(workspace_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    user_id = str(uuid.uuid4())
    
    user = User(
        id=user_id,
        name=user_data.name,
        email=user_data.email,
        workspace_id=workspace_id,
        created_at=datetime.now(timezone.utc)
    )
    
    storage.create_user(user)
    
    return UserResponse(id=user_id)


@router.get("/{workspace_id}/users", response_model=list[UserDetail])
def list_users_in_workspace(workspace_id: str):
    """
    List all users in a workspace
    
    - **workspace_id**: UUID of the workspace
    
    Returns a list of all users in the specified workspace
    """
    if not storage.workspace_exists(workspace_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Workspace not found"
        )
    
    users = storage.get_users_by_workspace(workspace_id)

    workspace = storage.get_workspace(workspace_id)
    workspace_name = workspace.name if workspace else "Unknown Workspace"
    
    return [
        UserDetail(
            id=user.id,
            name=user.name,
            email=user.email,
            workspace_id=user.workspace_id,
            workspace_name=workspace_name,
            created_at=user.created_at
        )
        for user in users
    ]