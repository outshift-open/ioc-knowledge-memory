# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

import pytest
from server.schemas.knowledge_graph_utils import (
    validate_uuid_field,
    split_field_by_separator,
    prefix_field_with_separator,
    build_internal_attribute_key,
    DEFAULT_PROPERTY_KEY_SEPARATOR,
)


class TestValidateUuidField:
    """Test suite for validate_uuid_field function."""

    def test_validate_uuid_field_valid_uuid(self):
        """Test validation with valid UUID."""
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        result = validate_uuid_field(valid_uuid, "test_field")
        assert result == valid_uuid

    def test_validate_uuid_field_valid_uuid_uppercase(self):
        """Test validation with valid uppercase UUID."""
        valid_uuid = "550E8400-E29B-41D4-A716-446655440000"
        result = validate_uuid_field(valid_uuid, "test_field")
        assert result == valid_uuid

    def test_validate_uuid_field_none_value(self):
        """Test validation with None value (should be allowed for optional fields)."""
        result = validate_uuid_field(None, "test_field")
        assert result is None

    def test_validate_uuid_field_invalid_uuid_format(self):
        """Test validation fails with invalid UUID format."""
        with pytest.raises(ValueError, match="test_field must be a valid UUID, got: invalid-uuid"):
            validate_uuid_field("invalid-uuid", "test_field")

    def test_validate_uuid_field_empty_string(self):
        """Test validation fails with empty string."""
        with pytest.raises(ValueError, match="test_field must be a valid UUID, got: "):
            validate_uuid_field("", "test_field")

    def test_validate_uuid_field_non_string(self):
        """Test validation fails with non-string input."""
        with pytest.raises(ValueError, match="test_field must be a valid UUID, got: 123"):
            validate_uuid_field("123", "test_field")

    def test_validate_uuid_field_custom_field_name(self):
        """Test validation error message includes custom field name."""
        with pytest.raises(ValueError, match="owner_id must be a valid UUID, got: bad-uuid"):
            validate_uuid_field("bad-uuid", "owner_id")

    def test_validate_uuid_field_default_field_name(self):
        """Test validation error message with default field name."""
        with pytest.raises(ValueError, match="field must be a valid UUID, got: bad-uuid"):
            validate_uuid_field("bad-uuid")


class TestSplitFieldBySeparator:
    """Test suite for split_field_by_separator function."""

    def test_split_field_by_separator_basic(self):
        """Test basic field splitting with default separator."""
        result = split_field_by_separator("owner$key")
        assert result == ("owner", "key")

    def test_split_field_by_separator_custom_separator(self):
        """Test field splitting with custom separator."""
        result = split_field_by_separator("owner_key", "_")
        assert result == ("owner", "key")

    def test_split_field_by_separator_no_separator(self):
        """Test field splitting when separator not found."""
        result = split_field_by_separator("noseparator")
        assert result == ("noseparator", "")

    def test_split_field_by_separator_multiple_separators(self):
        """Test field splitting with multiple separators (should split on first only)."""
        result = split_field_by_separator("owner$key$value")
        assert result == ("owner", "key$value")

    def test_split_field_by_separator_empty_field(self):
        """Test field splitting with empty field."""
        result = split_field_by_separator("")
        assert result == ("", "")

    def test_split_field_by_separator_separator_at_start(self):
        """Test field splitting with separator at start."""
        result = split_field_by_separator("$key")
        assert result == ("", "key")

    def test_split_field_by_separator_separator_at_end(self):
        """Test field splitting with separator at end."""
        result = split_field_by_separator("owner$")
        assert result == ("owner", "")

    def test_split_field_by_separator_only_separator(self):
        """Test field splitting with only separator."""
        result = split_field_by_separator("$")
        assert result == ("", "")

    def test_split_field_by_separator_uuid_example(self):
        """Test field splitting with UUID example."""
        uuid_key = "550e8400-e29b-41d4-a716-446655440000$category"
        result = split_field_by_separator(uuid_key)
        assert result == ("550e8400-e29b-41d4-a716-446655440000", "category")


