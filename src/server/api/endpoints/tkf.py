from server.schemas.tkf import TkfStoreRequest, TkfStoreResponse, TkfQueryRequest, TkfQueryResponse
from server.schemas.tkf import TkfDeleteRequest, TkfDeleteResponse
from server.services.tkf import tkf_service
from fastapi import APIRouter, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

router = APIRouter()


@router.post(
    "/",
    response_model=TkfStoreResponse,
    responses={201: {"description": "Successfully created TKF store"}, 500: {"description": "Internal server error"}},
)
async def create_tkf_store(tkf_data: TkfStoreRequest):
    """
    Create a new tkf store request
    """
    response = await tkf_service.create_tkf_store(tkf_data)

    if response.status == "success":
        status_code = status.HTTP_201_CREATED
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(content=jsonable_encoder(response), status_code=status_code)


@router.delete(
    "/",
    response_model=TkfDeleteResponse,
    status_code=status.HTTP_200_OK,
    responses={200: {"description": "Successfully deleted TKF store"}, 500: {"description": "Internal server error"}},
)
async def delete_tkf_store(tkf_data: TkfDeleteRequest):
    """
    Delete a tkf request
    """
    response = await tkf_service.delete_tkf_store(tkf_data)
    if response.status == "success":
        status_code = status.HTTP_200_OK
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(content=jsonable_encoder(response), status_code=status_code)


@router.post(
    "/query",
    response_model=TkfQueryResponse,
    responses={200: {"description": "Successfully queried TKF store"}, 500: {"description": "Internal server error"}},
)
async def query_tkf_store(tkf_data: TkfQueryRequest):
    """
    Query tkf store request
    """
    response = await tkf_service.query_tkf_store(tkf_data)

    if response.status == "success":
        status_code = status.HTTP_200_OK
    else:
        status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

    return JSONResponse(content=jsonable_encoder(response), status_code=status_code)
