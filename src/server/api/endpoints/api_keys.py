from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timezone
import uuid
import secrets

from server.schemas.api_key import ApiKeyResponse, ApiKeyDetail, ApiKeyListResponse
from server.models.api_key import ApiKey
from server.storage.memory import storage
from server.utils.validators import validate_uuid

router = APIRouter()


def create_key_preview(key: str) -> str:
    """Create a preview of the API key: first 8 chars + ... + last 4 chars"""
    if len(key) <= 12:
        return key
    return f"{key[:8]}...{key[-4:]}"

@router.post("/{workspace_id}/api-keys", 
             response_model=ApiKeyResponse,
             status_code=status.HTTP_201_CREATED,
             tags=["api-keys"])
async def create_api_key(workspace_id: str) -> ApiKeyResponse:
    """Create a new API key for a workspace
    
    - **workspace_id**: UUID of the workspace
    
    Returns the generated API key string
    """
    validate_uuid(workspace_id, "workspace_id")
    
    if not storage.workspace_exists(workspace_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace {workspace_id} not found"
        )
    
    api_key_string = f"tkf_{secrets.token_hex(16)}"
    
    api_key = ApiKey(
        id=str(uuid.uuid4()),
        key=api_key_string,
        workspace_id=workspace_id,
        created_at=datetime.now(timezone.utc)

    )
    
    storage.create_api_key(api_key)
    
    return ApiKeyResponse(key=api_key_string)



@router.get("/{workspace_id}/api-keys", 
             response_model=ApiKeyListResponse,
             status_code=status.HTTP_200_OK,
             tags=["api-keys"])
async def list_api_keys(workspace_id: str) -> ApiKeyListResponse:
    """List all API keys for a workspace
    
    - **workspace_id**: UUID of the workspace
    
    Returns list of API keys with metadata
    """
    validate_uuid(workspace_id, "workspace_id")
    
    if not storage.workspace_exists(workspace_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace {workspace_id} not found"
        )
    api_keys = storage.get_api_keys_by_workspace(workspace_id)

    api_key_list = []

    for api_key in api_keys:
        api_key_list.append(
            ApiKeyDetail(
                id=api_key.id,
                key_preview=create_key_preview(api_key.key),
                created_at=api_key.created_at
            )
        )  
    
    return ApiKeyListResponse(api_keys=api_key_list, total=len(api_key_list))


@router.delete("/{workspace_id}/api-keys/{api_key_id}", 
               status_code=status.HTTP_204_NO_CONTENT,
               tags=["api-keys"])
async def delete_api_key(workspace_id: str, api_key_id: str) -> None:
    """Delete an API key from a workspace
    
    - **workspace_id**: UUID of the workspace
    - **api_key_id**: UUID of the API key to delete
    
    Returns no content on successful deletion
    """
    validate_uuid(workspace_id, "workspace_id")
    validate_uuid(api_key_id, "api_key_id")
    
    if not storage.workspace_exists(workspace_id):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Workspace {workspace_id} not found"
        )
    
    api_key = storage.get_api_key(api_key_id)
    if not api_key or api_key.workspace_id != workspace_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"API key {api_key_id} not found in workspace {workspace_id}"
        )
    
    storage.delete_api_key(api_key_id)
    
    return