class TestPrefixFieldWithSeparator:
    """Test suite for prefix_field_with_separator function."""

    def test_prefix_field_with_separator_basic(self):
        """Test basic field prefixing with default separator."""
        result = prefix_field_with_separator("owner", "attribute")
        assert result == "owner$attribute"

    def test_prefix_field_with_separator_custom_separator(self):
        """Test field prefixing with custom separator."""
        result = prefix_field_with_separator("user123", "name", "_")
        assert result == "user123_name"

    def test_prefix_field_with_separator_empty_prefix(self):
        """Test field prefixing with empty prefix."""
        result = prefix_field_with_separator("", "field")
        assert result == "field"

    def test_prefix_field_with_separator_empty_field(self):
        """Test field prefixing with empty field."""
        result = prefix_field_with_separator("prefix", "")
        assert result == "prefix"

    def test_prefix_field_with_separator_both_empty(self):
        """Test field prefixing with both prefix and field empty."""
        result = prefix_field_with_separator("", "")
        assert result == ""

    def test_prefix_field_with_separator_none_prefix(self):
        """Test field prefixing with None prefix."""
        result = prefix_field_with_separator(None, "field")
        assert result == "field"

    def test_prefix_field_with_separator_none_field(self):
        """Test field prefixing with None field."""
        result = prefix_field_with_separator("prefix", None)
        assert result == "prefix"

    def test_prefix_field_with_separator_uuid_example(self):
        """Test field prefixing with UUID example."""
        uuid_owner = "550e8400-e29b-41d4-a716-446655440000"
        result = prefix_field_with_separator(uuid_owner, "category")
        assert result == "550e8400-e29b-41d4-a716-446655440000$category"

    def test_prefix_field_with_separator_special_characters(self):
        """Test field prefixing with special characters in inputs."""
        result = prefix_field_with_separator("owner-123", "key_name")
        assert result == "owner-123$key_name"


class TestBuildInternalAttributeKey:
    """Test suite for build_internal_attribute_key function."""

    def test_build_internal_attribute_key_success(self):
        """Test successful internal attribute key building."""
        owner = "550e8400-e29b-41d4-a716-446655440000"
        key = "category"
        success, prefixed_key, error_msg = build_internal_attribute_key(owner, key)
        
        assert success is True
        assert prefixed_key == "550e8400-e29b-41d4-a716-446655440000$category"
        assert error_msg == ""

    def test_build_internal_attribute_key_empty_owner(self):
        """Test internal attribute key building fails with empty owner."""
        success, prefixed_key, error_msg = build_internal_attribute_key("", "category")
        
        assert success is False
        assert prefixed_key == ""
        assert error_msg == "Error: Internal category requires owner field to be provided"

    def test_build_internal_attribute_key_none_owner(self):
        """Test internal attribute key building fails with None owner."""
        success, prefixed_key, error_msg = build_internal_attribute_key(None, "category")
        
        assert success is False
        assert prefixed_key == ""
        assert error_msg == "Error: Internal category requires owner field to be provided"

    def test_build_internal_attribute_key_valid_inputs(self):
        """Test internal attribute key building with various valid inputs."""
        test_cases = [
            ("owner123", "name", "owner123$name"),
            ("550e8400-e29b-41d4-a716-446655440000", "rate", "550e8400-e29b-41d4-a716-446655440000$rate"),
            ("user_id", "session_time", "user_id$session_time"),
        ]
        
        for owner, key, expected in test_cases:
            success, prefixed_key, error_msg = build_internal_attribute_key(owner, key)
            assert success is True
            assert prefixed_key == expected
            assert error_msg == ""

    def test_build_internal_attribute_key_empty_key(self):
        """Test internal attribute key building with empty key (should still work)."""
        owner = "550e8400-e29b-41d4-a716-446655440000"
        success, prefixed_key, error_msg = build_internal_attribute_key(owner, "")
        
        assert success is True
        assert prefixed_key == "550e8400-e29b-41d4-a716-446655440000"  # prefix_field_with_separator handles empty field
        assert error_msg == ""

    def test_build_internal_attribute_key_special_characters(self):
        """Test internal attribute key building with special characters."""
        owner = "550e8400-e29b-41d4-a716-446655440000"
        key = "key-with_special.chars"
        success, prefixed_key, error_msg = build_internal_attribute_key(owner, key)
        
        assert success is True
        assert prefixed_key == "550e8400-e29b-41d4-a716-446655440000$key-with_special.chars"
        assert error_msg == ""


