from server.schemas.tkf import TkfStoreRequest, TkfStoreResponse, TkfQueryRequest, TkfQueryResponse
from server.schemas.tkf import TkfDeleteRequest, TkfDeleteResponse

# from server.services.knowledge_kvp import knowledge_kvp_service
from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

router = APIRouter()
internal_router = APIRouter()


@router.post(
    "",
    responses={501: {"description": "Not implemented"}, 500: {"description": "Internal server error"}},
)
def create_kvp_store():
    """
    Create/update KVP knowledge store
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="KVP knowledge store creation is not yet implemented"
    )


@router.delete(
    "",
    status_code=status.HTTP_200_OK,
    responses={501: {"description": "Not implemented"}, 500: {"description": "Internal server error"}},
)
def delete_kvp_store():
    """
    Delete a KVP knowledge store
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="KVP knowledge store deletion is not yet implemented"
    )


@router.post(
    "/query",
    responses={501: {"description": "Not implemented"}, 500: {"description": "Internal server error"}},
)
def query_kvp_store():
    """
    Query KVP knowledge store
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="KVP knowledge store querying is not yet implemented"
    )


@internal_router.delete(
    "",
    status_code=status.HTTP_200_OK,
    responses={200: {"description": "Successfully deleted"}, 500: {"description": "Internal server error"}},
)
def internal_delete_kvp_store():
    """
    Internal API to Delete a KVP knowledge store
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="KVP knowledge store deletion is not yet implemented"
    )
