from fastapi import APIRouter

from server.api.endpoints.knowledge_graph import (
    router as knowledge_graph_router,
    internal_router as internal_knowledge_graph_router,
)
from server.api.endpoints.knowledge_kvp import (
    router as knowledge_kvp_router,
    internal_router as internal_knowledge_kvp_router,
)
from server.api.endpoints.knowledge_vector import (
    router as knowledge_vector_router,
    internal_router as internal_knowledge_vector_router,
)

api_router = APIRouter()

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
