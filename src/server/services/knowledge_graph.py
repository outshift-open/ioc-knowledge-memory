import logging

from knowledge_memory.server.adapters.adapter_graphdb_agensgraph import AdapterGraphdbAgensgraph
from knowledge_memory.server.database.graph_db.agensgraph.src.db import GraphDB
from knowledge_memory.server.schemas.knowledge_graph import (
    KnowledgeGraphStoreRequest,
    KnowledgeGraphStoreResponse,
    KnowledgeGraphDeleteRequest,
    KnowledgeGraphDeleteResponse,
    KnowledgeGraphQueryRequest,
    KnowledgeGraphQueryResponse,
    QUERY_TYPE_PATH,
    QUERY_TYPE_NEIGHBOUR,
    QUERY_TYPE_CONCEPT,
    ResponseStatus,
)


class KnowledgeGraphService:
    """Service layer for Knowledge Graph business logic"""

    def __init__(self):
        # Get logger instance (logging is setup in main.py)
        self.logger = logging.getLogger(__name__)

    def create_graph_store(self, data: KnowledgeGraphStoreRequest) -> KnowledgeGraphStoreResponse:
        """Create a new knowledge graph store request"""
        request_id = data.request_id
        self.logger.debug(f"Creating: {data}")
        try:
            adapter = AdapterGraphdbAgensgraph()
            graph = adapter.get_graph_name(data.model_dump())
            nodes, edges = adapter.convert_to_models(data.model_dump())

            db = GraphDB()
            save_result, msg = db.save(graph=graph, nodes=nodes, edges=edges, force_replace=data.force_replace)

            if save_result:
                response = KnowledgeGraphStoreResponse(
                    request_id=request_id,
                    status=ResponseStatus.SUCCESS,
                    message=f"{msg}",
                )
            else:
                response = KnowledgeGraphStoreResponse(
                    request_id=request_id, status=ResponseStatus.FAILURE, message=f"{msg}"
                )
            return response

        except Exception as e:
            error_msg = f"Failed to create: {str(e)}"
            response = KnowledgeGraphStoreResponse(
                request_id=request_id, status=ResponseStatus.FAILURE, message=error_msg
            )
            return response

    def delete_graph_store(self, data: KnowledgeGraphDeleteRequest) -> KnowledgeGraphDeleteResponse:
        """Delete a knowledge graph store request.
        Delete concepts and relationships. Graph is not deleted"""
        request_id = data.request_id
        self.logger.info(f"Deleting: {data}")
        try:
            adapter = AdapterGraphdbAgensgraph()
            graph = adapter.get_graph_name(data.model_dump())
            nodes, edges = adapter.convert_to_models(data.model_dump())

            db = GraphDB()
            delete_result, msg = db.delete(graph=graph, nodes=nodes)
            if delete_result:
                response = KnowledgeGraphDeleteResponse(
                    request_id=request_id,
                    status=ResponseStatus.SUCCESS,
                    message=f"{msg}",
                )
            else:
                response = KnowledgeGraphDeleteResponse(
                    request_id=request_id,
                    status=ResponseStatus.FAILURE,
                    message=f"{msg}",
                )
            return response

        except Exception as e:
            error_msg = f"Failed to delete: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            response = KnowledgeGraphDeleteResponse(
                request_id=request_id,
                status=ResponseStatus.FAILURE,
                message=error_msg,
            )
            return response

    def query_graph_store(self, data: KnowledgeGraphQueryRequest) -> KnowledgeGraphQueryResponse:
        request_id = data.request_id
        self.logger.info(f"Querying: {data}")

        try:
            adapter = AdapterGraphdbAgensgraph()
            graph = adapter.get_graph_name(data.model_dump())
            nodes = adapter.convert_query_to_models(data.model_dump())

            db = GraphDB()
            # Validate if graph exists
            graph_result = db.get_graph(graph)
            if not graph_result:
                response = KnowledgeGraphQueryResponse(
                    request_id=request_id,
                    status=ResponseStatus.NOT_FOUND,
                    message=f"Graph {graph} does not exist",
                )
                return response

            # Validate if nodes exist
            not_found_nodes = []
            for node in nodes:
                node_result = db.get_node(graph=graph, node=node)
                if not node_result:
                    not_found_nodes.append(node.id)

            if not_found_nodes:
                response = KnowledgeGraphQueryResponse(
                    request_id=request_id,
                    status=ResponseStatus.NOT_FOUND,
                    message=f"Nodes do not exist: {', '.join(not_found_nodes)}",
                )
                return response

            # Check query type and call appropriate method
            query_type = data.query_criteria.query_type

            if query_type == QUERY_TYPE_PATH:
                self.logger.info(f"Querying path: {nodes}")
                success, results, msg = db.query_type_path(
                    graph=graph,
                    nodes=nodes,
                    depth=data.query_criteria.depth,
                    use_direction=data.query_criteria.use_direction,
                )
            elif query_type == QUERY_TYPE_NEIGHBOUR:
                self.logger.info(f"Querying neighbor: {nodes}")
                success, results, msg = db.query_type_neighbor(graph=graph, nodes=nodes)
            elif query_type == QUERY_TYPE_CONCEPT:
                self.logger.info(f"Querying concept: {nodes}")
                success, results, msg = db.query_type_concept(graph=graph, nodes=nodes)
            else:
                # Default to neighbor query for QUERY_TYPE_NEIGHBOUR
                success, results, msg = db.query_type_neighbor(graph=graph, nodes=nodes)

            if success:
                records = adapter.convert_models_to_query_response_records(results)
                response = KnowledgeGraphQueryResponse(
                    request_id=request_id,
                    status=ResponseStatus.SUCCESS,
                    message=f"{msg}",
                    records=records if records else None,
                )
            else:
                response = KnowledgeGraphQueryResponse(
                    request_id=request_id,
                    status=ResponseStatus.FAILURE,
                    message=f"{msg}",
                )
            return response

        except Exception as e:
            error_msg = f"Failed to query: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            response = KnowledgeGraphQueryResponse(
                request_id=request_id,
                status=ResponseStatus.FAILURE,
                message=error_msg,
            )
            return response

    def delete_graph_store_internal(self, data: KnowledgeGraphDeleteRequest) -> KnowledgeGraphDeleteResponse:
        """Delete a graph"""
        request_id = data.request_id
        self.logger.info(f"Deleting: {data}")
        try:
            adapter = AdapterGraphdbAgensgraph()
            graph = adapter.get_graph_name(data.model_dump())

            db = GraphDB()
            is_deleted = db.delete_graph(graph)

            if is_deleted:
                response = KnowledgeGraphDeleteResponse(
                    request_id=request_id,
                    status=ResponseStatus.SUCCESS,
                    message=f"graph:{graph} deleted",
                )
            else:
                response = KnowledgeGraphDeleteResponse(
                    request_id=request_id,
                    status=ResponseStatus.FAILURE,
                    message=f"graph:{graph} not deleted",
                )
            return response

        except Exception as e:
            error_msg = f"Failed to delete: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            response = KnowledgeGraphDeleteResponse(
                request_id=request_id,
                status=ResponseStatus.FAILURE,
                message=error_msg,
            )
            return response


# Global service instance
knowledge_graph_service = KnowledgeGraphService()
