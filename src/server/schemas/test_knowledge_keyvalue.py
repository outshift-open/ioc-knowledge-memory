#!/usr/bin/env python3
# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

"""
Test suite for Knowledge Key-Value Pair (KVP) functionality.

This module contains comprehensive tests for:
- KVP schema validation
- KVP service layer operations
- KVP API endpoints
- Database operations
- UUID format validation
- Scope-based validation
"""

import json
import pytest
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock

from server.schemas.knowledge_keyvalue import (
    ScopeType,
    KnowledgeKVPStoreOnboardRequest,
    KnowledgeKVPStoreOnboardDeleteRequest,
    KnowledgeKVPStoreRequest,
    KnowledgeKVPDeleteRequest,
    KnowledgeKVPQueryRequest,
    KnowledgeKVPRecord,
    KnowledgeKVPQueryCriteria,
    ResponseStatus,
    validate_uuid_format,
    validate_scope_requirements,
    QUERY_TYPE_GET_BY_KEY
)
from server.services.knowledge_keyvalue import KnowledgeKVPService
from server.database.keyvalue_db.postgres.src.db import (
    KeyValueDB,
    KeyValueDBStoreRequest,
    KeyValueDBQueryRequest,
    KeyValueDBDeleteRequest
)


class TestUUIDValidation:
    """Test UUID format validation helper."""

    def test_valid_uuid_formats(self):
        """Test that valid UUID formats pass validation."""
        valid_uuids = [
            "123e4567-e89b-12d3-a456-426614174000",
            "00000000-0000-0000-0000-000000000000",
            "ffffffff-ffff-ffff-ffff-ffffffffffff",
            "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
        ]
        
        for uuid_str in valid_uuids:
            result = validate_uuid_format(uuid_str, "test_field")
            assert result == uuid_str

    def test_invalid_uuid_formats(self):
        """Test that invalid UUID formats raise ValueError."""
        invalid_uuids = [
            "123e4567_e89b_12d3_a456_426614174000",  # Underscores instead of hyphens
            "123e4567-e89b-12d3-a456",               # Too short
            "123e4567-e89b-12d3-a456-426614174000-extra",  # Too long
            "not-a-uuid-at-all",                     # Invalid format
            "123g4567-e89b-12d3-a456-426614174000",  # Invalid hex character
            "123e4567-e89b-12d3-a456-42661417400",   # Missing digit
        ]
        
        for uuid_str in invalid_uuids:
            with pytest.raises(ValueError, match=r"test_field must be a valid UUID format"):
                validate_uuid_format(uuid_str, "test_field")

    def test_none_uuid_passes_validation(self):
        """Test that None values pass validation (for optional fields)."""
        # The validate_uuid_format function returns None/empty values as-is
        result = validate_uuid_format(None, "test_field")
        assert result is None
        
        result = validate_uuid_format("", "test_field")
        assert result == ""


class TestScopeValidation:
    """Test scope-based field validation."""

    def test_mas_scope_validation_success(self):
        """Test successful MAS scope validation."""
        mock_instance = Mock()
        mock_instance.scope = ScopeType.MAS
        mock_instance.wksp_id = "123e4567-e89b-12d3-a456-426614174000"
        mock_instance.mas_id = "223e4567-e89b-12d3-a456-426614174001"
        mock_instance.ce_id = None
        
        result = validate_scope_requirements(mock_instance)
        assert result == mock_instance

    def test_ce_scope_validation_success(self):
        """Test successful CE scope validation."""
        mock_instance = Mock()
        mock_instance.scope = ScopeType.CE
        mock_instance.ce_id = "agent-001"
        mock_instance.wksp_id = None
        mock_instance.mas_id = None
        
        result = validate_scope_requirements(mock_instance)
        assert result == mock_instance

    def test_mas_scope_missing_wksp_id(self):
        """Test MAS scope validation failure when wksp_id is missing."""
        mock_instance = Mock()
        mock_instance.scope = ScopeType.MAS
        mock_instance.wksp_id = None
        mock_instance.mas_id = "223e4567-e89b-12d3-a456-426614174001"
        
        with pytest.raises(ValueError, match="wksp_id is required for MAS scope"):
            validate_scope_requirements(mock_instance)

    def test_mas_scope_missing_mas_id(self):
        """Test MAS scope validation failure when mas_id is missing."""
        mock_instance = Mock()
        mock_instance.scope = ScopeType.MAS
        mock_instance.wksp_id = "123e4567-e89b-12d3-a456-426614174000"
        mock_instance.mas_id = None
        
        with pytest.raises(ValueError, match="mas_id is required for MAS scope"):
            validate_scope_requirements(mock_instance)

    def test_ce_scope_missing_ce_id(self):
        """Test CE scope validation failure when ce_id is missing."""
        mock_instance = Mock()
        mock_instance.scope = ScopeType.CE
        mock_instance.ce_id = None
        
        with pytest.raises(ValueError, match="ce_id is required for CE scope"):
            validate_scope_requirements(mock_instance)


