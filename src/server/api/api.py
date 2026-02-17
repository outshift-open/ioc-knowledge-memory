from fastapi import APIRouter

from server.api.endpoints.workspaces import router as workspaces_router, internal_router as internal_workspaces_router
from server.api.endpoints.softwares import router as softwares_router
from server.api.endpoints.tkf import router as tkf_router
from server.api.endpoints.mas import router as mas_router
from server.api.endpoints.reasoners import router as reasoners_router
from server.api.endpoints.knowledge_adapters import router as kep_router
from server.api.endpoints.users import router as users_router
from server.api.endpoints.audit import router as audits_router
from server.api.endpoints.knowledge_graph import (
    router as knowledge_graph_router,
    internal_router as internal_knowledge_graph_router,
)
from server.api.endpoints.knowledge_vector import (
    router as knowledge_vector_router,
    internal_router as internal_knowledge_vector_router,
)
from server.api.endpoints.knowledge_kvp import (
    router as knowledge_kvp_router,
    internal_router as internal_knowledge_kvp_router,
)


api_router = APIRouter()

api_router.include_router(workspaces_router, prefix="/workspaces", tags=["workspaces"])
api_router.include_router(internal_workspaces_router, prefix="/internal/workspaces", tags=["internal-workspaces"])
api_router.include_router(softwares_router, prefix="/softwares", tags=["softwares"])
api_router.include_router(mas_router, prefix="/workspaces", tags=["multi-agentic-systems"])
api_router.include_router(reasoners_router, prefix="/workspaces", tags=["reasoners"])
api_router.include_router(kep_router, prefix="/workspaces", tags=["knowledge-adapters"])
api_router.include_router(users_router, prefix="/users", tags=["users"])
api_router.include_router(tkf_router, prefix="/tkf", tags=["tkf"])
api_router.include_router(audits_router, prefix="/audits", tags=["audits"])

# Knowledge store routers
api_router.include_router(knowledge_graph_router, prefix="/knowledge/graphs", tags=["knowledge-graph"])
api_router.include_router(knowledge_vector_router, prefix="/knowledge/vectors", tags=["knowledge-vector"])
api_router.include_router(knowledge_kvp_router, prefix="/knowledge/kvps", tags=["knowledge-kvp"])

# Internal knowledge store routers
api_router.include_router(
    internal_knowledge_graph_router, prefix="/internal/knowledge/graphs", tags=["internal-knowledge-graph"]
)
api_router.include_router(
    internal_knowledge_vector_router, prefix="/internal/knowledge/vectors", tags=["internal-knowledge-vector"]
)
api_router.include_router(
    internal_knowledge_kvp_router, prefix="/internal/knowledge/kvps", tags=["internal-knowledge-kvp"]
)
