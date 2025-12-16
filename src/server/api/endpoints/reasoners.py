from fastapi import APIRouter, status

from server.schemas.reasoner import (
    ReasonerRequest,
    ReasonerResponse,
    Reasoner,
    Reasoners,
)
from server.services import reasoner_service

router = APIRouter()


@router.post(
    "/{workspace_id}/reasoners",
    response_model=ReasonerResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_reasoner(
    workspace_id: str,
    reasoner_data: ReasonerRequest,
):
    """
    Create a new Reasoner within a workspace

    - **workspace_id**: UUID of the workspace
    - **name**: Friendly name for the reasoner
    - **mas_id**: UUID of the multi-agentic system
    - **config**: Optional configuration for the reasoner

    Returns the UUID and name of the created reasoner
    """
    return reasoner_service.create_reasoner(workspace_id, reasoner_data)


@router.get(
    "/{workspace_id}/reasoners",
    response_model=Reasoners,
)
def list_reasoners(workspace_id: str):
    """
    List all Reasoners in a workspace

    - **workspace_id**: UUID of the workspace

    Returns list of reasoners in the workspace
    """
    return reasoner_service.list_reasoners(workspace_id)


@router.get(
    "/{workspace_id}/reasoners/{reasoner_id}",
    response_model=Reasoner,
)
def get_reasoner(workspace_id: str, reasoner_id: str):
    """
    Get a specific Reasoner by ID

    - **workspace_id**: UUID of the workspace
    - **reasoner_id**: UUID of the reasoner

    Returns detailed reasoner information
    """
    return reasoner_service.get_reasoner(workspace_id, reasoner_id)


@router.delete(
    "/{workspace_id}/reasoners/{reasoner_id}",
    status_code=status.HTTP_200_OK,
)
def delete_reasoner(workspace_id: str, reasoner_id: str, _purge: bool = False):
    """
    Delete a Reasoner

    - **workspace_id**: UUID of the workspace
    - **reasoner_id**: UUID of the reasoner to delete
    - **_purge**: Optional query parameter. If false (default), performs soft delete. If true, performs hard delete.

    Returns success message
    """
    return reasoner_service.delete_reasoner(workspace_id, reasoner_id, _purge)