class TestKVPSchemas:
    """Test KVP Pydantic schema validation."""

    def test_kvp_store_onboard_request_valid(self):
        """Test valid KVP store onboard request."""
        request_data = {
            "scope": "mas",
        }
        
        request = KnowledgeKVPStoreOnboardRequest(**request_data)
        assert request.scope == ScopeType.MAS

    def test_kvp_store_request_uuid_validation(self):
        """Test UUID validation in KVP store request."""
        # Valid UUID format
        request_data = {
            "scope": "mas",
            "wksp_id": "123e4567-e89b-12d3-a456-426614174000",
            "mas_id": "223e4567-e89b-12d3-a456-426614174001",
            "records": [
                {
                    "key": {"episode_id": "123"},
                    "value": {"name": "John Doe"}
                }
            ]
        }
        
        request = KnowledgeKVPStoreRequest(**request_data)
        assert request.wksp_id == "123e4567-e89b-12d3-a456-426614174000"
        
        # Invalid UUID format should raise validation error
        invalid_data = request_data.copy()
        invalid_data["wksp_id"] = "123e4567_e89b_12d3_a456_426614174000"  # Underscores
        
        with pytest.raises(ValueError, match="wksp_id must be a valid UUID format"):
            KnowledgeKVPStoreRequest(**invalid_data)

    def test_kvp_delete_request_scope_validation(self):
        """Test scope validation in KVP delete request."""
        # Valid MAS scope
        mas_data = {
            "scope": "mas",
            "wksp_id": "123e4567-e89b-12d3-a456-426614174000",
            "mas_id": "223e4567-e89b-12d3-a456-426614174001",
            "key": {"episode_id": "123"}
        }
        
        request = KnowledgeKVPDeleteRequest(**mas_data)
        assert request.scope == ScopeType.MAS
        
        # Invalid MAS scope (missing mas_id)
        invalid_mas_data = mas_data.copy()
        del invalid_mas_data["mas_id"]
        
        with pytest.raises(ValueError, match="mas_id is required for MAS scope"):
            KnowledgeKVPDeleteRequest(**invalid_mas_data)

    def test_kvp_query_request_ce_scope(self):
        """Test CE scope validation in KVP query request."""
        ce_data = {
            "scope": "ce",
            "ce_id": "agent-001",
            "query_criteria": {
                "query_type": "get_by_key",
                "key": {"episode_id": "123"}
            }
        }
        
        request = KnowledgeKVPQueryRequest(**ce_data)
        assert request.scope == ScopeType.CE
        assert request.ce_id == "agent-001"
        assert request.query_criteria.query_type == "get_by_key"

    def test_ce_id_no_uuid_validation(self):
        """Test that ce_id doesn't require UUID format (it's VARCHAR in DB)."""
        # ce_id can be any string format
        valid_ce_ids = [
            "agent-001",
            "ce_engine_v2",
            "simple-string",
            "123",
            "cognition-engine-alpha"
        ]
        
        for ce_id in valid_ce_ids:
            request_data = {
                "scope": "ce",
                "ce_id": ce_id,
                "records": [{"key": {"test": "key"}, "value": {"test": "value"}}]
            }
            
            request = KnowledgeKVPStoreRequest(**request_data)
            assert request.ce_id == ce_id


