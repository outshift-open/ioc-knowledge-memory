# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

import json
import logging
from typing import List, Dict, Optional, Any, Union

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from server.database.connection import ConnectDB
from server.schemas.knowledge_keyvalue import ScopeType

TABLE_NAME = "key_value_entities"


class KeyValueDBStoreRequest(BaseModel):
    """
    Key-value database store request.
    """

    model_config = ConfigDict(exclude_none=True)

    schema_name: str
    scope_type: ScopeType
    wksp_id: Optional[str] = None
    mas_id: Optional[str] = None
    agent_id: Optional[str] = None
    ce_id: Optional[str] = None
    records: List[Dict[str, Any]]


class KeyValueDBQueryRequest(BaseModel):
    """Key-value database query request."""

    model_config = ConfigDict(exclude_none=True)

    schema_name: str
    scope_type: ScopeType
    key: Dict[str, Any] = Field(..., description="JSON key to query for")
    wksp_id: Optional[str] = Field(default=None, description="Workspace ID for filtering")
    mas_id: Optional[str] = Field(default=None, description="MAS ID for filtering")
    agent_id: Optional[str] = Field(default=None, description="Optional agent ID for agent-scoped filtering")
    ce_id: Optional[str] = Field(default=None, description="Cognition Engine ID for filtering")
    limit: Optional[int] = Field(default=None, description="Maximum number of results to return")


class KeyValueDBDeleteRequest(BaseModel):
    """Key-value database delete request."""

    model_config = ConfigDict(exclude_none=True)

    schema_name: str
    scope_type: ScopeType
    key: Dict[str, Any] = Field(..., description="JSON key to delete records for")
    wksp_id: Optional[str] = Field(default=None, description="Workspace ID for filtering")
    mas_id: Optional[str] = Field(default=None, description="MAS ID for filtering")
    agent_id: Optional[str] = Field(default=None, description="Optional agent ID for agent-scoped filtering")
    ce_id: Optional[str] = Field(default=None, description="Cognition Engine ID for filtering")
    soft_delete: bool = Field(default=True, description="If True, perform soft delete; if False, perform hard delete")


