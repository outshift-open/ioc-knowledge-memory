from fastapi import APIRouter, status, Query, Body

from server.schemas.reasoner import (
    ReasonerRequest,
    ReasonerResponse,
    Reasoner,
    Reasoners,
    QueryRequest,
    QueryResponse,
    QueryHistoryItem,
    QueryEvents,
    QueryEventFilter,
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


#################################################
# Reasoner Query History Endpoints
#################################################
@router.post(
    "/{workspace_id}/reasoners/{reasoner_id}/query_history",
    response_model=QueryResponse,
    status_code=status.HTTP_201_CREATED,
)
def store_reasoner_query(
    workspace_id: str,
    reasoner_id: str,
    query_data: QueryRequest,
):
    """
    Store a reasoner query response as backup history

    - **workspace_id**: UUID of the workspace
    - **reasoner_id**: UUID of the reasoner
    - **reasoner_cognition_response_id**: ID of the reasoner cognition response
    - **status**: Status of the query execution
    - **reasoner_cognition_request_id**: ID of the reasoner cognition request
    - **records**: Query result records
    - **meta**: Metadata about the query

    Returns the stored query information
    """
    return reasoner_service.store_reasoner_event(workspace_id, reasoner_id, query_data.model_dump())


@router.post(
    "/{workspace_id}/reasoning_history/events",
    response_model=QueryEvents,
)
def list_and_filter_reasoner_events(
    workspace_id: str,
    filters: QueryEventFilter = Body(default_factory=QueryEventFilter),
):
    """
    List Events in a workspace with optional filters

    - **workspace_id**: UUID of the workspace
    - **reasoner_id**: Optional filter by reasoner ID. If not provided, returns events from all reasoners
    - **request_id**: Optional filter by request ID
    - **response_id**: Optional filter by response ID
    - **created_by**: Optional filter by user who created the query
    - **start_date**: Optional filter for queries created on or after this date (ISO 8601 format)
    - **end_date**: Optional filter for queries created on or before this date (ISO 8601 format)
    - **limit**: Maximum number of records to return (default: 100, max: 1000)
    - **offset**: Number of records to skip for pagination (default: 0)

    Returns list of query events from the workspace or a specific reasoner with pagination support
    """
    return reasoner_service.list_and_filter_reasoner_events(workspace_id, filters.reasoner_id, filters)


@router.get(
    "/{workspace_id}/reasoning_history/events/{query_event_id}",
    response_model=QueryHistoryItem,
)
def get_reasoner_event_details(workspace_id: str, query_event_id: str):
    """
    Get detailed query event information for a specific query event

    - **workspace_id**: UUID of the workspace
    - **query_event_id**: UUID of the query event

    Returns detailed query event information including request/response IDs and response data
    """
    return reasoner_service.get_reasoner_event_details(workspace_id, query_event_id)
