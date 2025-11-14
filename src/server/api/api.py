from fastapi import APIRouter

from api.endpoints.workspaces import router as workspaces_router
from api.endpoints.users import router as users_router  

api_router = APIRouter()

api_router.include_router(workspaces_router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(users_router, prefix="/workspaces", tags=["users"])