class TestDefaultPropertyKeySeparator:
    """Test suite for DEFAULT_PROPERTY_KEY_SEPARATOR constant."""

    def test_default_property_key_separator_value(self):
        """Test that the default separator is '$'."""
        assert DEFAULT_PROPERTY_KEY_SEPARATOR == "$"

    def test_default_property_key_separator_usage_in_functions(self):
        """Test that functions use the default separator correctly."""
        # Test split_field_by_separator uses default
        result = split_field_by_separator("owner$key")
        assert result == ("owner", "key")
        
        # Test prefix_field_with_separator uses default
        result = prefix_field_with_separator("owner", "key")
        assert result == "owner$key"
        
        # Test build_internal_attribute_key uses default
        success, prefixed_key, _ = build_internal_attribute_key("owner", "key")
        assert success is True
        assert prefixed_key == "owner$key"


class TestIntegrationScenarios:
    """Test suite for integration scenarios combining multiple functions."""

    def test_round_trip_split_and_prefix(self):
        """Test that splitting and prefixing are inverse operations."""
        original = "550e8400-e29b-41d4-a716-446655440000$category"
        
        # Split the field
        owner, key = split_field_by_separator(original)
        
        # Prefix it back
        reconstructed = prefix_field_with_separator(owner, key)
        
        assert reconstructed == original

    def test_build_and_split_internal_attribute_key(self):
        """Test building an internal attribute key and then splitting it."""
        owner = "550e8400-e29b-41d4-a716-446655440000"
        key = "category"
        
        # Build the key
        success, prefixed_key, error_msg = build_internal_attribute_key(owner, key)
        assert success is True
        
        # Split it back
        split_owner, split_key = split_field_by_separator(prefixed_key)
        
        assert split_owner == owner
        assert split_key == key

    def test_validate_uuid_in_build_internal_attribute_key_workflow(self):
        """Test UUID validation in a typical workflow."""
        # Valid UUID should work
        valid_uuid = "550e8400-e29b-41d4-a716-446655440000"
        validated_uuid = validate_uuid_field(valid_uuid, "owner")
        
        success, prefixed_key, error_msg = build_internal_attribute_key(validated_uuid, "category")
        assert success is True
        assert prefixed_key == "550e8400-e29b-41d4-a716-446655440000$category"
        
        # Invalid UUID should raise error before reaching build function
        with pytest.raises(ValueError, match="owner must be a valid UUID"):
            invalid_uuid = "invalid-uuid"
            validate_uuid_field(invalid_uuid, "owner")

    def test_multiple_separators_in_complex_scenario(self):
        """Test handling of multiple separators in complex scenarios."""
        # Build a key with multiple potential separators
        owner = "550e8400-e29b-41d4-a716-446655440000"
        key = "nested$key$with$separators"
        
        success, prefixed_key, error_msg = build_internal_attribute_key(owner, key)
        assert success is True
        assert prefixed_key == "550e8400-e29b-41d4-a716-446655440000$nested$key$with$separators"
        
        # Split should only split on first separator
        split_owner, split_key = split_field_by_separator(prefixed_key)
        assert split_owner == owner
        assert split_key == "nested$key$with$separators"
