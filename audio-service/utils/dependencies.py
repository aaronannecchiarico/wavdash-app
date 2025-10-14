"""
FastAPI Dependency Injection
Reusable dependencies for route handlers
"""

import logging
from typing import Optional
from fastapi import Depends, HTTPException

from services.storage_service import (
    get_storage_service as _get_storage_service,
    is_storage_enabled as _is_storage_enabled,
    get_storage_type as _get_storage_type,
    StorageService,
    StorageType
)
from utils.exceptions import StorageNotEnabledError


logger = logging.getLogger(__name__)


def get_storage_service() -> StorageService:
    """
    Dependency to get the storage service instance

    Automatically validates that storage is enabled before returning service

    Raises:
        StorageNotEnabledError: If storage is not properly configured

    Returns:
        StorageService: Configured storage service instance
    """
    if not _is_storage_enabled():
        raise StorageNotEnabledError()

    return _get_storage_service()


def get_storage_type_dependency() -> StorageType:
    """
    Dependency to get the current storage type

    Returns:
        StorageType: The configured storage type (local, s3, r2, gcs)
    """
    return _get_storage_type()


class StorageValidator:
    """
    Dependency class for storage-related validations

    Usage:
        @router.post("/endpoint")
        async def endpoint(validator: StorageValidator = Depends()):
            validator.validate_file_exists(storage_path)
    """

    def __init__(self, storage: StorageService = Depends(get_storage_service)):
        self.storage = storage

    def validate_file_exists(self, storage_path: str) -> None:
        """
        Validate that a file exists in storage

        Args:
            storage_path: Path to validate

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        from utils.exceptions import FileNotFoundError

        if not self.storage.file_exists(storage_path):
            raise FileNotFoundError(storage_path)

    def get_file_info(self, storage_path: str) -> dict:
        """
        Get file information with automatic existence check

        Args:
            storage_path: Path to the file

        Returns:
            dict: File information

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        from utils.exceptions import FileNotFoundError

        file_info = self.storage.get_file_info(storage_path)
        if not file_info:
            raise FileNotFoundError(storage_path)

        return file_info


class RequestValidator:
    """
    Dependency class for request validation

    Usage:
        @router.post("/endpoint")
        async def endpoint(validator: RequestValidator = Depends()):
            validator.validate_required_field(value, "field_name")
    """

    @staticmethod
    def validate_required_field(value: Optional[str], field_name: str) -> None:
        """
        Validate that a required field is present

        Args:
            value: The field value
            field_name: Name of the field

        Raises:
            InvalidRequestError: If field is missing
        """
        from utils.exceptions import InvalidRequestError

        if not value:
            raise InvalidRequestError(field_name, "field is required")

    @staticmethod
    def validate_storage_path(storage_path: str) -> None:
        """
        Validate storage path format

        Args:
            storage_path: Path to validate

        Raises:
            InvalidStoragePathError: If path format is invalid
        """
        from utils.exceptions import InvalidStoragePathError

        if not storage_path:
            raise InvalidStoragePathError(storage_path, "path cannot be empty")

        # Add more validation rules as needed
        if ".." in storage_path:
            raise InvalidStoragePathError(storage_path, "path cannot contain '..'")

        if storage_path.startswith("/"):
            raise InvalidStoragePathError(storage_path, "path should not start with '/'")


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Dependency to get a logger instance

    Args:
        name: Logger name (defaults to module name)

    Returns:
        logging.Logger: Configured logger
    """
    return logging.getLogger(name)
