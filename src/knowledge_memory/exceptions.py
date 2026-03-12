"""Custom exceptions for the knowledge memory library."""


class KnowledgeMemoryError(Exception):
    """Base exception for knowledge memory operations."""

    pass


class ValidationError(KnowledgeMemoryError):
    """Raised when request validation fails."""

    pass


class NotFoundError(KnowledgeMemoryError):
    """Raised when requested resource is not found."""

    pass


class OperationFailedError(KnowledgeMemoryError):
    """Raised when an operation fails."""

    pass


def check_response_status(response, operation: str):
    """
    Check response status and raise appropriate exceptions.

    Args:
        response: Response object with status field
        operation: Name of the operation for error messages

    Raises:
        ValidationError: If validation error occurred
        NotFoundError: If resource not found
        OperationFailedError: If operation failed
    """
    try:
        # Try namespaced import (works when installed as wheel)
        from knowledge_memory.server.schemas.knowledge_graph import ResponseStatus
    except (ImportError, ModuleNotFoundError):
        # Fallback for development
        from server.schemas.knowledge_graph import ResponseStatus

    if response.status == ResponseStatus.VALIDATION_ERROR:
        raise ValidationError(f"{operation} validation error: {response.message}")
    elif response.status == ResponseStatus.NOT_FOUND:
        raise NotFoundError(f"{operation} not found: {response.message}")
    elif response.status == ResponseStatus.FAILURE:
        raise OperationFailedError(f"{operation} failed: {response.message}")
