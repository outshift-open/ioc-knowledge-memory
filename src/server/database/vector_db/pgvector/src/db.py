import logging
from typing import List, Dict, Optional

from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from knowledge_memory.server.database.connection import ConnectDB
from knowledge_memory.server.schemas.knowledge_vector import (
    KnowledgeVectorStoreRequestRecord,
    KnowledgeVectorQueryCriteria,
    QUERY_TYPE_INTERNAL_LIST_BY_WKSP_ID,
    QUERY_TYPE_INTERNAL_LIST_BY_MAS_ID,
    QUERY_TYPE_GET_BY_ID,
    QUERY_TYPE_DISTANCE_L2,
    QUERY_TYPE_DISTANCE_COSINE,
    EMBEDDING_VECTOR_SIZE,
)

TABLE_NAME = "document_embeddings"


class VectorDBStoreRequest:
    """
    Vector database store request.
    """

    schema_name: str
    wksp_id: str
    mas_id: str
    records: List[KnowledgeVectorStoreRequestRecord]


class VectorDBQueryRequest(BaseModel):
    """Vector database query request."""

    schema_name: str
    query_criteria: KnowledgeVectorQueryCriteria = Field(..., description="Query criteria")
    mas_id: str = Field(..., description="MAS ID for filtering")
    wksp_id: str = Field(..., description="Workspace ID for filtering")


