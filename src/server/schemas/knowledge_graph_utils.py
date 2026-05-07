# Copyright 2026 Cisco Systems, Inc. and its affiliates
#
# SPDX-License-Identifier: Apache-2.0

from typing import Optional

# Import the constant to avoid circular imports, we'll define it here too
DEFAULT_PROPERTY_KEY_SEPARATOR = "$"


def validate_uuid_field(value: Optional[str], field_name: str = "field") -> Optional[str]:
    """Common helper to validate field as uuid.
    
    Args:
        value: The value to validate (can be None for optional fields)
        field_name: Name of the field being validated (for error messages)
        
    Returns:
        The validated UUID string or None if value was None
        
    Raises:
        ValueError: If the value is not a valid UUID
    """
    if value is None:
        return value
        
    import uuid
    try:
        # This will raise ValueError if not a valid UUID
        uuid.UUID(value)
        return value
    except ValueError:
        raise ValueError(f"{field_name} must be a valid UUID, got: {value}")


def split_field_by_separator(field: str, separator: str = DEFAULT_PROPERTY_KEY_SEPARATOR) -> tuple[str, str]:
    """Split a field by separator and return both parts.
    
    Args:
        field: The field string to split
        separator: The separator to split on (default: "$")
        
    Returns:
        Tuple containing (prefix, suffix) parts
        If separator not found, returns (field, "")
        
    Examples:
        split_field_by_separator("ownerid$key", "$") -> ("ownerid", "key")
        split_field_by_separator("noseparator", "$") -> ("noseparator", "")
    """
    if separator in field:
        parts = field.split(separator, 1)  # Split on first occurrence only
        return parts[0], parts[1] if len(parts) == 2 else ""
    return field, ""


def prefix_field_with_separator(prefix: str, field: str, separator: str = DEFAULT_PROPERTY_KEY_SEPARATOR) -> str:
    """Prefix a field with a separator.
    
    Args:
        prefix: The prefix to add
        field: The field name to prefix
        separator: The separator to use (default: "$")
        
    Returns:
        Prefixed field string in format "prefix{separator}field"
        
    Examples:
        prefix_field_with_separator("owner", "attribute", "$") -> "owner$attribute"
        prefix_field_with_separator("user123", "name", "_") -> "user123_name"
    """
    if not prefix or not field:
        return field if field else prefix
        
    return f"{prefix}{separator}{field}"


def build_internal_attribute_key(owner: str, key: str) -> tuple[bool, str, str]:
    """Build internal attribute key for internal category filters.
    
    Args:
        owner: The owner UUID string
        key: The attribute key name
        
    Returns:
        Tuple containing (success: bool, prefixed_key: str, error_msg: str)
    """
    if not owner:
        return False, "", f"Error: Internal category requires owner field to be provided"
    
    # Use owner directly and prefix with attribute key (no sanitization needed with property key quoting)
    prefixed_key = prefix_field_with_separator(owner, key, DEFAULT_PROPERTY_KEY_SEPARATOR)
    
    return True, prefixed_key, ""
