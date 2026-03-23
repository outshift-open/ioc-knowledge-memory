# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

import logging

from knowledge_memory.server.database.vector_db.pgvector.src.db import VectorDB, VectorDBStoreRequest, VectorDBQueryRequest
from knowledge_memory.server.schemas.knowledge_vector import (
    KnowledgeVectorStoreRequest,
    KnowledgeVectorStoreResponse,
    KnowledgeVectorStoreOnboardRequest,
    KnowledgeVectorStoreOnboardResponse,
    KnowledgeVectorStoreOnboardDeleteRequest,
    KnowledgeVectorStoreOnboardDeleteResponse,
    KnowledgeVectorQueryRequest,
    KnowledgeVectorQueryResponse,
    KnowledgeVectorQueryResponseRecord,
    KnowledgeVectorDeleteRequest,
    KnowledgeVectorDeleteResponse,
    ResponseStatus,
)

WORKSPACE_SCHEMA_PREFIX = "workspace_"


class KnowledgeVectorService:
    """Service layer for Knowledge Vector business logic"""

    def __init__(self):
        # Get logger instance (logging is setup in main.py)
        self.logger = logging.getLogger(__name__)

    def _normalize_id(self, id: str) -> str:
        """
        Normalize ID.

        Args:
            id: ID to normalize

        Returns:
            str: Normalized ID with hyphens replaced by underscores
        """
        normalized_id = id.replace("-", "_")
        return f"{normalized_id}"

    def _denormalize_id(self, normalized_id: str) -> str:
        """
        Denormalize ID (reverse the normalization process).

        Args:
            normalized_id: Normalized ID to denormalize

        Returns:
            str: Original ID with underscores replaced by hyphens
        """
        denormalized_id = normalized_id.replace("_", "-")
        return denormalized_id

    def get_schema_name(self, wksp_id: str) -> str:
        """
        Helper method to generate the schema name for a workspace.

        Args:
            wksp_id: Workspace ID

        Returns:
            str: Normalized schema name with workspace prefix
        """
        return WORKSPACE_SCHEMA_PREFIX + self._normalize_id(wksp_id)

    def _workspace_exists(self, wksp_id: str) -> bool:
        """
        Check if a workspace exists by verifying its schema exists.

        Args:
            wksp_id: Workspace ID to check

        Returns:
            bool: True if workspace exists, False otherwise
        """
        try:
            db = VectorDB()
            schema_name = self.get_schema_name(wksp_id)
            schema_info = db.get_schema(schema_name)
            return schema_info is not None
        except Exception as e:
            self.logger.error(f"Error checking workspace existence for {wksp_id}: {str(e)}")
            return False

    def onboard(self, store_id: str, data: KnowledgeVectorStoreOnboardRequest) -> KnowledgeVectorStoreOnboardResponse:
        request_id = data.request_id
        self.logger.info(f"input request: {data}, store_id: {store_id}")

        try:
            db = VectorDB()

            # Normalize schema name and create schema and table using onboard method
            schema_name = self.get_schema_name(store_id)
            onboard_success = db.onboard(schema_name)

            if onboard_success:
                self.logger.info(f"Successfully created vectorstore container for store: {store_id}")
                return KnowledgeVectorStoreOnboardResponse(
                    request_id=request_id,
                    status=ResponseStatus.SUCCESS,
                    message=f"Successfully onboarded store {store_id}",
                )
            else:
                self.logger.error(f"Failed to create vectorstore container for store: {store_id}")
                return KnowledgeVectorStoreOnboardResponse(
                    request_id=request_id, status=ResponseStatus.FAILURE, message=f"Failed to onboard store {store_id}"
                )

        except Exception as e:
            self.logger.error(f"Exception in onboard for request {request_id}: {str(e)}")
            return KnowledgeVectorStoreOnboardResponse(
                request_id=request_id, status=ResponseStatus.FAILURE, message=f"Internal error: {str(e)}"
            )

    def create_vector_store(self, data: KnowledgeVectorStoreRequest) -> KnowledgeVectorStoreResponse:
        request_id = data.request_id
        self.logger.info(f"Upserting vectorstore: {data}")

        try:
            # Check if workspace exists
            if not self._workspace_exists(data.wksp_id):
                self.logger.warning(f"Workspace {data.wksp_id} not found for request: {request_id}")
                return KnowledgeVectorStoreResponse(
                    request_id=request_id,
                    status=ResponseStatus.NOT_FOUND,
                    message=f"Workspace {data.wksp_id} not found",
                )

            db = VectorDB()

            # Convert to VectorDBStoreRequest and save records
            vector_request = VectorDBStoreRequest()
            vector_request.schema_name = self.get_schema_name(data.wksp_id)
            vector_request.mas_id = data.mas_id
            vector_request.wksp_id = data.wksp_id
            vector_request.records = data.records

            save_success = db.save(vector_request)

            if save_success:
                self.logger.info(f"Successfully saved records for request: {request_id}")
                return KnowledgeVectorStoreResponse(
                    request_id=request_id,
                    status=ResponseStatus.SUCCESS,
                    message=f"Successfully saved {len(data.records)} records",
                )
            else:
                self.logger.error(f"Failed to save records for request: {request_id}")
                return KnowledgeVectorStoreResponse(
                    request_id=request_id, status=ResponseStatus.FAILURE, message="Failed to save records"
                )

        except Exception as e:
            self.logger.error(f"Exception in create_vector_store for request {request_id}: {str(e)}")
            return KnowledgeVectorStoreResponse(
                request_id=request_id, status=ResponseStatus.FAILURE, message=f"Internal error: {str(e)}"
            )

    def query_vector_store(self, data: KnowledgeVectorQueryRequest) -> KnowledgeVectorQueryResponse:
        """Query vector store based on the provided criteria."""
        request_id = data.request_id
        self.logger.info(f"Querying vectorstore: {data}")

        try:
            # Check if workspace exists
            if not self._workspace_exists(data.wksp_id):
                self.logger.warning(f"Workspace {data.wksp_id} not found for request: {request_id}")
                return KnowledgeVectorQueryResponse(
                    request_id=request_id,
                    status=ResponseStatus.NOT_FOUND,
                    message=f"Workspace {data.wksp_id} not found",
                )

            db = VectorDB()

            # Create query request for database layer
            schema_name = self.get_schema_name(data.wksp_id)

            # Create query request for database layer
            query_request = VectorDBQueryRequest(
                schema_name=schema_name, query_criteria=data.query_criteria, mas_id=data.mas_id, wksp_id=data.wksp_id
            )

            # Execute query
            query_results = db.query(query_request)

            if query_results is not None:
                # Convert dictionary results to KnowledgeVectorQueryResponseRecord objects
                response_records = []
                for result in query_results:
                    # Build record data, only including distance if it exists
                    record_data = {
                        "id": result["id"],
                        "content": result["content"],
                        "embedding": {"data": result["embedding"]},
                    }

                    # Add timestamps if they exist in the result
                    if "created_at" in result:
                        record_data["created_at"] = result["created_at"]

                    if "updated_at" in result:
                        record_data["updated_at"] = result["updated_at"]

                    # Only add distance if it exists in the result
                    if "distance" in result:
                        record_data["distance"] = result["distance"]

                    response_record = KnowledgeVectorQueryResponseRecord(**record_data)
                    response_records.append(response_record)

                self.logger.info(f"Successfully queried {len(response_records)} records for request: {request_id}")
                return KnowledgeVectorQueryResponse(
                    request_id=request_id,
                    status=ResponseStatus.SUCCESS,
                    message=f"Successfully queried {len(response_records)} records",
                    records=response_records,
                )
            else:
                self.logger.info(f"No records found for request: {request_id}")
                return KnowledgeVectorQueryResponse(
                    request_id=request_id, status=ResponseStatus.SUCCESS, message="No records found", records=[]
                )

        except Exception as e:
            self.logger.error(f"Exception in query_vector_store for request {request_id}: {str(e)}")
            return KnowledgeVectorQueryResponse(
                request_id=request_id, status=ResponseStatus.FAILURE, message=f"Internal error: {str(e)}"
            )

    def delete_vector_store(self, data: KnowledgeVectorDeleteRequest) -> KnowledgeVectorDeleteResponse:
        """
        Delete a vector record from the vector store.

        Args:
            data: Delete request containing record ID and delete options

        Returns:
            KnowledgeVectorDeleteResponse: Response indicating success or failure
        """
        request_id = data.request_id
        self.logger.info(
            f"Deleting vector: request_id='{request_id}' wksp_id='{data.wksp_id}' mas_id='{data.mas_id}' id='{data.id}' soft_delete={data.soft_delete}"
        )

        try:
            # Check if workspace exists
            if not self._workspace_exists(data.wksp_id):
                self.logger.warning(f"Workspace {data.wksp_id} not found for request: {request_id}")
                return KnowledgeVectorDeleteResponse(
                    request_id=request_id,
                    status=ResponseStatus.NOT_FOUND,
                    message=f"Workspace {data.wksp_id} not found",
                )

            # Get schema name for the workspace
            schema_name = self.get_schema_name(data.wksp_id)

            # Initialize database connection
            db = VectorDB()

            # Perform delete operation
            delete_success = db.delete_vector(schema_name=schema_name, vector_id=data.id, soft_delete=data.soft_delete)

            if delete_success:
                delete_type = "soft deleted" if data.soft_delete else "permanently deleted"
                self.logger.info(f"Successfully {delete_type} vector {data.id} for request: {request_id}")
                return KnowledgeVectorDeleteResponse(
                    request_id=request_id,
                    status=ResponseStatus.SUCCESS,
                    message=f"Successfully {delete_type} vector {data.id}",
                )
            else:
                self.logger.warning(f"Vector {data.id} not found for deletion in request: {request_id}")
                return KnowledgeVectorDeleteResponse(
                    request_id=request_id, status=ResponseStatus.NOT_FOUND, message=f"Vector {data.id} not found"
                )

        except Exception as e:
            self.logger.error(f"Exception in delete_vector_store for request {request_id}: {str(e)}")
            return KnowledgeVectorDeleteResponse(
                request_id=request_id, status=ResponseStatus.FAILURE, message=f"Internal error: {str(e)}"
            )

    def internal_delete_vector_store(
        self, store_id: str, data: KnowledgeVectorStoreOnboardDeleteRequest
    ) -> KnowledgeVectorStoreOnboardDeleteResponse:
        """
        Internal method to hard delete a vector store schema and all associated data.

        Args:
            store_id: Store ID to delete (used as workspace ID)
            data: Delete request data

        Returns:
            KnowledgeVectorStoreOnboardDeleteResponse: Response indicating success or failure
        """
        request_id = data.request_id
        self.logger.info(f"Internal delete vector store: request_id='{request_id}' store_id='{store_id}'")

        try:
            # Get schema name for the store
            schema_name = self.get_schema_name(store_id)

            # Initialize database connection
            db = VectorDB()

            # Check if schema exists before attempting delete
            schema_info = db.get_schema(schema_name)
            if schema_info is None:
                self.logger.warning(f"Schema {schema_name} not found for store {store_id} in request: {request_id}")
                return KnowledgeVectorStoreOnboardDeleteResponse(
                    request_id=request_id, status=ResponseStatus.NOT_FOUND, message=f"Store {store_id} not found"
                )

            # Perform hard delete of schema (this will cascade delete all tables)
            delete_success = db.delete_schema(schema_name)

            if delete_success:
                self.logger.info(
                    f"Successfully hard deleted schema {schema_name} for store {store_id} in request: {request_id}"
                )
                return KnowledgeVectorStoreOnboardDeleteResponse(
                    request_id=request_id,
                    status=ResponseStatus.SUCCESS,
                    message=f"Successfully deleted store {store_id} and all associated data",
                )
            else:
                self.logger.error(
                    f"Failed to delete schema {schema_name} for store {store_id} in request: {request_id}"
                )
                return KnowledgeVectorStoreOnboardDeleteResponse(
                    request_id=request_id, status=ResponseStatus.FAILURE, message=f"Failed to delete store {store_id}"
                )

        except Exception as e:
            self.logger.error(f"Exception in internal_delete_vector_store for request {request_id}: {str(e)}")
            return KnowledgeVectorStoreOnboardDeleteResponse(
                request_id=request_id, status=ResponseStatus.FAILURE, message=f"Internal error: {str(e)}"
            )


# Global service instance
knowledge_vector_service = KnowledgeVectorService()