class VectorDB:
    """
    Vector database operations using pgvector extension.
    Uses ConnectDB singleton for database connections.
    """

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.connect_db = ConnectDB()

    def create_schema(self, schema_name: str) -> bool:
        """create a new schema in the database if it does not exist.

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
                  Contains: name, owner, creation_time (if available)

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

    def onboard(self, schema_name: str) -> bool:
        """Create schema and document_embeddings table for vector storage.

        Args:
            schema_name: Name of the schema to create

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

                # Create the document_embeddings table if not exists
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
                        document_txt VARCHAR NOT NULL,
                        embedding_vector VECTOR({EMBEDDING_VECTOR_SIZE}) NOT NULL
                    )
                """
                conn.execute(text(create_table_query))
                self.logger.info(f"Ensured table 'document_embeddings' exists in schema '{schema_name}'")

                # Create HNSW index for L2 distance if not exists
                create_l2_index_query = f"""
                    CREATE INDEX IF NOT EXISTS document_vector_embedding_l2_idx 
                    ON "{schema_name}".document_embeddings 
                    USING hnsw (embedding_vector vector_l2_ops)
                """
                conn.execute(text(create_l2_index_query))
                self.logger.info(f"Ensured HNSW L2 index exists on embedding_vector in schema '{schema_name}'")

                # Create HNSW index for cosine similarity if not exists
                create_cosine_index_query = f"""
                    CREATE INDEX IF NOT EXISTS document_vector_embedding_cosine_idx 
                    ON "{schema_name}".document_embeddings 
                    USING hnsw (embedding_vector vector_cosine_ops)
                """
                conn.execute(text(create_cosine_index_query))
                self.logger.info(f"Ensured HNSW cosine index exists on embedding_vector in schema '{schema_name}'")

                # Create index on wksp_uuid for better query performance
                create_wksp_index_query = f"""
                    CREATE INDEX IF NOT EXISTS document_embeddings_wksp_uuid_idx 
                    ON "{schema_name}".document_embeddings (wksp_uuid)
                """
                conn.execute(text(create_wksp_index_query))
                self.logger.info(f"Ensured index exists on wksp_uuid in schema '{schema_name}'")

                # Create index on mas_uuid for better query performance
                create_mas_index_query = f"""
                    CREATE INDEX IF NOT EXISTS document_embeddings_mas_uuid_idx 
                    ON "{schema_name}".document_embeddings (mas_uuid)
                """
                conn.execute(text(create_mas_index_query))
                self.logger.info(f"Ensured index exists on mas_uuid in schema '{schema_name}'")

                # Create index on deleted_at for soft delete queries
                create_deleted_at_index_query = f"""
                    CREATE INDEX IF NOT EXISTS document_embeddings_deleted_at_idx 
                    ON "{schema_name}".document_embeddings (deleted_at)
                """
                conn.execute(text(create_deleted_at_index_query))
                self.logger.info(f"Ensured index exists on deleted_at in schema '{schema_name}'")

                # Create index on id for primary key lookups
                create_id_index_query = f"""
                    CREATE INDEX IF NOT EXISTS document_embeddings_id_idx 
                    ON "{schema_name}".document_embeddings (id)
                """
                conn.execute(text(create_id_index_query))
                self.logger.info(f"Ensured index exists on id in schema '{schema_name}'")

                # If we reach here, all operations were successful
                self.logger.info(f"Successfully onboarded schema '{schema_name}' with document_embeddings table")
                return True

        except SQLAlchemyError as e:
            self.logger.error(f"Failed to onboard schema '{schema_name}': {str(e)}")
            raise RuntimeError(f"Failed to onboard schema '{schema_name}': {str(e)}")

    def save(self, request: VectorDBStoreRequest) -> bool:
        """Save vector records with upsert functionality.

        Args:
            request: VectorDBStoreRequest containing workspace ID and vector records

        Returns:
            bool: True if save was successful

        Raises:
            RuntimeError: If there's an error saving the vectors
        """
        try:
            table_name = f'"{request.schema_name}"."{TABLE_NAME}"'

            # Use transaction with automatic rollback on failure
            with self.connect_db.engine.begin() as conn:
                # Prepare the upsert query
                if not request.records:
                    self.logger.warning("No records to save")
                    return True

                try:
                    # Process records individually within the transaction
                    for record in request.records:
                        # Convert embedding data to PostgreSQL array format
                        embedding_str = str(record.embedding.data).replace(" ", "")

                        upsert_query = f"""
                            INSERT INTO {table_name} (id, wksp_uuid, mas_uuid, document_txt, embedding_vector, created_at) 
                            VALUES (:id, :wksp_uuid, :mas_uuid, :document_txt, :embedding_vector, now())
                            ON CONFLICT (id) DO UPDATE SET 
                                wksp_uuid = EXCLUDED.wksp_uuid,
                                mas_uuid = EXCLUDED.mas_uuid,
                                document_txt = EXCLUDED.document_txt,
                                embedding_vector = EXCLUDED.embedding_vector,
                                updated_at = now()
                        """

                        conn.execute(
                            text(upsert_query),
                            {
                                "id": record.id,
                                "wksp_uuid": request.wksp_id,
                                "mas_uuid": request.mas_id,
                                "document_txt": record.content,
                                "embedding_vector": embedding_str,
                            },
                        )

                    # If we reach here, all records were processed successfully
                    self.logger.info(f"Successfully saved {len(request.records)} vector records to {table_name}")
                    return True

                except Exception as e:
                    # Transaction will automatically rollback due to context manager
                    self.logger.error(f"Failed to save record, transaction rolled back: {str(e)}")
                    raise

        except SQLAlchemyError as e:
            raise RuntimeError(f"Failed to save vectors: {str(e)}")

    def query(self, request: VectorDBQueryRequest) -> List[Dict]:
        """
        Query vectors from the database based on the provided criteria.

        Args:
            request: VectorDBQueryRequest containing all query parameters

        Returns:
            List of dictionaries containing query results, or empty list if no results

        Raises:
            RuntimeError: If there's an error executing the query
        """
        try:
            table_name = f'"{request.schema_name}"."{TABLE_NAME}"'

            with self.connect_db.engine.begin() as conn:
                query_type = request.query_criteria.query_type

                if query_type == QUERY_TYPE_INTERNAL_LIST_BY_WKSP_ID:
                    # List all records for workspace
                    query = f"""
                        SELECT id, document_txt as content, embedding_vector as embedding,
                               EXTRACT(EPOCH FROM created_at) as created_at,
                               EXTRACT(EPOCH FROM updated_at) as updated_at
                        FROM {table_name}
                        WHERE wksp_uuid = :wksp_uuid AND deleted_at IS NULL
                        ORDER BY created_at DESC
                    """
                    if request.query_criteria.limit:
                        query += f" LIMIT {request.query_criteria.limit}"

                    result = conn.execute(text(query), {"wksp_uuid": request.wksp_id})

                elif query_type == QUERY_TYPE_INTERNAL_LIST_BY_MAS_ID:
                    # List all records for MAS
                    query = f"""
                        SELECT id, document_txt as content, embedding_vector as embedding,
                               EXTRACT(EPOCH FROM created_at) as created_at,
                               EXTRACT(EPOCH FROM updated_at) as updated_at
                        FROM {table_name}
                        WHERE mas_uuid = :mas_uuid AND deleted_at IS NULL
                        ORDER BY created_at DESC
                    """
                    if request.query_criteria.limit:
                        query += f" LIMIT {request.query_criteria.limit}"

                    result = conn.execute(text(query), {"mas_uuid": request.mas_id})

                elif query_type == QUERY_TYPE_GET_BY_ID:
                    # Get specific record by ID
                    query = f"""
                        SELECT id, document_txt as content, embedding_vector as embedding,
                               EXTRACT(EPOCH FROM created_at) as created_at,
                               EXTRACT(EPOCH FROM updated_at) as updated_at
                        FROM {table_name}
                        WHERE id = :id AND wksp_uuid = :wksp_uuid AND mas_uuid = :mas_uuid AND deleted_at IS NULL
                    """

                    result = conn.execute(
                        text(query),
                        {"id": request.query_criteria.id, "wksp_uuid": request.wksp_id, "mas_uuid": request.mas_id},
                    )

                elif query_type == QUERY_TYPE_DISTANCE_L2:
                    # L2 distance similarity search
                    embedding_str = str(request.query_criteria.embedding.data).replace(" ", "")
                    query = f"""
                        SELECT id, document_txt as content, embedding_vector as embedding,
                               embedding_vector <-> :query_embedding as distance,
                               EXTRACT(EPOCH FROM created_at) as created_at,
                               EXTRACT(EPOCH FROM updated_at) as updated_at
                        FROM {table_name}
                        WHERE wksp_uuid = :wksp_uuid AND mas_uuid = :mas_uuid AND deleted_at IS NULL
                        ORDER BY embedding_vector <-> :query_embedding
                    """
                    if request.query_criteria.limit:
                        query += f" LIMIT {request.query_criteria.limit}"

                    result = conn.execute(
                        text(query),
                        {"query_embedding": embedding_str, "wksp_uuid": request.wksp_id, "mas_uuid": request.mas_id},
                    )

                elif query_type == QUERY_TYPE_DISTANCE_COSINE:
                    # Cosine distance similarity search
                    embedding_str = str(request.query_criteria.embedding.data).replace(" ", "")
                    query = f"""
                        SELECT id, document_txt as content, embedding_vector as embedding,
                               1 - (embedding_vector <=> :query_embedding) as distance,
                               EXTRACT(EPOCH FROM created_at) as created_at,
                               EXTRACT(EPOCH FROM updated_at) as updated_at
                        FROM {table_name}
                        WHERE wksp_uuid = :wksp_uuid AND mas_uuid = :mas_uuid AND deleted_at IS NULL
                        ORDER BY embedding_vector <=> :query_embedding
                    """
                    if request.query_criteria.limit:
                        query += f" LIMIT {request.query_criteria.limit}"

                    result = conn.execute(
                        text(query),
                        {"query_embedding": embedding_str, "wksp_uuid": request.wksp_id, "mas_uuid": request.mas_id},
                    )

                else:
                    raise ValueError(f"Unsupported query type: {query_type}")

                # Convert results to list of dictionaries
                rows = result.fetchall()
                if not rows:
                    return []

                results = []
                for row in rows:
                    # Parse embedding vector string back to list
                    embedding_data = []
                    if row.embedding:
                        # Remove brackets and split by comma
                        embedding_str = str(row.embedding).strip("[]")
                        if embedding_str:
                            embedding_data = [float(x.strip()) for x in embedding_str.split(",")]

                    # Create result dictionary, excluding distance if None
                    result_dict = {
                        "id": str(row.id),  # Convert UUID to string
                        "content": row.content,
                        "embedding": embedding_data,
                    }

                    # Add timestamps in epoch format
                    created_at = getattr(row, "created_at", None)
                    if created_at is not None:
                        result_dict["created_at"] = int(created_at)

                    updated_at = getattr(row, "updated_at", None)
                    if updated_at is not None:
                        result_dict["updated_at"] = int(updated_at)

                    # Only include distance if it has a value
                    distance = getattr(row, "distance", None)
                    if distance is not None:
                        result_dict["distance"] = distance

                    results.append(result_dict)

                self.logger.info(f"Successfully queried {len(results)} records from {table_name}")
                return results

        except SQLAlchemyError as e:
            self.logger.error(f"Failed to query vectors: {str(e)}")
            raise RuntimeError(f"Failed to query vectors: {str(e)}")

    def delete_vector(self, schema_name: str, vector_id: str, soft_delete: bool = True) -> bool:
        """
        Delete a vector record from the database.

        Args:
            schema_name: Name of the schema containing the table
            vector_id: ID of the vector to delete
            soft_delete: If True, perform soft delete; if False, perform hard delete

        Returns:
            bool: True if deletion was successful, False if record not found

        Raises:
            RuntimeError: If there's an error executing the delete operation
        """
        try:
            table_name = f'"{schema_name}"."{TABLE_NAME}"'

            with self.connect_db.engine.begin() as conn:
                if soft_delete:
                    # Soft delete: Update deleted_at and deleted_by fields
                    query = f"""
                        UPDATE {table_name}
                        SET deleted_at = now(), deleted_by = current_user, updated_at = now(), updated_by = current_user
                        WHERE id = :vector_id AND deleted_at IS NULL
                    """
                    self.logger.info(f"Performing soft delete for vector {vector_id} in {table_name}")
                else:
                    # Hard delete: Permanently remove the record
                    query = f"""
                        DELETE FROM {table_name}
                        WHERE id = :vector_id
                    """
                    self.logger.info(f"Performing hard delete for vector {vector_id} in {table_name}")

                result = conn.execute(text(query), {"vector_id": vector_id})
                rows_affected = result.rowcount

                if rows_affected > 0:
                    delete_type = "soft deleted" if soft_delete else "permanently deleted"
                    self.logger.info(f"Successfully {delete_type} vector {vector_id} from {table_name}")
                    return True
                else:
                    self.logger.warning(f"Vector {vector_id} not found or already deleted in {table_name}")
                    return False

        except SQLAlchemyError as e:
            self.logger.error(f"Failed to delete vector {vector_id}: {str(e)}")
            raise RuntimeError(f"Failed to delete vector: {str(e)}")
