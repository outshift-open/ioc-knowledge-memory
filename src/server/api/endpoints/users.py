from fastapi import APIRouter, status

from server.schemas.user import Users
from server.services.user import user_service

router = APIRouter()


@router.get("/", status_code=status.HTTP_200_OK, response_model=Users)
def list_users():
    """
    Get all users

    Returns a list of all active users in the database

    Returns:
        Users: List of users with total count
    """
    return user_service.list_users()
