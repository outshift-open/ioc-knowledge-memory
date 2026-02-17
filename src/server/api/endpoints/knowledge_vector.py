from server.schemas.tkf import TkfStoreRequest, TkfStoreResponse, TkfQueryRequest, TkfQueryResponse
from server.schemas.tkf import TkfDeleteRequest, TkfDeleteResponse
from fastapi import APIRouter, HTTPException, status

router = APIRouter()
internal_router = APIRouter()


@router.post(
    "",
    responses={501: {"description": "Not implemented"}, 500: {"description": "Internal server error"}},
)
def create_vector_store():
    """
    Create/update vector knowledge store
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Vector knowledge store creation is not yet implemented"
    )


@router.delete(
    "",
    status_code=status.HTTP_200_OK,
    responses={501: {"description": "Not implemented"}, 500: {"description": "Internal server error"}},
)
def delete_vector_store():
    """
    Delete a vector knowledge store
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Vector knowledge store deletion is not yet implemented"
    )


@router.post(
    "/query",
    responses={501: {"description": "Not implemented"}, 500: {"description": "Internal server error"}},
)
def query_vector_store():
    """
    Query vector knowledge store
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Vector knowledge store querying is not yet implemented"
    )


@internal_router.delete(
    "",
    status_code=status.HTTP_200_OK,
    responses={200: {"description": "Successfully deleted"}, 500: {"description": "Internal server error"}},
)
def internal_delete_vector_store():
    """
    Internal API to Delete a vector knowledge store
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED, detail="Vector knowledge store deletion is not yet implemented"
    )
