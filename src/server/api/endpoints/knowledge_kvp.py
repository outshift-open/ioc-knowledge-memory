# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

import logging
from fastapi import APIRouter, HTTPException, status, Path

from server.services.knowledge_keyvalue import KnowledgeKVPService
from server.schemas.knowledge_keyvalue import (
    ScopeType,
    KnowledgeKVPStoreOnboardRequest,
    KnowledgeKVPStoreOnboardResponse,
    KnowledgeKVPStoreOnboardDeleteRequest,
    KnowledgeKVPStoreRequest,
    KnowledgeKVPStoreResponse,
    KnowledgeKVPQueryRequest,
    KnowledgeKVPQueryResponse,
    KnowledgeKVPDeleteRequest,
    KnowledgeKVPDeleteResponse,
    ResponseStatus,
)

logger = logging.getLogger(__name__)

router = APIRouter()
internal_router = APIRouter()

# Initialize service
kvp_service = KnowledgeKVPService()


@router.post(
    "/stores/{store_id}",
    status_code=status.HTTP_201_CREATED,
    response_model=KnowledgeKVPStoreOnboardResponse,
    responses={
        201: {"description": "Knowledge KVP store onboarded successfully"},
        400: {"description": "Bad request - validation error"},
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)
def onboard_kvp_store(
    store_id: str = Path(..., description="Unique identifier for the KVP store"),
    request: KnowledgeKVPStoreOnboardRequest = ...,
):
    """
    Onboard KVP Store

    Creates essential entities for the key-value pair store to function and provides partitioning by workspace.
    """
    try:
        logger.info(f"Onboarding KVP store with ID: {store_id}")
        response = kvp_service.onboard(store_id, request)

        if response.status == ResponseStatus.SUCCESS:
            return response
        elif response.status == ResponseStatus.NOT_FOUND:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=response.message)
        elif response.status == ResponseStatus.VALIDATION_ERROR:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.message)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response.message)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in onboard_kvp_store: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete(
    "/stores/{store_id}",
    responses={
        501: {"description": "Not implemented - KVP knowledge store deletion is currently supported as an internal API"}
    },
)
def onboard_kvp_store_delete(
    store_id: str = Path(..., description="Unique identifier for the KVP store"),
    request: KnowledgeKVPStoreOnboardDeleteRequest = ...,
):
    """
    Delete KVP Store (Not Implemented)

    Delete a partition of the key-value pair knowledge store and associated entities created during onboarding of the store.
    Currently supported as an internal API only.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="KVP knowledge store deletion is currently supported as an *internal API*",
    )


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=KnowledgeKVPStoreResponse,
    responses={
        201: {"description": "Knowledge KVP data successfully created/updated"},
        400: {"description": "Bad request - validation error"},
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)
def upsert_kvp_store(request: KnowledgeKVPStoreRequest):
    """
    Upsert KVP Data

    Upsert key-value pairs in the KVP knowledge store. Either all records are upserted or none (runs as a transaction).
    """
    try:
        logger.info(f"Upserting KVP data for MAS: {request.mas_id}")
        response = kvp_service.create_kvp_store(request)

        if response.status == ResponseStatus.SUCCESS:
            return response
        elif response.status == ResponseStatus.NOT_FOUND:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=response.message)
        elif response.status == ResponseStatus.VALIDATION_ERROR:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.message)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response.message)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in upsert_kvp_store: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.delete(
    "",
    status_code=status.HTTP_200_OK,
    response_model=KnowledgeKVPDeleteResponse,
    responses={
        200: {"description": "Knowledge KVP data successfully deleted"},
        400: {"description": "Bad request - validation error"},
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)
def delete_kvp_store(request: KnowledgeKVPDeleteRequest):
    """
    Delete KVP Entity

    Delete a key-value pair from the KVP knowledge store
    """
    try:
        logger.info(f"Deleting KVP data for MAS: {request.mas_id}, key: {request.key}")
        response = kvp_service.delete_kvp_store(request)

        if response.status == ResponseStatus.SUCCESS:
            return response
        elif response.status == ResponseStatus.NOT_FOUND:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=response.message)
        elif response.status == ResponseStatus.VALIDATION_ERROR:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.message)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response.message)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in delete_kvp_store: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@router.post(
    "/query",
    status_code=status.HTTP_200_OK,
    response_model=KnowledgeKVPQueryResponse,
    responses={
        200: {"description": "Query executed successfully"},
        400: {"description": "Bad request"},
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)
def query_kvp_store(request: KnowledgeKVPQueryRequest):
    """
    Query KVP Store

    Query key-value pairs from the KVP knowledge store using various query types including key-based lookups
    """
    try:
        logger.info(f"Querying KVP data for MAS: {request.mas_id}")
        response = kvp_service.query_kvp_store(request)

        if response.status == ResponseStatus.SUCCESS:
            return response
        elif response.status == ResponseStatus.NOT_FOUND:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=response.message)
        elif response.status == ResponseStatus.VALIDATION_ERROR:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=response.message)
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=response.message)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in query_kvp_store: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")


@internal_router.delete(
    "/stores/{store_id}",
    status_code=status.HTTP_200_OK,
    response_model=KnowledgeKVPStoreOnboardResponse,
    responses={
        200: {"description": "Knowledge KVP data successfully deleted"},
        400: {"description": "Bad request - validation error"},
        404: {"description": "Not found"},
        500: {"description": "Internal server error"},
    },
)
def internal_delete_kvp_store(
    store_id: str = Path(..., description="Unique identifier for the KVP store"),
    request: KnowledgeKVPStoreOnboardDeleteRequest = ...,
):
    """
    Internal Delete KVP Store

    Internal method to hard delete a KVP store schema and all associated data
    """
    try:
        logger.info(f"Internal delete KVP store with ID: {store_id}")

        # For internal delete, we actually delete the schema
        from server.database.keyvalue_db.postgres.src.db import KeyValueDB

        db = KeyValueDB()
        schema_name = kvp_service.get_schema_name(store_id, request.scope)

        delete_success = db.delete_schema(schema_name)

        if delete_success:
            return KnowledgeKVPStoreOnboardResponse(
                request_id=request.request_id,
                status=ResponseStatus.SUCCESS,
                message=f"Successfully deleted KVP store {store_id}",
            )
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"KVP store {store_id} not found")

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in internal_delete_kvp_store: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal server error")
