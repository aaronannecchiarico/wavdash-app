from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, Any, List
from enum import Enum


class TaskStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AudioProcessingRequest(BaseModel):
    """Request model for audio processing"""
    filename: str = Field(..., min_length=1, description="Name of the audio file")
    async_processing: bool = Field(default=True, description="Whether to process asynchronously") 
    extract_detailed: bool = Field(default=False, description="Whether to extract detailed features")
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "filename": "sample.wav",
                "async_processing": True
            }
        }
    )


class AudioProcessingResponse(BaseModel):
    """Response model for audio processing"""
    task_id: Optional[str] = Field(None, description="Celery task ID for async processing")
    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")
    result: Optional[Dict[str, Any]] = Field(None, description="Processing results")
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "task_id": "abc123-def456-ghi789",
                "status": "processing",
                "message": "Audio processing started",
                "result": None
            }
        }
    )


class AudioFeatures(BaseModel):
    """Model for audio features - simplified for testing"""
    tempo: float = Field(..., description="Estimated tempo in BPM", gt=0)
    key: str = Field(..., description="Detected musical key")
    loudness: float = Field(..., description="Overall loudness in dB")
    duration: float = Field(..., description="Audio duration in seconds", gt=0)
    spectral_centroid: Optional[float] = Field(None, description="Spectral centroid")
    mfcc: Optional[List[float]] = Field(None, description="MFCC coefficients")
    chroma: Optional[List[float]] = Field(None, description="Chroma features")
    
    @field_validator('tempo')
    @classmethod
    def tempo_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError('Tempo must be positive')
        return v
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "tempo": 120.0,
                "key": "C major",
                "loudness": -12.5,
                "duration": 180.0,
                "spectral_centroid": 2000.0,
                "mfcc": [1.0, 2.0, 3.0],
                "chroma": [0.1, 0.2, 0.3]
            }
        }
    )


class StemSeparationRequest(BaseModel):
    """Request model for stem separation"""
    filename: str = Field(..., description="Name of the audio file")
    model_name: str = Field(default="htdemucs", description="Demucs model to use")
    async_processing: bool = Field(default=True, description="Whether to process asynchronously")
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "filename": "song.wav",
                "model_name": "htdemucs",
                "async_processing": True
            }
        }
    )


class StemSeparationResult(BaseModel):
    """Result model for stem separation"""
    filename: str = Field(..., description="Original filename")
    model_used: str = Field(..., description="Demucs model used")
    stems: Dict[str, str] = Field(..., description="Separated stems file paths")
    processing_time: float = Field(..., description="Processing time in seconds")
    
    @field_validator('stems')
    @classmethod
    def stems_not_empty(cls, v):
        if not v:
            raise ValueError('Stems dictionary cannot be empty')
        return v
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "filename": "song.wav",
                "model_used": "htdemucs",
                "stems": {
                    "vocals": "/path/to/vocals.wav",
                    "drums": "/path/to/drums.wav",
                    "bass": "/path/to/bass.wav",
                    "other": "/path/to/other.wav"
                },
                "processing_time": 45.2
            }
        }
    )


class StemSeparationResponse(BaseModel):
    """Response model for stem separation"""
    task_id: Optional[str] = Field(None, description="Celery task ID for async processing")
    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")
    stems: Optional[Dict[str, str]] = Field(None, description="Separated stems file paths")
    model_used: Optional[str] = Field(None, description="Model used for separation")
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "task_id": "abc123-def456-ghi789",
                "status": "completed",
                "message": "Stem separation completed",
                "stems": {
                    "vocals": "/path/to/vocals.wav",
                    "drums": "/path/to/drums.wav",
                    "bass": "/path/to/bass.wav",
                    "other": "/path/to/other.wav"
                },
                "model_used": "htdemucs"
            }
        }
    )


class TaskStatus(BaseModel):
    """Model for task status - matches test expectations"""
    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Task status")
    progress: int = Field(..., description="Progress percentage", ge=0, le=100)
    message: Optional[str] = Field(None, description="Status message")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    @field_validator('progress')
    @classmethod 
    def progress_valid_range(cls, v):
        if v < 0 or v > 100:
            raise ValueError('Progress must be between 0 and 100')
        return v
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "task_id": "abc123-def456-ghi789",
                "status": "processing",
                "progress": 75,
                "message": "Extracting audio features",
                "result": None,
                "error": None
            }
        }
    )


class TaskStatusResponse(BaseModel):
    """Response model for task status"""
    task_id: str = Field(..., description="Celery task ID")
    status: str = Field(..., description="Task status")
    message: Optional[str] = Field(None, description="Status message")
    progress: Optional[int] = Field(None, description="Progress percentage")
    result: Optional[Dict[str, Any]] = Field(None, description="Task result")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "task_id": "abc123-def456-ghi789",
                "status": "processing",
                "message": "Extracting audio features",
                "progress": 75,
                "result": None,
                "error": None
            }
        }
    )


class BatchProcessingRequest(BaseModel):
    """Request model for batch processing"""
    filenames: List[str] = Field(..., description="List of audio file names")
    processing_type: str = Field(..., description="Type of processing (features|stems)")
    model_name: Optional[str] = Field("htdemucs", description="Model for stem separation")
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "filenames": ["song1.wav", "song2.wav"],
                "processing_type": "features",
                "model_name": "htdemucs"
            }
        }
    )


class HealthCheckResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service status")
    redis_connected: Optional[Dict[str, Any]] = Field(None, description="Redis connection status")
    version: str = Field("1.0.0", description="Service version")
    
    model_config = ConfigDict(
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "redis_connected": {"worker1": "pong"},
                "version": "1.0.0"
            }
        }
    )