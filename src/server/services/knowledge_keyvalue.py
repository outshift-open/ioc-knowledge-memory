# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

import logging
from typing import Dict, Any

from server.database.keyvalue_db.postgres.src.db import (
    KeyValueDB,
    KeyValueDBStoreRequest,
    KeyValueDBQueryRequest,
    KeyValueDBDeleteRequest,
)
from server.schemas.knowledge_keyvalue import (
    ScopeType,
    KnowledgeKVPStoreRequest,
    KnowledgeKVPStoreResponse,
    KnowledgeKVPStoreOnboardRequest,
    KnowledgeKVPStoreOnboardResponse,
    KnowledgeKVPStoreOnboardDeleteRequest,
    KnowledgeKVPQueryRequest,
    KnowledgeKVPQueryResponse,
    KnowledgeKVPDeleteRequest,
    KnowledgeKVPDeleteResponse,
    KnowledgeKVPRecord,
    ResponseStatus,
    QUERY_TYPE_GET_BY_KEY,
)

MAS_SCHEMA_PREFIX = "kvp_mas_"
CE_SCHEMA_PREFIX = "kvp_ce_"


class KnowledgeKVPService:
    """Service layer for Knowledge Key-Value Pair business logic"""

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

    def get_schema_name(self, store_id: str, scope_type: ScopeType = ScopeType.MAS) -> str:
        """
        Helper method to generate the schema name for a store.

        Args:
            store_id: Store ID (MAS ID or CE ID)
            scope_type: Type of scope (MAS or CE)

        Returns:
            str: Normalized schema name with appropriate prefix
        """
        if scope_type == ScopeType.MAS:
            return MAS_SCHEMA_PREFIX + self._normalize_id(store_id)
        else:  # CE scope
            return CE_SCHEMA_PREFIX + self._normalize_id(store_id)

    def _store_exists(self, store_id: str, scope_type: ScopeType = ScopeType.MAS) -> bool:
        """
        Check if a KVP store exists by verifying its schema exists.

        Args:
            store_id: Store ID to check
            scope_type: Type of scope (MAS or CE)

        Returns:
            bool: True if KVP store exists, False otherwise
        """
        try:
            db = KeyValueDB()
            schema_name = self.get_schema_name(store_id, scope_type)
            schema_info = db.get_schema(schema_name)
            return schema_info is not None
        except Exception as e:
            self.logger.error(f"Error checking KVP store existence for {store_id}: {str(e)}")
            return False

    def onboard(self, store_id: str, data: KnowledgeKVPStoreOnboardRequest) -> KnowledgeKVPStoreOnboardResponse:
        """
        Onboard a KVP store by creating the necessary schema and tables.
        Uses scope type from request body.

        Args:
            store_id: Store ID (MAS ID or CE ID)
            data: Onboard request data

        Returns:
            KnowledgeKVPStoreOnboardResponse: Response indicating success or failure
        """
        request_id = data.request_id
        scope_type = data.scope
        self.logger.info(f"input request: {data}, store_id: {store_id}, scope_type: {scope_type}")

        try:
            db = KeyValueDB()

            # Normalize schema name using store ID and create schema and table using onboard method
            schema_name = self.get_schema_name(store_id, scope_type)
            onboard_success = db.onboard(schema_name, scope_type)

            if onboard_success:
                self.logger.info(
                    f"Successfully created KVP store container for store: {store_id} (scope: {scope_type})"
                )
                return KnowledgeKVPStoreOnboardResponse(
                    request_id=request_id,
                    status=ResponseStatus.SUCCESS,
                    message=f"Successfully onboarded KVP store {store_id}",
                )
            else:
                self.logger.error(f"Failed to create KVP store container for store: {store_id} (scope: {scope_type})")
                return KnowledgeKVPStoreOnboardResponse(
                    request_id=request_id,
                    status=ResponseStatus.FAILURE,
                    message=f"Failed to onboard KVP store {store_id}",
                )

        except Exception as e:
            self.logger.error(f"Exception in onboard for request {request_id}: {str(e)}")
            return KnowledgeKVPStoreOnboardResponse(
                request_id=request_id, status=ResponseStatus.FAILURE, message=f"Internal error: {str(e)}"
            )

    def create_kvp_store(self, data: KnowledgeKVPStoreRequest) -> KnowledgeKVPStoreResponse:
        """
        Store/upsert key-value pairs in the KVP store.
        Uses scope type from request body.

        Args:
            data: KVP store request data

        Returns:
            KnowledgeKVPStoreResponse: Response indicating success or failure
        """
        request_id = data.request_id
        self.logger.debug(f"Upserting KVP store: {data}")

        try:
            # Use scope type from request and determine store ID accordingly
            scope_type = data.scope
            if scope_type == ScopeType.MAS:
                store_id = data.mas_id
            else:  # CE scope
                store_id = data.ce_id

            # Check if store exists
            if not self._store_exists(store_id, scope_type):
                self.logger.warning(f"KVP store {store_id} not found for request: {request_id}")
                return KnowledgeKVPStoreResponse(
                    request_id=request_id,
                    status=ResponseStatus.NOT_FOUND,
                    message=f"KVP store {store_id} not found",
                )

            db = KeyValueDB()

            # Convert to KeyValueDBStoreRequest and save records
            from uuid import uuid4

            # Pass UUIDs directly to database layer (already validated in schema)
            kvp_request = KeyValueDBStoreRequest(
                schema_name=self.get_schema_name(store_id, scope_type),
                scope_type=scope_type,
                wksp_id=data.wksp_id,
                mas_id=data.mas_id,
                agent_id=data.agent_id,
                ce_id=data.ce_id,
                records=[
                    {
                        "id": str(uuid4()),  # Generate unique UUID for each record
                        "key": record.key,
                        "value": record.value,
                    }
                    for record in data.records
                ],
            )

            save_success = db.save(kvp_request)

            if save_success:
                self.logger.info(f"Successfully saved KVP records for request: {request_id}")
                return KnowledgeKVPStoreResponse(
                    request_id=request_id,
                    status=ResponseStatus.SUCCESS,
                    message=f"Successfully saved {len(data.records)} KVP records",
                )
            else:
                self.logger.error(f"Failed to save KVP records for request: {request_id}")
                return KnowledgeKVPStoreResponse(
                    request_id=request_id, status=ResponseStatus.FAILURE, message="Failed to save KVP records"
                )

        except Exception as e:
            self.logger.error(f"Exception in create_kvp_store for request {request_id}: {str(e)}")
            return KnowledgeKVPStoreResponse(
                request_id=request_id, status=ResponseStatus.FAILURE, message=f"Internal error: {str(e)}"
            )

    def query_kvp_store(self, data: KnowledgeKVPQueryRequest) -> KnowledgeKVPQueryResponse:
        """
        Query key-value pairs from the KVP store.
        Uses scope type from request body.

        Args:
            data: KVP query request data

        Returns:
            KnowledgeKVPQueryResponse: Response with query results
        """
        request_id = data.request_id
        self.logger.debug(f"Querying KVP store: {data}")

        try:
            # Use scope type from request and determine store ID accordingly
            scope_type = data.scope
            if scope_type == ScopeType.MAS:
                store_id = data.mas_id
            else:  # CE scope
                store_id = data.ce_id

            # Check if store exists
            if not self._store_exists(store_id, scope_type):
                self.logger.warning(f"KVP store {store_id} not found for request: {request_id}")
                return KnowledgeKVPQueryResponse(
                    request_id=request_id,
                    status=ResponseStatus.NOT_FOUND,
                    message=f"KVP store {store_id} not found",
                )

            # Validate query criteria
            if data.query_criteria.query_type != QUERY_TYPE_GET_BY_KEY:
                return KnowledgeKVPQueryResponse(
                    request_id=request_id,
                    status=ResponseStatus.VALIDATION_ERROR,
                    message=f"Unsupported query type: {data.query_criteria.query_type}",
                )

            if not data.query_criteria.key:
                return KnowledgeKVPQueryResponse(
                    request_id=request_id,
                    status=ResponseStatus.VALIDATION_ERROR,
                    message="Key is required for get_by_key query type",
                )

            db = KeyValueDB()

            # Convert to KeyValueDBQueryRequest and execute query
            # Pass UUIDs directly to database layer (already validated in schema)
            kvp_query_request = KeyValueDBQueryRequest(
                schema_name=self.get_schema_name(store_id, scope_type),
                scope_type=scope_type,
                key=data.query_criteria.key,
                wksp_id=data.wksp_id,
                mas_id=data.mas_id,
                agent_id=data.agent_id,
                ce_id=data.ce_id,
                limit=data.query_criteria.limit,
            )

            query_results = db.query(kvp_query_request)

            # Convert results to KnowledgeKVPRecord format
            records = []
            for result in query_results:
                record = KnowledgeKVPRecord(
                    key=result["key"],
                    value=result["value"],
                    created_at=result.get("created_at"),
                    updated_at=result.get("updated_at"),
                )
                records.append(record)

            self.logger.info(f"Successfully queried {len(records)} KVP records for request: {request_id}")
            return KnowledgeKVPQueryResponse(
                request_id=request_id,
                status=ResponseStatus.SUCCESS,
                message=f"Query executed successfully, found {len(records)} records",
                records=records,
            )

        except Exception as e:
            self.logger.error(f"Exception in query_kvp_store for request {request_id}: {str(e)}")
            return KnowledgeKVPQueryResponse(
                request_id=request_id, status=ResponseStatus.FAILURE, message=f"Internal error: {str(e)}"
            )

    def delete_kvp_store(self, data: KnowledgeKVPDeleteRequest) -> KnowledgeKVPDeleteResponse:
        """
        Delete key-value pairs from the KVP store.
        Uses scope type from request body.

        Args:
            data: KVP delete request data

        Returns:
            KnowledgeKVPDeleteResponse: Response indicating success or failure
        """
        request_id = data.request_id
        self.logger.debug(f"Deleting from KVP store: {data}")

        try:
            # Use scope type from request and determine store ID accordingly
            scope_type = data.scope
            if scope_type == ScopeType.MAS:
                store_id = data.mas_id
            else:  # CE scope
                store_id = data.ce_id

            # Check if store exists
            if not self._store_exists(store_id, scope_type):
                self.logger.warning(f"KVP store {store_id} not found for request: {request_id}")
                return KnowledgeKVPDeleteResponse(
                    request_id=request_id,
                    status=ResponseStatus.NOT_FOUND,
                    message=f"KVP store {store_id} not found",
                )

            db = KeyValueDB()

            # Execute delete operation using KeyValueDBDeleteRequest
            # Pass UUIDs directly to database layer (already validated in schema)
            delete_request = KeyValueDBDeleteRequest(
                schema_name=self.get_schema_name(store_id, scope_type),
                scope_type=scope_type,
                key=data.key,
                wksp_id=data.wksp_id,
                mas_id=data.mas_id,
                agent_id=data.agent_id,
                ce_id=data.ce_id,
                soft_delete=data.soft_delete,
            )
            deleted_count = db.delete(delete_request)

            if deleted_count > 0:
                delete_type = "soft deleted" if data.soft_delete else "permanently deleted"
                self.logger.info(f"Successfully {delete_type} {deleted_count} KVP records for request: {request_id}")
                return KnowledgeKVPDeleteResponse(
                    request_id=request_id,
                    status=ResponseStatus.SUCCESS,
                    message=f"Successfully {delete_type} {deleted_count} KVP records",
                )
            else:
                self.logger.warning(f"No KVP records found to delete for request: {request_id}")
                return KnowledgeKVPDeleteResponse(
                    request_id=request_id,
                    status=ResponseStatus.NOT_FOUND,
                    message="No KVP records found matching the specified key and filters",
                )

        except Exception as e:
            self.logger.error(f"Exception in delete_kvp_store for request {request_id}: {str(e)}")
            return KnowledgeKVPDeleteResponse(
                request_id=request_id, status=ResponseStatus.FAILURE, message=f"Internal error: {str(e)}"
            )
