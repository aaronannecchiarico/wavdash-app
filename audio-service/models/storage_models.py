"""
Unified Storage Models
Works with both local and R2 storage
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any, List
from enum import Enum


class StorageProcessingRequest(BaseModel):
    """Request model for storage-based audio processing"""

    storage_path: str = Field(
        ..., min_length=1, description="Path to audio file in storage"
    )
    extract_detailed: bool = Field(
        default=False, description="Whether to extract detailed features"
    )
    callback_url: Optional[str] = Field(
        None, description="URL to notify when processing is complete"
    )
    metadata: Optional[Dict[str, str]] = Field(
        default={}, description="Additional metadata"
    )

    @field_validator("storage_path")
    @classmethod
    def validate_storage_path(cls, v):
        # Allow more flexible path validation for both local and cloud storage
        if not v or v.isspace():
            raise ValueError("Storage path cannot be empty")
        return v.strip()

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "storage_path": "uploads/123/2025/01/01/song.wav",
                "extract_detailed": False,
                "callback_url": "https://your-laravel-app.com/api/audio/processed/123",
                "metadata": {"user_id": "123", "original_filename": "song.wav"},
            }
        }
    )


class StorageProcessingResponse(BaseModel):
    """Response model for storage-based audio processing"""

    task_id: Optional[str] = Field(
        None, description="Celery task ID for async processing"
    )
    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")
    storage_analysis_path: Optional[str] = Field(
        None, description="Path to analysis results in storage"
    )
    storage_processed_path: Optional[str] = Field(
        None, description="Path to processed audio in storage"
    )
    public_urls: Optional[Dict[str, str]] = Field(
        None, description="Public URLs for processed files"
    )
    processing_time: Optional[float] = Field(
        None, description="Processing time in seconds"
    )
    storage_type: Optional[str] = Field(
        None, description="Type of storage used (local/r2)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "abc123-def456-ghi789",
                "status": "completed",
                "message": "Audio processing completed successfully",
                "storage_analysis_path": "processed/2024/08/12/uuid_features.json",
                "storage_processed_path": "processed/2024/08/12/uuid_processed.wav",
                "public_urls": {
                    "analysis": "https://yourdomain.com/storage/processed/2024/08/12/uuid_features.json",
                    "processed": "https://yourdomain.com/storage/processed/2024/08/12/uuid_processed.wav",
                },
                "processing_time": 3.45,
                "storage_type": "local",
            }
        }
    )


class StorageStemSeparationRequest(BaseModel):
    """Request model for storage-based stem separation"""

    storage_path: str = Field(
        ..., min_length=1, description="Path to audio file in storage"
    )
    model_name: str = Field(default="htdemucs", description="Demucs model to use")
    callback_url: Optional[str] = Field(
        None, description="URL to notify when processing is complete"
    )
    metadata: Optional[Dict[str, str]] = Field(
        default={}, description="Additional metadata"
    )

    @field_validator("storage_path")
    @classmethod
    def validate_storage_path(cls, v):
        if not v or v.isspace():
            raise ValueError("Storage path cannot be empty")
        return v.strip()

    @field_validator("model_name")
    @classmethod
    def validate_model_name(cls, v):
        valid_models = ["htdemucs", "htdemucs_ft", "htdemucs_6s", "mdx", "mdx_extra"]
        if v not in valid_models:
            raise ValueError(f'Model must be one of: {", ".join(valid_models)}')
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "storage_path": "uploads/123/2025/01/01/song.wav",
                "model_name": "htdemucs",
                "callback_url": "https://your-laravel-app.com/api/stems/processed/123",
                "metadata": {"user_id": "123", "original_filename": "song.wav"},
            }
        }
    )


class StorageStemSeparationResponse(BaseModel):
    """Response model for storage-based stem separation"""

    task_id: Optional[str] = Field(
        None, description="Celery task ID for async processing"
    )
    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")
    model_used: Optional[str] = Field(None, description="Model used for separation")
    storage_stems_paths: Optional[Dict[str, str]] = Field(
        None, description="Storage paths for separated stems"
    )
    public_urls: Optional[Dict[str, str]] = Field(
        None, description="Public URLs for stem files"
    )
    processing_time: Optional[float] = Field(
        None, description="Processing time in seconds"
    )
    storage_type: Optional[str] = Field(
        None, description="Type of storage used (local/r2)"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "abc123-def456-ghi789",
                "status": "completed",
                "message": "Stem separation completed successfully",
                "model_used": "htdemucs",
                "storage_stems_paths": {
                    "vocals": "stems/2024/08/12/uuid/vocals.wav",
                    "drums": "stems/2024/08/12/uuid/drums.wav",
                    "bass": "stems/2024/08/12/uuid/bass.wav",
                    "other": "stems/2024/08/12/uuid/other.wav",
                },
                "public_urls": {
                    "vocals": "https://yourdomain.com/storage/stems/2024/08/12/uuid/vocals.wav",
                    "drums": "https://yourdomain.com/storage/stems/2024/08/12/uuid/drums.wav",
                    "bass": "https://yourdomain.com/storage/stems/2024/08/12/uuid/bass.wav",
                    "other": "https://yourdomain.com/storage/stems/2024/08/12/uuid/other.wav",
                },
                "processing_time": 45.67,
                "storage_type": "local",
            }
        }
    )


class StorageFileInfo(BaseModel):
    """Model for storage file information"""

    storage_path: str = Field(..., description="Path in storage")
    size: int = Field(..., description="File size in bytes")
    last_modified: str = Field(..., description="Last modified timestamp")
    content_type: str = Field(..., description="MIME type")
    metadata: Dict[str, str] = Field(default={}, description="File metadata")
    public_url: Optional[str] = Field(None, description="Public URL if available")
    storage_type: Optional[str] = Field(None, description="Type of storage (local/r2)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "storage_path": "uploads/123/2025/01/01/song.wav",
                "size": 5242880,
                "last_modified": "2025-01-01T10:30:00Z",
                "content_type": "audio/wav",
                "metadata": {
                    "original_filename": "song.wav",
                    "upload_source": "laravel_app",
                },
                "public_url": "https://yourdomain.com/storage/uploads/123/2025/01/01/song.wav",
                "storage_type": "local",
            }
        }
    )


class StorageCallbackData(BaseModel):
    """Model for callback data sent to Laravel app"""

    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Final status (completed/failed)")
    processing_type: str = Field(..., description="Type of processing (features/stems)")
    storage_paths: Dict[str, str] = Field(..., description="Relevant storage paths")
    analysis_summary: Optional[Dict[str, Any]] = Field(
        None, description="Summary of analysis results"
    )
    error_message: Optional[str] = Field(None, description="Error message if failed")
    processing_time: float = Field(..., description="Total processing time")
    storage_type: str = Field(..., description="Type of storage used (local/r2)")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "abc123-def456-ghi789",
                "status": "completed",
                "processing_type": "features",
                "storage_paths": {
                    "analysis": "processed/2024/08/12/uuid_features.json",
                    "processed": "processed/2024/08/12/uuid_processed.wav",
                },
                "analysis_summary": {
                    "bpm": 120.5,
                    "key": "C major",
                    "key_confidence": 0.82,
                    "loudness_db": -12.3,
                    "brightness": 2000.0,
                    "duration": 180.0,
                },
                "processing_time": 3.45,
                "storage_type": "local",
            }
        }
    )


class StorageBatchProcessingRequest(BaseModel):
    """Request model for batch storage processing"""

    storage_paths: List[str] = Field(
        ..., min_length=1, description="List of storage paths to process"
    )
    processing_type: str = Field(..., description="Type of processing (features|stems)")
    model_name: Optional[str] = Field(
        "htdemucs", description="Model for stem separation"
    )
    callback_url: Optional[str] = Field(
        None, description="URL to notify when batch is complete"
    )
    batch_metadata: Optional[Dict[str, str]] = Field(
        default={}, description="Batch-level metadata"
    )

    @field_validator("processing_type")
    @classmethod
    def validate_processing_type(cls, v):
        if v not in ["features", "stems"]:
            raise ValueError('processing_type must be "features" or "stems"')
        return v

    @field_validator("storage_paths")
    @classmethod
    def validate_storage_paths(cls, v):
        for path in v:
            if not path or path.isspace():
                raise ValueError(f"Invalid storage path: {path}")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "storage_paths": [
                    "uploads/123/2025/01/01/song1.wav",
                    "uploads/123/2025/01/01/song2.wav",
                ],
                "processing_type": "features",
                "callback_url": "https://your-laravel-app.com/api/batch/processed/123",
                "batch_metadata": {"batch_id": "batch_123", "user_id": "456"},
            }
        }
    )