class TestKnowledgeKVPService:
    """Test KVP service layer functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = KnowledgeKVPService()
        self.mock_db = Mock(spec=KeyValueDB)

    def test_normalize_id(self):
        """Test ID normalization for schema names."""
        service = KnowledgeKVPService()
        
        test_cases = [
            ("123e4567-e89b-12d3-a456-426614174000", "123e4567_e89b_12d3_a456_426614174000"),
            ("simple-id", "simple_id"),
            ("already_normalized", "already_normalized"),
            ("multi-dash-id", "multi_dash_id")
        ]
        
        for input_id, expected in test_cases:
            result = service._normalize_id(input_id)
            assert result == expected

    def test_denormalize_id(self):
        """Test ID denormalization."""
        service = KnowledgeKVPService()
        
        test_cases = [
            ("123e4567_e89b_12d3_a456_426614174000", "123e4567-e89b-12d3-a456-426614174000"),
            ("simple_id", "simple-id"),
            ("already-denormalized", "already-denormalized"),
            ("multi_underscore_id", "multi-underscore-id")
        ]
        
        for input_id, expected in test_cases:
            result = service._denormalize_id(input_id)
            assert result == expected

    def test_get_schema_name_mas(self):
        """Test schema name generation for MAS scope."""
        service = KnowledgeKVPService()
        
        store_id = "223e4567-e89b-12d3-a456-426614174001"
        schema_name = service.get_schema_name(store_id, ScopeType.MAS)
        
        expected = "kvp_mas_223e4567_e89b_12d3_a456_426614174001"
        assert schema_name == expected

    def test_get_schema_name_ce(self):
        """Test schema name generation for CE scope."""
        service = KnowledgeKVPService()
        
        store_id = "agent-001"
        schema_name = service.get_schema_name(store_id, ScopeType.CE)
        
        expected = "kvp_ce_agent_001"
        assert schema_name == expected

    @patch('server.services.knowledge_keyvalue.KeyValueDB')
    def test_onboard_success(self, mock_db_class):
        """Test successful KVP store onboarding."""
        # Setup
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        mock_db.create_schema.return_value = True
        
        service = KnowledgeKVPService()
        
        request_data = KnowledgeKVPStoreOnboardRequest(
            scope=ScopeType.MAS
        )
        
        # Execute
        response = service.onboard("test-store-id", request_data)
        
        # Verify
        assert response.status == ResponseStatus.SUCCESS
        assert "test-store-id" in response.message
        mock_db.onboard.assert_called_once()

    @patch('server.services.knowledge_keyvalue.KeyValueDB')
    def test_create_kvp_store_success(self, mock_db_class):
        """Test successful KVP record creation."""
        # Setup
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        mock_db.save.return_value = True
        
        service = KnowledgeKVPService()
        
        # Mock store existence check
        with patch.object(service, '_store_exists', return_value=True):
            request_data = KnowledgeKVPStoreRequest(
                scope=ScopeType.CE,
                ce_id="agent-001",
                records=[
                    KnowledgeKVPRecord(
                        key={"episode_id": "123"},
                        value={"name": "John Doe"}
                    )
                ]
            )
            
            # Execute
            response = service.create_kvp_store(request_data)
            
            # Verify
            assert response.status == ResponseStatus.SUCCESS
            mock_db.save.assert_called_once()

    @patch('server.services.knowledge_keyvalue.KeyValueDB')
    def test_query_kvp_store_success(self, mock_db_class):
        """Test successful KVP query."""
        # Setup
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        mock_db.query.return_value = [
            {
                "key": {"episode_id": "123"},
                "value": {"name": "John Doe"},
                "created_at": 1640995200,
                "updated_at": 1640995200
            }
        ]
        
        service = KnowledgeKVPService()
        
        # Mock store existence check
        with patch.object(service, '_store_exists', return_value=True):
            request_data = KnowledgeKVPQueryRequest(
                scope=ScopeType.CE,
                ce_id="agent-001",
                query_criteria=KnowledgeKVPQueryCriteria(
                    query_type=QUERY_TYPE_GET_BY_KEY,
                    key={"episode_id": "123"}
                )
            )
            
            # Execute
            response = service.query_kvp_store(request_data)
            
            # Verify
            assert response.status == ResponseStatus.SUCCESS
            assert len(response.records) == 1
            assert response.records[0].key == {"episode_id": "123"}
            assert response.records[0].value == {"name": "John Doe"}

    @patch('server.services.knowledge_keyvalue.KeyValueDB')
    def test_delete_kvp_store_success(self, mock_db_class):
        """Test successful KVP record deletion."""
        # Setup
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        mock_db.delete.return_value = 1  # 1 record deleted
        
        service = KnowledgeKVPService()
        
        # Mock store existence check
        with patch.object(service, '_store_exists', return_value=True):
            request_data = KnowledgeKVPDeleteRequest(
                scope=ScopeType.CE,
                ce_id="agent-001",
                key={"episode_id": "123"},
                soft_delete=True
            )
            
            # Execute
            response = service.delete_kvp_store(request_data)
            
            # Verify
            assert response.status == ResponseStatus.SUCCESS
            assert "soft deleted" in response.message
            mock_db.delete.assert_called_once()

    def test_store_not_found_error(self):
        """Test error handling when store doesn't exist."""
        service = KnowledgeKVPService()
        
        # Mock store existence check to return False
        with patch.object(service, '_store_exists', return_value=False):
            request_data = KnowledgeKVPStoreRequest(
                scope=ScopeType.CE,
                ce_id="agent-001",
                records=[]
            )
            
            # Execute
            response = service.create_kvp_store(request_data)
            
            # Verify
            assert response.status == ResponseStatus.NOT_FOUND
            assert "not found" in response.message


