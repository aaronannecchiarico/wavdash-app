"""
Error Response Models
Standard error response models for consistent API error handling
"""

from datetime import datetime, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


def get_utc_timestamp() -> str:
    """Get current UTC timestamp in ISO format"""
    return datetime.now(timezone.utc).isoformat()


class ErrorDetail(BaseModel):
    """Detailed error information"""

    field: Optional[str] = Field(
        None, description="Field that caused the error (for validation errors)"
    )
    message: str = Field(..., description="Error message")
    code: Optional[str] = Field(
        None, description="Error code for programmatic handling"
    )


class ErrorResponse(BaseModel):
    """
    Standard error response model

    Used for all API error responses to ensure consistency
    """

    error: str = Field(..., description="Error type or category")
    detail: str = Field(..., description="Human-readable error description")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: str = Field(
        default_factory=get_utc_timestamp, description="Error timestamp (ISO format)"
    )
    path: Optional[str] = Field(None, description="Request path that caused the error")
    request_id: Optional[str] = Field(None, description="Request ID for tracking")
    errors: Optional[list[ErrorDetail]] = Field(
        None, description="Additional error details (for validation errors)"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "FileNotFoundError",
                "detail": "File not found in storage: uploads/test.mp3",
                "status_code": 404,
                "timestamp": "2025-01-13T10:30:00.000Z",
                "path": "/storage/extract-features",
                "request_id": "req-12345",
            }
        }


class ValidationErrorResponse(BaseModel):
    """
    Validation error response model

    Used specifically for request validation errors (422)
    """

    error: str = Field(default="ValidationError", description="Error type")
    detail: str = Field(..., description="General validation error message")
    status_code: int = Field(default=422, description="HTTP status code")
    timestamp: str = Field(default_factory=get_utc_timestamp)
    validation_errors: list[Dict[str, Any]] = Field(
        ..., description="List of validation errors from Pydantic"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "detail": "Request validation failed",
                "status_code": 422,
                "timestamp": "2025-01-13T10:30:00.000Z",
                "validation_errors": [
                    {
                        "loc": ["body", "storage_path"],
                        "msg": "field required",
                        "type": "value_error.missing",
                    }
                ],
            }
        }


class StorageErrorResponse(BaseModel):
    """
    Storage-specific error response

    Used for storage service errors
    """

    error: str = Field(default="StorageError", description="Error type")
    detail: str = Field(..., description="Storage error description")
    status_code: int = Field(..., description="HTTP status code")
    timestamp: str = Field(default_factory=get_utc_timestamp)
    storage_type: Optional[str] = Field(
        None, description="Type of storage (local, s3, r2, gcs)"
    )
    storage_path: Optional[str] = Field(
        None, description="Storage path that caused the error"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "error": "StorageError",
                "detail": "Failed to upload file to storage",
                "status_code": 500,
                "timestamp": "2025-01-13T10:30:00.000Z",
                "storage_type": "local",
                "storage_path": "uploads/test.mp3",
            }
        }


class TaskErrorResponse(BaseModel):
    """
    Task processing error response

    Used for Celery task errors
    """

    error: str = Field(default="TaskError", description="Error type")
    detail: str = Field(..., description="Task error description")
    status_code: int = Field(default=500, description="HTTP status code")
    timestamp: str = Field(default_factory=get_utc_timestamp)
    task_id: Optional[str] = Field(None, description="Task ID that failed")
    task_name: Optional[str] = Field(None, description="Name of the failed task")

    class Config:
        json_schema_extra = {
            "example": {
                "error": "TaskError",
                "detail": "Task failed during audio processing",
                "status_code": 500,
                "timestamp": "2025-01-13T10:30:00.000Z",
                "task_id": "task-12345",
                "task_name": "process_audio_features",
            }
        }
