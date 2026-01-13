import logging

from server.schemas.tkf import (
    TkfStoreRequest,
    TkfStoreResponse,
    TkfDeleteRequest,
    TkfDeleteResponse,
    TkfQueryRequest,
    TkfQueryResponse,
)

from datetime import datetime
from server.adapters.adapter_graphdb_neo4j import Adapter_GraphDB_Neo4j
from server.database.graph_db.neo4j.src.db_async import GraphDB
from server.services.audit import AuditEventType, ResourceType, audit_service, AuditRequest


class TkfService:
    """Service layer for TKF business logic"""

    def __init__(self):
        # Get logger instance (logging is setup in main.py)
        self.logger = logging.getLogger(__name__)

    async def create_tkf_store(self, tkf_store_request: TkfStoreRequest) -> TkfStoreResponse:
        """Create a new TKF store request"""
        request_id = tkf_store_request.request_id
        self.logger.info(f"Creating: {tkf_store_request}")
        try:
            adapter = Adapter_GraphDB_Neo4j()
            nodes, edges = adapter.convert_to_models(tkf_store_request.model_dump())

            db = GraphDB()
            save_result, msg = await db.save(nodes=nodes, edges=edges, force_replace=tkf_store_request.force_replace)

            if save_result:
                response = TkfStoreResponse(
                    request_id=request_id,
                    status="success",
                    message=f"{msg}",
                )
            else:
                response = TkfStoreResponse(request_id=request_id, status="failure", message=f"{msg}")

            # add to audits table
            audit_service.create_audit(
                AuditRequest(
                    operation_id=request_id,
                    resource_type=ResourceType.MAS,
                    audit_type=AuditEventType.RESOURCE_CREATED,
                    audit_resource_id=tkf_store_request.mas_id
                    if tkf_store_request.mas_id
                    else tkf_store_request.wksp_id,
                    created_by="",  # TODO: get user from apikey
                    audit_information=tkf_store_request.model_dump(),
                    audit_extra_information=response.status,
                    created_at=datetime.utcnow(),
                )
            )

            return response

        except Exception as e:
            error_msg = f"Failed to create: {str(e)}"
            response = TkfStoreResponse(request_id=request_id, status="failure", message=error_msg)
            # add to audits table
            audit_service.create_audit(
                AuditRequest(
                    operation_id=request_id,
                    resource_type=ResourceType.MAS,
                    audit_type=AuditEventType.RESOURCE_CREATED,
                    audit_resource_id=tkf_store_request.mas_id
                    if tkf_store_request.mas_id
                    else tkf_store_request.wksp_id,
                    created_by="",  # TODO: get user from apikey
                    audit_information=tkf_store_request.model_dump(),
                    audit_extra_information=response.status,
                    created_at=datetime.utcnow(),
                )
            )
            return response

    async def delete_tkf_store(self, tkf_delete_request: TkfDeleteRequest) -> TkfDeleteResponse:
        """Delete a TKF store request"""
        request_id = tkf_delete_request.request_id
        self.logger.info(f"Deleting: {tkf_delete_request}")
        try:
            adapter = Adapter_GraphDB_Neo4j()
            nodes, edges = adapter.convert_to_models(tkf_delete_request.model_dump())

            db = GraphDB()
            delete_result, msg = await db.delete(nodes=nodes)

            if delete_result:
                response = TkfDeleteResponse(
                    request_id=request_id,
                    status="success",
                    message=f"{msg}",
                )
            else:
                response = TkfDeleteResponse(
                    request_id=request_id,
                    status="failure",
                    message=f"{msg}",
                )

            # add to audits table
            audit_service.create_audit(
                AuditRequest(
                    operation_id=request_id,
                    resource_type=ResourceType.MAS,
                    audit_type=AuditEventType.RESOURCE_DELETED,
                    audit_resource_id=tkf_delete_request.mas_id
                    if tkf_delete_request.mas_id
                    else tkf_delete_request.wksp_id,
                    deleted_by="",  # TODO: get user from apikey
                    deleted_at=datetime.utcnow(),
                )
            )

            return response

        except Exception as e:
            error_msg = f"Failed to delete: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            response = TkfDeleteResponse(
                request_id=request_id,
                status="failure",
                message=error_msg,
            )
            # add to audits table
            audit_service.create_audit(
                AuditRequest(
                    operation_id=request_id,
                    resource_type=ResourceType.MAS,
                    audit_type=AuditEventType.RESOURCE_DELETED,
                    audit_resource_id=tkf_delete_request.mas_id
                    if tkf_delete_request.mas_id
                    else tkf_delete_request.wksp_id,
                    deleted_by="",  # TODO: get user from apikey
                    audit_information=tkf_delete_request.model_dump(),
                    audit_extra_information=response.status,
                    deleted_at=datetime.utcnow(),
                )
            )
            return response

    async def query_tkf_store(self, tkf_query_request: TkfQueryRequest) -> TkfQueryResponse:
        request_id = tkf_query_request.request_id
        self.logger.info(f"Querying: {tkf_query_request}")

        try:
            adapter = Adapter_GraphDB_Neo4j()
            nodes = adapter.convert_query_to_models(tkf_query_request.dict())
            self.logger.info(f"Query Nodes: {nodes}")

            db = GraphDB()
            # Pass the query_criteria Pydantic model directly
            success, results, msg = await db.query(nodes, query_criteria=tkf_query_request.query_criteria)
            if success:
                records = adapter.convert_models_to_query_response_records(results)
                response = TkfQueryResponse(
                    request_id=request_id,
                    status="success",
                    message=f"{msg}",
                    records=records,
                )
            else:
                response = TkfQueryResponse(
                    request_id=request_id,
                    status="failure",
                    message=f"{msg}",
                    records=[],
                )

            # todo add to audits table

            return response

        except Exception as e:
            error_msg = f"Failed to query: {str(e)}"
            self.logger.error(error_msg, exc_info=True)
            response = TkfQueryResponse(
                request_id=request_id,
                status="failure",
                message=error_msg,
            )

            # todo add to audits table

            return response


# Global service instance
tkf_service = TkfService()
