"""Reasoner service - Business logic for reasoner operations"""

from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from server.schemas.reasoner import (
    ReasonerRequest,
    ReasonerResponse,
    Reasoner as ReasonerSchema,
    Reasoners,
    QueryResponse,
    QueryHistoryItem,
    QueryEvent,
    QueryEvents,
    QueryEventFilter,
)
from server.database.relational_db.models.reasoner import Reasoner as ReasonerModel
from server.database.relational_db.models.reasoner_query import ReasonerHistory
from server.database.relational_db.models.mas import MultiAgenticSystem
from server.database.relational_db.db import RelationalDB
from server.services.workspace import workspace_service
from server.services.audit import AuditEventType, ResourceType, audit_service, AuditRequest


class ReasonerService:
    """Service layer for reasoner business logic"""

    def create_reasoner(self, workspace_id: str, reasoner_data: ReasonerRequest) -> ReasonerResponse:
        # Validate workspace exists
        if not workspace_service.workspace_exists(workspace_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found",
            )

        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                # Verify MAS exists in the workspace
                mas = (
                    session.query(MultiAgenticSystem)
                    .filter(
                        MultiAgenticSystem.id == reasoner_data.mas_id,
                        MultiAgenticSystem.workspace_id == workspace_id,
                        MultiAgenticSystem.deleted_at.is_(None),
                    )
                    .first()
                )

                if not mas:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Multi-agentic system with id '{reasoner_data.mas_id}' not found in this workspace",
                    )

                # Prevent duplicate active Reasoner names within the same workspace
                existing = (
                    session.query(ReasonerModel)
                    .filter(
                        ReasonerModel.workspace_id == workspace_id,
                        ReasonerModel.name == reasoner_data.name,
                        ReasonerModel.deleted_at.is_(None),
                    )
                    .first()
                )
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Reasoner with name '{reasoner_data.name}' already exists in this workspace",
                    )

                # Create new reasoner
                new_reasoner = ReasonerModel(
                    workspace_id=workspace_id,
                    mas_id=reasoner_data.mas_id,
                    name=reasoner_data.name,
                    config=reasoner_data.config,
                )

                session.add(new_reasoner)
                session.commit()
                session.refresh(new_reasoner)

                response = ReasonerResponse(
                    id=new_reasoner.id,
                    name=new_reasoner.name,
                )

                # add to audits table
                audit_service.create_audit(
                    AuditRequest(
                        resource_type=ResourceType.REASONER,
                        audit_type=AuditEventType.RESOURCE_CREATED,
                        audit_resource_id=new_reasoner.id,
                        created_by="",  # TODO: get user from apikey
                        audit_information=reasoner_data.model_dump(),
                        audit_extra_information="success",
                        created_at=new_reasoner.created_at,
                    )
                )

                return response

            except HTTPException:
                session.rollback()
                raise
            except IntegrityError as e:
                session.rollback()
                if "idx_reasoner_workspace_name_unique" in str(e):
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail=f"Reasoner with name '{reasoner_data.name}' already exists in this workspace",
                    )
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Database integrity error: {str(e)}",
                )
            except Exception as e:
                session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to create reasoner: {str(e)}",
                )
            finally:
                session.close()

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create reasoner: {str(e)}",
            )

    def list_reasoners(self, workspace_id: str) -> Reasoners:
        # Validate workspace exists
        if not workspace_service.workspace_exists(workspace_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found",
            )

        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                reasoners = (
                    session.query(ReasonerModel)
                    .filter(
                        ReasonerModel.workspace_id == workspace_id,
                        ReasonerModel.deleted_at.is_(None),
                    )
                    .all()
                )

                reasoner_responses = [
                    ReasonerSchema(
                        id=reasoner.id,
                        workspace_id=reasoner.workspace_id,
                        mas_id=reasoner.mas_id,
                        name=reasoner.name,
                        config=reasoner.config,
                        created_at=reasoner.created_at,
                        updated_at=reasoner.updated_at,
                    )
                    for reasoner in reasoners
                ]

                return Reasoners(reasoners=reasoner_responses)

            finally:
                session.close()

        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve reasoners: {str(e)}",
            )

    def get_reasoner(self, workspace_id: str, reasoner_id: str) -> ReasonerSchema:
        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                reasoner = (
                    session.query(ReasonerModel)
                    .filter(
                        ReasonerModel.id == reasoner_id,
                        ReasonerModel.workspace_id == workspace_id,
                        ReasonerModel.deleted_at.is_(None),
                    )
                    .first()
                )

                if not reasoner:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Reasoner not found",
                    )

                return ReasonerSchema(
                    id=reasoner.id,
                    workspace_id=reasoner.workspace_id,
                    mas_id=reasoner.mas_id,
                    name=reasoner.name,
                    config=reasoner.config,
                    created_at=reasoner.created_at,
                    updated_at=reasoner.updated_at,
                    created_by=reasoner.created_by,
                    updated_by=reasoner.updated_by,
                )

            finally:
                session.close()

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve reasoner: {str(e)}",
            )

    def delete_reasoner(self, workspace_id: str, reasoner_id: str, _purge: bool = False) -> dict:
        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                reasoner = (
                    session.query(ReasonerModel)
                    .filter(
                        ReasonerModel.id == reasoner_id,
                        ReasonerModel.workspace_id == workspace_id,
                        ReasonerModel.deleted_at.is_(None),
                    )
                    .first()
                )

                if not reasoner:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail="Reasoner not found",
                    )

                if _purge:
                    session.delete(reasoner)
                    message = "Reasoner permanently deleted"
                else:
                    reasoner.deleted_at = datetime.now(timezone.utc)
                    message = "Reasoner deleted successfully"

                session.commit()

                # add to audits table
                audit_service.create_audit(
                    AuditRequest(
                        resource_type=ResourceType.REASONER,
                        audit_type=AuditEventType.RESOURCE_DELETED,
                        audit_resource_id=reasoner_id,
                        deleted_by="",  # TODO: get user from apikey
                        audit_information={"purge": _purge},
                        audit_extra_information=message,
                        deleted_at=reasoner.deleted_at,
                    )
                )

                return {"message": message}

            finally:
                session.close()

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete reasoner: {str(e)}",
            )

    def store_reasoner_event(self, workspace_id: str, reasoner_id: str, query_data: dict) -> QueryResponse:
        """Store a query response as backup history"""
        # Validate workspace exists
        if not workspace_service.workspace_exists(workspace_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found",
            )

        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                # Verify reasoner exists in the workspace
                reasoner = (
                    session.query(ReasonerModel)
                    .filter(
                        ReasonerModel.id == reasoner_id,
                        ReasonerModel.workspace_id == workspace_id,
                        ReasonerModel.deleted_at.is_(None),
                    )
                    .first()
                )

                if not reasoner:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Reasoner with id '{reasoner_id}' not found in this workspace",
                    )

                # Create query record
                query_input_value = query_data.get("query_input")
                # Convert empty string to None for NULL in database
                if query_input_value == "":
                    query_input_value = None

                query_record = ReasonerHistory(
                    workspace_id=workspace_id,
                    reasoner_id=reasoner_id,
                    request_id=query_data.get("reasoner_cognition_request_id"),
                    response_id=query_data.get("reasoner_cognition_response_id"),
                    query_input=query_input_value,
                    response_data=query_data,
                    created_by="",  # TODO: get user from apikey
                )

                session.add(query_record)
                session.commit()
                session.refresh(query_record)

                response = QueryResponse(
                    id=query_record.id,
                    reasoner_id=reasoner_id,
                    workspace_id=workspace_id,
                    created_at=query_record.created_at,
                )

                # Log audit event
                audit_service.create_audit(
                    AuditRequest(
                        resource_type=ResourceType.REASONER,
                        audit_type=AuditEventType.REASONING_QUERY,
                        audit_resource_id=reasoner_id,
                        created_by="",  # TODO: get user from apikey
                        audit_information={"response_id": query_data.get("reasoner_cognition_response_id")},
                        audit_extra_information="query stored",
                        created_at=query_record.created_at,
                    )
                )

                return response

            except HTTPException:
                session.rollback()
                raise
            except Exception as e:
                session.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to store query: {str(e)}",
                )
            finally:
                session.close()

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to store query: {str(e)}",
            )

    def list_and_filter_reasoner_events(
        self, workspace_id: str, reasoner_id: str = None, filters: QueryEventFilter = None
    ) -> QueryEvents:
        """Retrieve query events with optional filters. Can query all reasoners or a specific reasoner"""
        # Validate workspace exists
        if not workspace_service.workspace_exists(workspace_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found",
            )

        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                # Normalize reasoner_id: treat empty string as None
                reasoner_id = reasoner_id if reasoner_id else None

                # Build query with filters
                query = session.query(ReasonerHistory).filter(ReasonerHistory.workspace_id == workspace_id)

                # Apply reasoner_id filter if provided (either from parameter or filters)
                if reasoner_id:
                    query = query.filter(ReasonerHistory.reasoner_id == reasoner_id)
                elif filters and filters.reasoner_id:
                    query = query.filter(ReasonerHistory.reasoner_id == filters.reasoner_id)

                # Apply optional filters
                if filters:
                    if filters.request_id:
                        query = query.filter(ReasonerHistory.request_id == filters.request_id)
                    if filters.response_id:
                        query = query.filter(ReasonerHistory.response_id == filters.response_id)
                    if filters.created_by:
                        query = query.filter(ReasonerHistory.created_by == filters.created_by)
                    if filters.start_date:
                        query = query.filter(ReasonerHistory.created_at >= filters.start_date)
                    if filters.end_date:
                        query = query.filter(ReasonerHistory.created_at <= filters.end_date)

                # Get total count before pagination
                total = query.count()

                # Apply ordering and pagination
                offset = filters.offset if filters and filters.offset else 0
                limit = filters.limit if filters and filters.limit else 100

                query_records = query.order_by(ReasonerHistory.created_at.desc()).offset(offset).limit(limit).all()

                events = [
                    QueryEvent(
                        id=str(record.id),
                        reasoner_id=str(record.reasoner_id),
                        workspace_id=str(record.workspace_id),
                        request_id=record.request_id,
                        response_id=record.response_id,
                        created_at=record.created_at,
                        created_by=record.created_by,
                        query_input=record.query_input,
                    )
                    for record in query_records
                ]

                return QueryEvents(records=events, total=total)

            finally:
                session.close()

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve query events: {str(e)}",
            )

    def get_reasoner_event_details(self, workspace_id: str, query_event_id: str) -> QueryHistoryItem:
        """Retrieve detailed query event information including response data"""
        # Validate workspace exists
        if not workspace_service.workspace_exists(workspace_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workspace not found",
            )

        try:
            db = RelationalDB()
            session = db.get_session()

            try:
                # Retrieve the specific query event
                query_record = (
                    session.query(ReasonerHistory)
                    .filter(
                        ReasonerHistory.id == query_event_id,
                        ReasonerHistory.workspace_id == workspace_id,
                    )
                    .first()
                )

                if not query_record:
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Query event with id '{query_event_id}' not found",
                    )

                return QueryHistoryItem(
                    id=query_record.id,
                    reasoner_id=query_record.reasoner_id,
                    workspace_id=query_record.workspace_id,
                    request_id=query_record.request_id,
                    response_id=query_record.response_id,
                    response_data=query_record.response_data,
                    created_at=query_record.created_at,
                )

            finally:
                session.close()

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve query event history: {str(e)}",
            )


# Global service instance
reasoner_service = ReasonerService()
