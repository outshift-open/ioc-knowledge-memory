from fastapi import APIRouter

from server.api.endpoints.workspaces import router as workspaces_router
from server.api.endpoints.users import router as users_router  
from server.api.endpoints.api_keys import router as api_keys_router

api_router = APIRouter()

api_router.include_router(workspaces_router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(users_router, prefix="/workspaces", tags=["users"])
api_router.include_router(api_keys_router, prefix="/workspaces", tags=["api-keys"])