from fastapi import APIRouter, HTTPException, status
from datetime import datetime

from server.schemas.software import (
    SoftwareCreate,
    SoftwareResponse,
    SoftwareDetail,
    SoftwareUpdate,
    SoftwareList,
    SoftwareConfig,
)
from server.models.software import Software
from server.storage.memory import storage

router = APIRouter()

# temporary - use in-memory storage


@router.post("/{workspace_id}/softwares", response_model=SoftwareResponse, status_code=status.HTTP_201_CREATED)
def create_software(workspace_id: str, software_data: SoftwareCreate):
    """
    Create a new software

    - **workspace_id**: UUID of the workspace
    - **type**: Type of the software (Reasoner or KEP Adapter)
    - **name**: Name of the software (required)
    - **config**: Optional software configuration

    Returns the created software details
    """
    # Validate workspace exists
    if not storage.workspace_exists(workspace_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workspace '{workspace_id}' not found")

    try:
        software = Software(
            type=software_data.type,
            name=software_data.name,
            config=software_data.config.dict() if software_data.config else None,
            workspace_id=workspace_id,
        )

        created_software = storage.create_software(software)
        return created_software

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to create software: {str(e)}"
        )


@router.get("/{workspace_id}/softwares", response_model=SoftwareList)
def list_softwares(workspace_id: str):
    """
    List all softwares in a workspace

    - **workspace_id**: UUID of the workspace

    Returns a list of all softwares in the specified workspace
    """
    # Validate workspace exists
    if not storage.workspace_exists(workspace_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workspace '{workspace_id}' not found")

    try:
        softwares_dict = storage.list_softwares()
        softwares = [
            SoftwareDetail(
                id=sw.id,
                type=sw.type,
                name=sw.name,
                config=SoftwareConfig(**sw.config) if sw.config else None,
                workspace_id=sw.workspace_id,
                created_at=sw.created_at,
            )
            for sw in softwares_dict.values()
            if sw.deleted_at is None
            and sw.workspace_id == workspace_id  # Only return non-deleted software in this workspace
        ]

        return SoftwareList(
            softwares=softwares,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to list softwares: {str(e)}"
        )


@router.get("/{workspace_id}/softwares/{software_id}", response_model=SoftwareDetail)
def get_software(workspace_id: str, software_id: str):
    """
    Get a specific software by ID within a workspace

    - **workspace_id**: UUID of the workspace
    - **software_id**: UUID of the software

    Returns detailed software information
    """
    # Validate workspace exists
    if not storage.workspace_exists(workspace_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workspace '{workspace_id}' not found")

    # Use workspace-scoped lookup
    software = storage.get_software(software_id)
    if not software:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Software '{software_id}' not found in workspace '{workspace_id}'",
        )

    # Check if software is soft-deleted - should be handled by DB
    # if software.deleted_at is not None:
    #   raise HTTPException(
    #     status_code=status.HTTP_404_NOT_FOUND,
    #     detail=f"Software '{software_id}' not found"
    #   )

    try:
        return SoftwareDetail(
            id=software.id,
            type=software.type,
            name=software.name,
            config=SoftwareConfig(**software.config) if software.config else None,
            workspace_id=software.workspace_id,
            created_at=software.created_at,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to retrieve software: {str(e)}"
        )


@router.put("/{workspace_id}/softwares/{software_id}", response_model=SoftwareDetail)
def update_software(workspace_id: str, software_id: str, software_data: SoftwareUpdate):
    """
    Update a software within a workspace

    - **workspace_id**: UUID of the workspace
    - **software_id**: UUID of the software
    - **name**: New name for the software (optional)

    Returns the updated software details
    """
    # Validate workspace exists
    if not storage.workspace_exists(workspace_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workspace '{workspace_id}' not found")

    # Use workspace-scoped lookup
    existing_software = storage.get_software(software_id)
    if not existing_software:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Software '{software_id}' not found in workspace '{workspace_id}'",
        )

    # Check if software is soft-deleted - should be handled by DB
    # if existing_software.deleted_at is not None:
    #   raise HTTPException(
    #     status_code=status.HTTP_404_NOT_FOUND,
    #     detail=f"Software '{software_id}' not found"
    #   )
    #
    # # Validate field to update - todo what additional fields can be updated
    # if software_data.name is None:
    #   raise HTTPException(
    #     status_code=status.HTTP_400_BAD_REQUEST,
    #     detail="No valid fields provided for update"
    #   )

    try:
        if software_data.name is not None:
            existing_software.name = software_data.name
            existing_software.updated_at = datetime.now()

        success = storage.update_software(software_id, existing_software)
        if not success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to update software")

        return SoftwareDetail(
            id=existing_software.id,
            type=existing_software.type,
            name=existing_software.name,
            config=SoftwareConfig(**existing_software.config) if existing_software.config else None,
            workspace_id=existing_software.workspace_id,
            created_at=existing_software.created_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to update software: {str(e)}"
        )


@router.delete("/{workspace_id}/softwares/{software_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_software(workspace_id: str, software_id: str):
    """
    Delete a software within a workspace

    - **workspace_id**: UUID of the workspace
    - **software_id**: UUID of the software

    Removes the software and all associated data
    """
    # Validate workspace exists
    if not storage.workspace_exists(workspace_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Workspace '{workspace_id}' not found")

    # Use workspace-scoped lookup
    existing_software = storage.get_software(software_id)
    if not existing_software:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Software '{software_id}' not found in workspace '{workspace_id}'",
        )

    # Check if already soft-deleted - should be handled by DB
    # if existing_software.deleted_at is not None:
    #   raise HTTPException(
    #     status_code=status.HTTP_404_NOT_FOUND,
    #     detail=f"Software '{software_id}' not found"
    #   )

    try:
        success = storage.delete_software(software_id)
        if not success:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete software")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to delete software: {str(e)}"
        )
