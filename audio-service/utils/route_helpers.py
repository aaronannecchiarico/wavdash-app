"""
Route Helper Utilities
Common functions used across multiple route handlers to reduce code duplication
"""

import uuid
import logging
from typing import Optional
from fastapi import HTTPException

from services.storage_service import get_storage_service, is_storage_enabled, get_storage_type
from services.storage_service import StorageType


logger = logging.getLogger(__name__)


def generate_task_id() -> str:
    """
    Generate a unique task ID for async processing

    Returns:
        str: UUID string for task tracking
    """
    return str(uuid.uuid4())


def validate_storage_enabled() -> None:
    """
    Validate that storage service is properly configured and enabled

    Raises:
        HTTPException: 503 error if storage is not enabled
    """
    if not is_storage_enabled():
        logger.error("Storage is not properly configured")
        raise HTTPException(
            status_code=503,
            detail="Storage is not properly configured"
        )


def validate_file_exists(storage_path: str) -> None:
    """
    Validate that a file exists in the configured storage

    Args:
        storage_path: Path to the file in storage

    Raises:
        HTTPException: 404 error if file not found
    """
    storage = get_storage_service()
    if not storage.file_exists(storage_path):
        logger.error(f"File not found in storage: {storage_path}")
        raise HTTPException(
            status_code=404,
            detail=f"File not found in storage: {storage_path}"
        )


def validate_storage_and_file(storage_path: str) -> None:
    """
    Combined validation for storage enabled and file existence

    Args:
        storage_path: Path to the file in storage

    Raises:
        HTTPException: 503 if storage not enabled, 404 if file not found
    """
    validate_storage_enabled()
    validate_file_exists(storage_path)


def get_storage_type_value() -> str:
    """
    Get the current storage type as a string value

    Returns:
        str: Storage type value (e.g., "local", "s3")
    """
    return get_storage_type().value


def handle_route_error(error: Exception, context: str, log_details: Optional[dict] = None) -> HTTPException:
    """
    Standardized error handling for route exceptions

    Args:
        error: The exception that was caught
        context: Description of what operation failed (e.g., "storage feature extraction")
        log_details: Optional dict of additional details to log

    Returns:
        HTTPException: Properly formatted HTTP exception

    Notes:
        - HTTPExceptions are re-raised as-is
        - Other exceptions are wrapped in 500 errors
        - All errors are logged with context
    """
    # Re-raise HTTP exceptions without wrapping
    if isinstance(error, HTTPException):
        raise error

    # Log the error with context
    logger.error(f"Error in {context}: {str(error)}")
    if log_details:
        logger.error(f"Additional details: {log_details}")

    # Return wrapped exception
    raise HTTPException(
        status_code=500,
        detail=f"Processing error: {str(error)}"
    )


def validate_required_field(value: Optional[str], field_name: str) -> None:
    """
    Validate that a required field is present and not empty

    Args:
        value: The field value to check
        field_name: Name of the field for error messages

    Raises:
        HTTPException: 422 error if field is missing or empty
    """
    if not value:
        logger.error(f"Missing required field: {field_name}")
        raise HTTPException(
            status_code=422,
            detail=f"{field_name} is required"
        )


def create_processing_response(
    task_id: str,
    status: str,
    message: str,
    **additional_fields
) -> dict:
    """
    Create a standardized processing response dictionary

    Args:
        task_id: The task ID for tracking
        status: Status string (e.g., "processing", "completed")
        message: Human-readable message
        **additional_fields: Any additional fields to include in response

    Returns:
        dict: Standardized response dictionary
    """
    response = {
        "task_id": task_id,
        "status": status,
        "message": message,
        "storage_type": get_storage_type_value()
    }
    response.update(additional_fields)
    return response
