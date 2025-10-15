"""
Custom Exceptions
Application-specific exceptions for better error handling
"""

from typing import Optional, Dict, Any


class AudioServiceException(Exception):
    """Base exception for all audio service errors"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message
        self.status_code = status_code
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


class StorageNotEnabledError(AudioServiceException):
    """Raised when storage service is not properly configured"""

    def __init__(self, message: str = "Storage is not properly configured"):
        super().__init__(
            message=message, status_code=503, error_code="StorageNotEnabled"
        )


class FileNotFoundError(AudioServiceException):
    """Raised when a file is not found in storage"""

    def __init__(self, storage_path: str):
        super().__init__(
            message=f"File not found in storage: {storage_path}",
            status_code=404,
            error_code="FileNotFound",
            details={"storage_path": storage_path},
        )


class InvalidStoragePathError(AudioServiceException):
    """Raised when storage path is invalid"""

    def __init__(self, storage_path: str, reason: str = "Invalid format"):
        super().__init__(
            message=f"Invalid storage path: {storage_path} - {reason}",
            status_code=422,
            error_code="InvalidStoragePath",
            details={"storage_path": storage_path, "reason": reason},
        )


class StorageOperationError(AudioServiceException):
    """Raised when a storage operation fails"""

    def __init__(self, operation: str, storage_path: str, reason: str):
        super().__init__(
            message=f"Storage {operation} failed for {storage_path}: {reason}",
            status_code=500,
            error_code="StorageOperationError",
            details={
                "operation": operation,
                "storage_path": storage_path,
                "reason": reason,
            },
        )


class TaskNotFoundError(AudioServiceException):
    """Raised when a task ID is not found"""

    def __init__(self, task_id: str):
        super().__init__(
            message=f"Task not found: {task_id}",
            status_code=404,
            error_code="TaskNotFound",
            details={"task_id": task_id},
        )


class TaskProcessingError(AudioServiceException):
    """Raised when task processing fails"""

    def __init__(self, task_id: str, reason: str):
        super().__init__(
            message=f"Task processing failed: {reason}",
            status_code=500,
            error_code="TaskProcessingError",
            details={"task_id": task_id, "reason": reason},
        )


class AudioProcessingError(AudioServiceException):
    """Raised when audio processing fails"""

    def __init__(self, reason: str, file_path: Optional[str] = None):
        details = {"reason": reason}
        if file_path:
            details["file_path"] = file_path

        super().__init__(
            message=f"Audio processing failed: {reason}",
            status_code=500,
            error_code="AudioProcessingError",
            details=details,
        )


class InvalidAudioFormatError(AudioServiceException):
    """Raised when audio format is invalid or unsupported"""

    def __init__(self, format_type: str, supported_formats: Optional[list] = None):
        message = f"Unsupported audio format: {format_type}"
        details = {"format": format_type}

        if supported_formats:
            message += f". Supported formats: {', '.join(supported_formats)}"
            details["supported_formats"] = supported_formats

        super().__init__(
            message=message,
            status_code=422,
            error_code="InvalidAudioFormat",
            details=details,
        )


class FeatureExtractionError(AudioServiceException):
    """Raised when feature extraction fails"""

    def __init__(self, feature_name: str, reason: str):
        super().__init__(
            message=f"Feature extraction failed for '{feature_name}': {reason}",
            status_code=500,
            error_code="FeatureExtractionError",
            details={"feature": feature_name, "reason": reason},
        )


class CallbackError(AudioServiceException):
    """Raised when callback to external service fails"""

    def __init__(self, callback_url: str, reason: str):
        super().__init__(
            message=f"Callback to {callback_url} failed: {reason}",
            status_code=500,
            error_code="CallbackError",
            details={"callback_url": callback_url, "reason": reason},
        )


class RateLimitExceededError(AudioServiceException):
    """Raised when rate limit is exceeded"""

    def __init__(self, limit: int, window: str):
        super().__init__(
            message=f"Rate limit exceeded: {limit} requests per {window}",
            status_code=429,
            error_code="RateLimitExceeded",
            details={"limit": limit, "window": window},
        )


class InvalidRequestError(AudioServiceException):
    """Raised for invalid request parameters"""

    def __init__(self, field: str, reason: str):
        super().__init__(
            message=f"Invalid request: {field} - {reason}",
            status_code=422,
            error_code="InvalidRequest",
            details={"field": field, "reason": reason},
        )