class KeyValueDB:
    """
    Key-value database operations using PostgreSQL with JSONB.
    Uses ConnectDB singleton for database connections.
    Supports both MAS-scoped and Cognition Engine-scoped key-value stores.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connect_db = ConnectDB()

    def _build_filter_clauses(self, filters: Dict[str, Any]) -> tuple[str, Dict[str, Any]]:
        """
        Helper method to build filter clauses and parameters for queries.

        Args:
            filters: Dictionary mapping filter names to their values and column mappings
                    Format: {filter_name: {"value": value, "column": column_name}}

        Returns:
            tuple: (filter_clauses_string, parameters_dict)
        """
        filter_clauses = ""
        params = {}

        for filter_name, filter_config in filters.items():
            value = filter_config.get("value")
            column = filter_config.get("column")

            if value is not None:
                filter_clauses += f" AND {column} = :{filter_name}"
                params[filter_name] = value

        return filter_clauses, params

    def create_schema(self, schema_name: str) -> bool:
        """Create a new schema in the database if it does not exist.

        Args:
            schema_name: Name of the schema to create

        Returns:
            bool: True if schema was created successfully or already exists

        Raises:
            RuntimeError: If there's an error creating the schema
        """
        try:
            with self.connect_db.engine.begin() as conn:
                # Check if schema already exists
                result = conn.execute(
                    text("SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = :name"),
                    {"name": schema_name},
                )
                if result.scalar() > 0:
                    self.logger.warning(f"Schema '{schema_name}' already exists")
                    return True

                # Create the schema
                conn.execute(text(f'CREATE SCHEMA "{schema_name}"'))
                self.logger.info(f"Created schema '{schema_name}'")

                return True

        except SQLAlchemyError as e:
            raise RuntimeError(f"Failed to create schema '{schema_name}': {str(e)}")

    def delete_schema(self, schema_name: str) -> bool:
        """Delete a schema from the database.

        Args:
            schema_name: Name of the schema to delete

        Returns:
            bool: True if schema was deleted successfully

        Raises:
            RuntimeError: If there's an error deleting the schema
        """
        try:
            with self.connect_db.engine.begin() as conn:
                # Check if schema exists
                result = conn.execute(
                    text("SELECT COUNT(*) FROM information_schema.schemata WHERE schema_name = :name"),
                    {"name": schema_name},
                )
                if result.scalar() == 0:
                    self.logger.warning(f"Schema '{schema_name}' does not exist")
                    return False

                # Delete the schema (CASCADE will drop all objects in it)
                conn.execute(text(f'DROP SCHEMA "{schema_name}" CASCADE'))
                self.logger.info(f"Deleted schema '{schema_name}'")
                return True

        except SQLAlchemyError as e:
            raise RuntimeError(f"Failed to delete schema '{schema_name}': {str(e)}")

    def get_schema(self, schema_name: str) -> dict | None:
        """Get information about a specific schema.

        Args:
            schema_name: Name of the schema to retrieve information for

        Returns:
            dict: Schema information if it exists, None if it doesn't exist
                  Contains: name, owner

        Raises:
            RuntimeError: If there's an error retrieving the schema
        """
        try:
            with self.connect_db.engine.connect() as conn:
                result = conn.execute(
                    text(
                        """
                        SELECT schema_name, schema_owner
                        FROM information_schema.schemata 
                        WHERE schema_name = :name
                        """
                    ),
                    {"name": schema_name},
                ).fetchone()

                if not result:
                    return None

                return {
                    "name": result[0],
                    "owner": result[1],
                }

        except SQLAlchemyError as e:
            raise RuntimeError(f"Failed to get schema '{schema_name}': {str(e)}")

    def onboard(self, schema_name: str, scope_type: ScopeType) -> bool:
        """Create schema and key_value_entities table for key-value storage.

        Args:
            schema_name: Name of the schema to create (e.g., kvp_mas_<normalized_mas_id> or kvp_ce_<normalized_ce_id>)
            scope_type: Type of scope (MAS or CE) to determine table structure

        Returns:
            bool: True if successful, False otherwise

        Raises:
            RuntimeError: If schema or table creation fails
        """
        try:
            # Use transaction with automatic rollback on failure
            with self.connect_db.engine.begin() as conn:
                # Create schema if not exists
                conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
                self.logger.info(f"Ensured schema '{schema_name}' exists")

                # Create the key_value_entities table based on scope type
                if scope_type == ScopeType.MAS:
                    # MAS Scoped Key Value Store
                    create_table_query = f"""
                        CREATE TABLE IF NOT EXISTS "{schema_name}"."{TABLE_NAME}" (
                            id UUID PRIMARY KEY,
                            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
                            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
                            created_by VARCHAR DEFAULT current_user,
                            updated_by VARCHAR DEFAULT current_user,
                            deleted_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NULL,
                            deleted_by VARCHAR DEFAULT current_user,
                            wksp_uuid UUID NOT NULL,
                            mas_uuid UUID NOT NULL,
                            agent_id VARCHAR NULL,
                            key JSONB NOT NULL,
                            value JSONB NOT NULL
                        )
                    """
                elif scope_type == ScopeType.CE:
                    # Cognition Engine Scoped Key Value Store
                    create_table_query = f"""
                        CREATE TABLE IF NOT EXISTS "{schema_name}"."{TABLE_NAME}" (
                            id UUID PRIMARY KEY,
                            created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
                            updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now(),
                            created_by VARCHAR DEFAULT current_user,
                            updated_by VARCHAR DEFAULT current_user,
                            deleted_at TIMESTAMP WITHOUT TIME ZONE DEFAULT NULL,
                            deleted_by VARCHAR DEFAULT current_user,
                            wksp_uuid UUID NULL,
                            mas_uuid UUID NULL,
                            agent_id VARCHAR NULL,
                            ce_id VARCHAR NOT NULL,
                            key JSONB NOT NULL,
                            value JSONB NOT NULL
                        )
                    """
                else:
                    raise ValueError(f"Unsupported scope type: {scope_type}")

                conn.execute(text(create_table_query))
                self.logger.info(
                    f"Ensured table '{TABLE_NAME}' exists in schema '{schema_name}' for scope '{scope_type}'"
                )

                # Create indexes for better query performance
                if scope_type == ScopeType.MAS:
                    # Indexes for MAS-scoped store
                    indexes = [
                        ("wksp_uuid_idx", "wksp_uuid", "btree"),
                        ("mas_uuid_idx", "mas_uuid", "btree"),
                        ("agent_id_idx", "agent_id", "btree"),
                        ("key_gin_idx", "key", "gin"),
                        ("deleted_at_idx", "deleted_at", "btree"),
                    ]
                else:  # CE scope
                    # Indexes for CE-scoped store
                    indexes = [
                        ("wksp_uuid_idx", "wksp_uuid", "btree"),
                        ("mas_uuid_idx", "mas_uuid", "btree"),
                        ("agent_id_idx", "agent_id", "btree"),
                        ("ce_id_idx", "ce_id", "btree"),
                        ("key_gin_idx", "key", "gin"),
                        ("deleted_at_idx", "deleted_at", "btree"),
                    ]

                for idx_name, idx_column, idx_method in indexes:
                    if idx_method == "gin":
                        create_index_query = f"""
                            CREATE INDEX IF NOT EXISTS {TABLE_NAME}_{idx_name}
                            ON "{schema_name}".{TABLE_NAME} USING gin ({idx_column})
                        """
                    else:
                        create_index_query = f"""
                            CREATE INDEX IF NOT EXISTS {TABLE_NAME}_{idx_name}
                            ON "{schema_name}".{TABLE_NAME} ({idx_column})
                        """
                    conn.execute(text(create_index_query))
                    self.logger.info(f"Ensured {idx_method} index exists on {idx_column} in schema '{schema_name}'")

                # Create unique constraint for key-based conflict resolution
                if scope_type == ScopeType.MAS:
                    # Unique constraint for MAS scope: wksp_uuid + mas_uuid + agent_id + key
                    create_unique_constraint_query = f"""
                        CREATE UNIQUE INDEX IF NOT EXISTS {TABLE_NAME}_unique_key_mas_idx
                        ON "{schema_name}".{TABLE_NAME} (wksp_uuid, mas_uuid, COALESCE(agent_id, ''), key)
                    """
                else:  # CE scope
                    # Unique constraint for CE scope: wksp_uuid + mas_uuid + agent_id + ce_id + key
                    create_unique_constraint_query = f"""
                        CREATE UNIQUE INDEX IF NOT EXISTS {TABLE_NAME}_unique_key_ce_idx
                        ON "{schema_name}".{TABLE_NAME} (COALESCE(wksp_uuid::text, ''), COALESCE(mas_uuid::text, ''), COALESCE(agent_id, ''), ce_id, key)
                    """

                conn.execute(text(create_unique_constraint_query))
                self.logger.info(
                    f"Ensured unique constraint exists for key-based conflict resolution in schema '{schema_name}'"
                )

                # If we reach here, all operations were successful
                self.logger.info(
                    f"Successfully onboarded schema '{schema_name}' with {TABLE_NAME} table for scope '{scope_type}'"
                )
                return True

        except SQLAlchemyError as e:
            self.logger.error(f"Failed to onboard schema '{schema_name}': {str(e)}")
            raise RuntimeError(f"Failed to onboard schema '{schema_name}': {str(e)}")

    def save(self, request: KeyValueDBStoreRequest) -> bool:
        """Save key-value records with upsert functionality.

        Args:
            request: KeyValueDBStoreRequest containing key-value records

        Returns:
            bool: True if save was successful

        Raises:
            RuntimeError: If there's an error saving the key-value pairs
        """
        try:
            table_name = f'"{request.schema_name}"."{TABLE_NAME}"'

            # Use transaction with automatic rollback on failure
            with self.connect_db.engine.begin() as conn:
                if not request.records:
                    self.logger.warning("No records to save")
                    return True

                try:
                    # Process records individually within the transaction
                    for record in request.records:
                        record_id = record.get("id")
                        key_data = record.get("key")
                        value_data = record.get("value")

                        if not record_id or not key_data or not value_data:
                            raise ValueError("Each record must have 'id', 'key', and 'value' fields")

                        # Convert key to JSON string
                        key_json = json.dumps(key_data)

                        # Build upsert query and parameters based on scope type
                        if request.scope_type == ScopeType.MAS:
                            # For MAS scope, conflict resolution based on key + scope identifiers
                            upsert_query = f"""
                                INSERT INTO {table_name} (id, wksp_uuid, mas_uuid, agent_id, key, value, created_at)
                                VALUES (:id, :wksp_uuid, :mas_uuid, :agent_id, :key, :value, now())
                                ON CONFLICT (wksp_uuid, mas_uuid, COALESCE(agent_id, ''), key) DO UPDATE SET
                                    id = EXCLUDED.id,
                                    value = EXCLUDED.value,
                                    updated_at = now(),
                                    updated_by = current_user
                            """
                            params = {
                                "id": record_id,
                                "wksp_uuid": request.wksp_id,
                                "mas_uuid": request.mas_id,
                                "agent_id": request.agent_id,
                                "key": key_json,
                                "value": json.dumps(value_data),
                            }
                        else:  # CE scope
                            # For CE scope, conflict resolution based on key + scope identifiers
                            upsert_query = f"""
                                INSERT INTO {table_name} (id, wksp_uuid, mas_uuid, agent_id, ce_id, key, value, created_at)
                                VALUES (:id, :wksp_uuid, :mas_uuid, :agent_id, :ce_id, :key, :value, now())
                                ON CONFLICT (COALESCE(wksp_uuid::text, ''), COALESCE(mas_uuid::text, ''), COALESCE(agent_id, ''), ce_id, key) DO UPDATE SET
                                    id = EXCLUDED.id,
                                    value = EXCLUDED.value,
                                    updated_at = now(),
                                    updated_by = current_user
                            """
                            params = {
                                "id": record_id,
                                "wksp_uuid": request.wksp_id,
                                "mas_uuid": request.mas_id,
                                "agent_id": request.agent_id,
                                "ce_id": request.ce_id,
                                "key": key_json,
                                "value": json.dumps(value_data),
                            }

                        conn.execute(text(upsert_query), params)

                    # If we reach here, all records were processed successfully
                    self.logger.info(f"Successfully saved {len(request.records)} key-value records to {table_name}")
                    return True

                except Exception as e:
                    # Transaction will automatically rollback due to context manager
                    self.logger.error(f"Failed to save record, transaction rolled back: {str(e)}")
                    raise

        except SQLAlchemyError as e:
            raise RuntimeError(f"Failed to save key-value pairs: {str(e)}")

    def query(self, request: KeyValueDBQueryRequest) -> List[Dict]:
        """
        Query key-value pairs from the database based on the provided key.

        Args:
            request: KeyValueDBQueryRequest containing all query parameters

        Returns:
            List of dictionaries containing query results, or empty list if no results

        Raises:
            RuntimeError: If there's an error executing the query
        """
        try:
            table_name = f'"{request.schema_name}"."{TABLE_NAME}"'

            with self.connect_db.engine.begin() as conn:
                # Build base query with key matching
                key_json = json.dumps(request.key)

                if request.scope_type == ScopeType.MAS:
                    # MAS-scoped query
                    base_query = f"""
                        SELECT id, key, value, wksp_uuid, mas_uuid, agent_id,
                               EXTRACT(EPOCH FROM created_at) as created_at,
                               EXTRACT(EPOCH FROM updated_at) as updated_at
                        FROM {table_name}
                        WHERE key = :key AND deleted_at IS NULL
                    """

                    # Build filters for MAS scope
                    filters = {
                        "wksp_uuid": {"value": request.wksp_id, "column": "wksp_uuid"},
                        "mas_uuid": {"value": request.mas_id, "column": "mas_uuid"},
                        "agent_id": {"value": request.agent_id, "column": "agent_id"},
                    }

                else:  # CE scope
                    # CE-scoped query
                    base_query = f"""
                        SELECT id, key, value, wksp_uuid, mas_uuid, agent_id, ce_id,
                               EXTRACT(EPOCH FROM created_at) as created_at,
                               EXTRACT(EPOCH FROM updated_at) as updated_at
                        FROM {table_name}
                        WHERE key = :key AND deleted_at IS NULL
                    """

                    # Build filters for CE scope
                    filters = {
                        "wksp_uuid": {"value": request.wksp_id, "column": "wksp_uuid"},
                        "mas_uuid": {"value": request.mas_id, "column": "mas_uuid"},
                        "ce_id": {"value": request.ce_id, "column": "ce_id"},
                        "agent_id": {"value": request.agent_id, "column": "agent_id"},
                    }

                # Apply filters using helper method
                filter_clauses, filter_params = self._build_filter_clauses(filters)
                base_query += filter_clauses

                # Combine all parameters
                params = {"key": key_json}
                params.update(filter_params)

                # Add ordering and limit
                base_query += " ORDER BY created_at DESC"
                if request.limit:
                    base_query += f" LIMIT {request.limit}"

                result = conn.execute(text(base_query), params)

                # Convert results to list of dictionaries
                rows = result.fetchall()
                if not rows:
                    return []

                results = []
                for row in rows:
                    # Create result dictionary
                    result_dict = {
                        "id": str(row.id),  # Convert UUID to string
                        "key": row.key,
                        "value": row.value,
                    }

                    # Add scope-specific fields
                    if request.scope_type == ScopeType.MAS:
                        result_dict.update(
                            {
                                "wksp_uuid": str(row.wksp_uuid) if row.wksp_uuid else None,
                                "mas_uuid": str(row.mas_uuid) if row.mas_uuid else None,
                                "agent_id": row.agent_id,
                            }
                        )
                    else:  # CE scope
                        result_dict.update(
                            {
                                "wksp_uuid": str(row.wksp_uuid) if row.wksp_uuid else None,
                                "mas_uuid": str(row.mas_uuid) if row.mas_uuid else None,
                                "agent_id": row.agent_id,
                                "ce_id": row.ce_id,
                            }
                        )

                    # Add timestamps in epoch format
                    created_at = getattr(row, "created_at", None)
                    if created_at is not None:
                        result_dict["created_at"] = int(created_at)

                    updated_at = getattr(row, "updated_at", None)
                    if updated_at is not None:
                        result_dict["updated_at"] = int(updated_at)

                    results.append(result_dict)

                self.logger.info(f"Successfully queried {len(results)} records from {table_name}")
                return results

        except SQLAlchemyError as e:
            self.logger.error(f"Failed to query key-value pairs: {str(e)}")
            raise RuntimeError(f"Failed to query key-value pairs: {str(e)}")

    def delete(self, request: KeyValueDBDeleteRequest) -> int:
        """
        Delete key-value records by key.

        Args:
            request: KeyValueDBDeleteRequest containing delete parameters

        Returns:
            int: Number of deleted records

        Raises:
            RuntimeError: If there's an error executing the delete operation
        """
        try:
            table_name = f'"{request.schema_name}"."{TABLE_NAME}"'
            key_json = json.dumps(request.key)

            with self.connect_db.engine.begin() as conn:
                # Build base WHERE clause with key matching
                base_where_clause = "WHERE key = :key AND deleted_at IS NULL"

                # Build scope-specific filters using helper method (same as query method)
                if request.scope_type == ScopeType.MAS:
                    filters = {
                        "wksp_uuid": {"value": request.wksp_id, "column": "wksp_uuid"},
                        "mas_uuid": {"value": request.mas_id, "column": "mas_uuid"},
                        "agent_id": {"value": request.agent_id, "column": "agent_id"},
                    }
                else:  # CE scope
                    filters = {
                        "wksp_uuid": {"value": request.wksp_id, "column": "wksp_uuid"},
                        "mas_uuid": {"value": request.mas_id, "column": "mas_uuid"},
                        "ce_id": {"value": request.ce_id, "column": "ce_id"},
                        "agent_id": {"value": request.agent_id, "column": "agent_id"},
                    }

                # Apply filters using helper method
                filter_clauses, filter_params = self._build_filter_clauses(filters)
                base_where_clause += filter_clauses

                # Combine all parameters
                params = {"key": key_json}
                params.update(filter_params)

                if request.soft_delete:
                    # Soft delete: Update deleted_at and deleted_by fields
                    query = f"""
                        UPDATE {table_name}
                        SET deleted_at = now(), deleted_by = current_user, updated_at = now(), updated_by = current_user
                        {base_where_clause}
                    """
                    self.logger.info(f"Performing soft delete by key in {table_name} (scope={request.scope_type})")
                else:
                    # Hard delete: Permanently remove the records (remove deleted_at filter for hard delete)
                    hard_delete_clause = base_where_clause.replace(" AND deleted_at IS NULL", "")
                    query = f"""
                        DELETE FROM {table_name}
                        {hard_delete_clause}
                    """
                    self.logger.info(f"Performing hard delete by key in {table_name} (scope={request.scope_type})")

                result = conn.execute(text(query), params)
                rows_affected = result.rowcount

                delete_type = "soft deleted" if request.soft_delete else "permanently deleted"
                self.logger.info(f"Successfully {delete_type} {rows_affected} key-value records from {table_name}")
                return rows_affected

        except SQLAlchemyError as e:
            self.logger.error(f"Failed to delete key-value records by key: {str(e)}")
            raise RuntimeError(f"Failed to delete key-value records by key: {str(e)}")