class TestDatabaseLayer:
    """Test database layer operations."""

    def test_keyvalue_db_store_request_creation(self):
        """Test KeyValueDBStoreRequest creation."""
        request = KeyValueDBStoreRequest(
            schema_name="kvp_mas_test_schema",
            scope_type=ScopeType.MAS,
            wksp_id="123e4567-e89b-12d3-a456-426614174000",
            mas_id="223e4567-e89b-12d3-a456-426614174001",
            agent_id="agent_1",
            ce_id=None,
            records=[
                {
                    "id": str(uuid4()),
                    "key": {"episode_id": "123"},
                    "value": {"name": "John Doe"}
                }
            ]
        )
        
        assert request.schema_name == "kvp_mas_test_schema"
        assert request.scope_type == ScopeType.MAS
        assert request.wksp_id == "123e4567-e89b-12d3-a456-426614174000"
        assert len(request.records) == 1

    def test_keyvalue_db_query_request_creation(self):
        """Test KeyValueDBQueryRequest creation."""
        request = KeyValueDBQueryRequest(
            schema_name="kvp_ce_test_schema",
            scope_type=ScopeType.CE,
            key={"episode_id": "123"},
            wksp_id=None,
            mas_id=None,
            agent_id=None,
            ce_id="agent-001",
            limit=10
        )
        
        assert request.schema_name == "kvp_ce_test_schema"
        assert request.scope_type == ScopeType.CE
        assert request.key == {"episode_id": "123"}
        assert request.ce_id == "agent-001"
        assert request.limit == 10

    def test_keyvalue_db_delete_request_creation(self):
        """Test KeyValueDBDeleteRequest creation."""
        request = KeyValueDBDeleteRequest(
            schema_name="kvp_mas_test_schema",
            scope_type=ScopeType.MAS,
            key={"episode_id": "123"},
            wksp_id="123e4567-e89b-12d3-a456-426614174000",
            mas_id="223e4567-e89b-12d3-a456-426614174001",
            agent_id="agent_1",
            ce_id=None,
            soft_delete=True
        )
        
        assert request.schema_name == "kvp_mas_test_schema"
        assert request.scope_type == ScopeType.MAS
        assert request.key == {"episode_id": "123"}
        assert request.soft_delete is True


class TestIntegration:
    """Integration tests for end-to-end KVP functionality."""

    @patch('server.services.knowledge_keyvalue.KeyValueDB')
    def test_full_kvp_workflow(self, mock_db_class):
        """Test complete KVP workflow: onboard -> store -> query -> delete."""
        # Setup
        mock_db = Mock()
        mock_db_class.return_value = mock_db
        mock_db.create_schema.return_value = True
        mock_db.save.return_value = True
        mock_db.query.return_value = [
            {
                "key": {"episode_id": "123"},
                "value": {"name": "John Doe"},
                "created_at": 1640995200,
                "updated_at": 1640995200
            }
        ]
        mock_db.delete.return_value = 1
        
        service = KnowledgeKVPService()
        store_id = "223e4567-e89b-12d3-a456-426614174001"
        
        # 1. Onboard store
        onboard_request = KnowledgeKVPStoreOnboardRequest(
            scope=ScopeType.MAS
        )
        
        onboard_response = service.onboard(store_id, onboard_request)
        assert onboard_response.status == ResponseStatus.SUCCESS
        
        # Mock store existence for subsequent operations
        with patch.object(service, '_store_exists', return_value=True):
            # 2. Store records
            store_request = KnowledgeKVPStoreRequest(
                scope=ScopeType.MAS,
                wksp_id="123e4567-e89b-12d3-a456-426614174000",
                mas_id=store_id,
                records=[
                    KnowledgeKVPRecord(
                        key={"episode_id": "123"},
                        value={"name": "John Doe"}
                    )
                ]
            )
            
            store_response = service.create_kvp_store(store_request)
            assert store_response.status == ResponseStatus.SUCCESS
            
            # 3. Query records
            query_request = KnowledgeKVPQueryRequest(
                scope=ScopeType.MAS,
                wksp_id="123e4567-e89b-12d3-a456-426614174000",
                mas_id=store_id,
                query_criteria=KnowledgeKVPQueryCriteria(
                    query_type=QUERY_TYPE_GET_BY_KEY,
                    key={"episode_id": "123"}
                )
            )
            
            query_response = service.query_kvp_store(query_request)
            assert query_response.status == ResponseStatus.SUCCESS
            assert len(query_response.records) == 1
            
            # 4. Delete records
            delete_request = KnowledgeKVPDeleteRequest(
                scope=ScopeType.MAS,
                wksp_id="123e4567-e89b-12d3-a456-426614174000",
                mas_id=store_id,
                key={"episode_id": "123"},
                soft_delete=True
            )
            
            delete_response = service.delete_kvp_store(delete_request)
            assert delete_response.status == ResponseStatus.SUCCESS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
