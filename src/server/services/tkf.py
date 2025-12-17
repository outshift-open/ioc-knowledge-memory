import logging
from server.schemas.tkf import TkfStoreRequest, TkfStoreResponse
from server.schemas.tkf import TkfDeleteRequest, TkfDeleteResponse
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
            nodes, edges = adapter.convert_to_models(tkf_store_request.dict())

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
                    request_id=request_id,
                    resource_type=ResourceType.MAS_TKF if tkf_store_request.mas_id else ResourceType.WKSP_TKF,
                    audit_type=AuditEventType.CREATE_TKF,
                    audit_resource_id=tkf_store_request.mas_id
                    if tkf_store_request.mas_id
                    else tkf_store_request.wksp_id,
                    created_by="",  # TODO: get user from apikey
                    audit_information=tkf_store_request.dict(),
                    audit_extra_information=response.status,
                )
            )

            return response

        except Exception as e:
            error_msg = f"Failed to create: {str(e)}"
            response = TkfStoreResponse(request_id=request_id, status="failure", message=error_msg)
            # add to audits table
            audit_service.create_audit(
                AuditRequest(
                    request_id=request_id,
                    resource_type=ResourceType.MAS_TKF if tkf_store_request.mas_id else ResourceType.WKSP_TKF,
                    audit_type=AuditEventType.CREATE_TKF,
                    audit_resource_id=tkf_store_request.mas_id
                    if tkf_store_request.mas_id
                    else tkf_store_request.wksp_id,
                    created_by="",  # TODO: get user from apikey
                    audit_information=tkf_store_request.dict(),
                    audit_extra_information=response.status,
                )
            )
            return response

    async def delete_tkf_store(self, tkf_delete_request: TkfDeleteRequest) -> TkfDeleteResponse:
        """Delete a TKF store request"""
        request_id = tkf_delete_request.request_id
        self.logger.info(f"Deleting: {tkf_delete_request}")
        try:
            adapter = Adapter_GraphDB_Neo4j()
            nodes, edges = adapter.convert_to_models(tkf_delete_request.dict())

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
                    request_id=request_id,
                    resource_type=ResourceType.MAS_TKF if tkf_delete_request.mas_id else ResourceType.WKSP_TKF,
                    audit_type=AuditEventType.DELETE_TKF,
                    audit_resource_id=tkf_delete_request.mas_id
                    if tkf_delete_request.mas_id
                    else tkf_delete_request.wksp_id,
                    deleted_by="",  # TODO: get user from apikey
                    audit_information=tkf_delete_request.dict(),
                    audit_extra_information=response.status,
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
                    request_id=request_id,
                    resource_type=ResourceType.MAS_TKF if tkf_delete_request.mas_id else ResourceType.WKSP_TKF,
                    audit_type=AuditEventType.DELETE_TKF,
                    audit_resource_id=tkf_delete_request.mas_id
                    if tkf_delete_request.mas_id
                    else tkf_delete_request.wksp_id,
                    deleted_by="",  # TODO: get user from apikey
                    audit_information=tkf_delete_request.dict(),
                    audit_extra_information=response.status,
                )
            )
            return response


# Global service instance
tkf_service = TkfService()
