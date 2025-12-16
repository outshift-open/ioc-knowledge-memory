from fastapi import APIRouter, status

from server.schemas.multi_agentic_system import (
    MultiAgenticSystemRequest,
    MultiAgenticSystemResponse,
    MultiAgenticSystem,
    MultiAgenticSystems,
)
from server.services import mas_service

router = APIRouter()


@router.post(
    "/{workspace_id}/multi-agentic-systems",
    response_model=MultiAgenticSystemResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_multi_agentic_system(
    workspace_id: str,
    mas_data: MultiAgenticSystemRequest,
):
    """
    Create a new Multi-Agentic System (MAS) within a workspace

    - **workspace_id**: UUID of the workspace
    - **name**: Unique name within the workspace for the MAS
    - **description**: Optional description of the MAS
    - **agents**: Optional configuration of agents in the system
    - **config**: Optional configuration for managing long-term memories

    Returns the UUID and name of the created MAS
    """
    return mas_service.create_multi_agentic_system(workspace_id, mas_data)


@router.get(
    "/{workspace_id}/multi-agentic-systems",
    response_model=MultiAgenticSystems,
)
def list_multi_agentic_systems(workspace_id: str):
    """
    List all Multi-Agentic Systems in a workspace

    - **workspace_id**: UUID of the workspace

    Returns list of MAS in the workspace
    """
    return mas_service.list_multi_agentic_systems(workspace_id)


@router.get(
    "/{workspace_id}/multi-agentic-systems/{mas_id}",
    response_model=MultiAgenticSystem,
)
def get_multi_agentic_system(workspace_id: str, mas_id: str):
    """
    Get a specific Multi-Agentic System by ID

    - **workspace_id**: UUID of the workspace
    - **mas_id**: UUID of the multi-agentic system

    Returns detailed MAS information
    """
    return mas_service.get_multi_agentic_system(workspace_id, mas_id)


@router.delete(
    "/{workspace_id}/multi-agentic-systems/{mas_id}",
    status_code=status.HTTP_200_OK,
)
def delete_multi_agentic_system(workspace_id: str, mas_id: str, _purge: bool = False):
    """
    Delete a Multi-Agentic System

    - **workspace_id**: UUID of the workspace
    - **mas_id**: UUID of the multi-agentic system to delete
    - **_purge**: Optional query parameter. If false (default), performs soft delete. If true, performs hard delete.

    Returns success message
    """
    return mas_service.delete_multi_agentic_system(workspace_id, mas_id, _purge)
