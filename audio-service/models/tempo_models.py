"""
Tempo Processing Models
Models for sped-up and slowed-down audio processing
"""

from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TempoPresetEnum(str, Enum):
    """Available tempo processing presets"""

    CUSTOM = "custom"
    SPED_UP = "sped_up"
    SLOWED_REVERB = "slowed_reverb"
    NIGHTCORE = "nightcore"
    CHOPPED_SCREWED = "chopped_screwed"
    TIME_STRETCHED = "time_stretched"


class StorageTempoProcessingRequest(BaseModel):
    """Request model for storage-based tempo processing"""

    storage_path: str = Field(
        ..., min_length=1, description="Path to audio file in storage"
    )
    preset: TempoPresetEnum = Field(
        default=TempoPresetEnum.CUSTOM, description="Processing preset"
    )
    tempo_factor: float = Field(
        default=1.0,
        ge=0.25,
        le=4.0,
        description="Tempo multiplication factor (0.25-4.0)",
    )
    pitch_shift_semitones: float = Field(
        default=0.0,
        ge=-12.0,
        le=12.0,
        description="Pitch shift in semitones (-12 to +12)",
    )
    preserve_pitch: bool = Field(
        default=False, description="Use time stretching to preserve pitch"
    )
    add_reverb: bool = Field(default=False, description="Add reverb effect")
    use_stems: bool = Field(
        default=False, description="Process stems separately for higher quality"
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
        if not v or v.isspace():
            raise ValueError("Storage path cannot be empty")
        return v.strip()

    @field_validator("tempo_factor")
    @classmethod
    def validate_tempo_factor(cls, v):
        if not 0.25 <= v <= 4.0:
            raise ValueError("Tempo factor must be between 0.25 and 4.0")
        return v

    @field_validator("pitch_shift_semitones")
    @classmethod
    def validate_pitch_shift(cls, v):
        if not -12.0 <= v <= 12.0:
            raise ValueError("Pitch shift must be between -12 and +12 semitones")
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "storage_path": "uploads/123/2025/08/13/song.wav",
                "preset": "slowed_reverb",
                "tempo_factor": 0.75,
                "pitch_shift_semitones": -2.0,
                "preserve_pitch": False,
                "add_reverb": True,
                "use_stems": True,
                "callback_url": "https://your-laravel-app.com/api/tempo/processed/123",
                "metadata": {
                    "user_id": "123",
                    "upload_id": "456",
                    "original_filename": "song.wav",
                },
            }
        }
    )


class TempoProcessingResponse(BaseModel):
    """Response model for tempo processing"""

    task_id: Optional[str] = Field(
        None, description="Celery task ID for async processing"
    )
    status: str = Field(..., description="Processing status")
    message: str = Field(..., description="Status message")
    original_analysis: Optional[Dict[str, Any]] = Field(
        None, description="Original audio analysis data"
    )
    tempo_processing: Optional[Dict[str, Any]] = Field(
        None, description="Tempo processing details"
    )
    output_files: Optional[Dict[str, Any]] = Field(
        None, description="Output file paths"
    )
    output_file: Optional[Dict[str, Any]] = Field(
        None,
        description="Direct processing output file info (path, filename, size, etc.)",
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
    smart_suggestions: Optional[Dict[str, Any]] = Field(
        None,
        description="AI-generated preset suggestions based on audio characteristics",
    )
    processing_warnings: Optional[Dict[str, str]] = Field(
        None, description="Validation warnings about processing parameters"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "abc123-def456-ghi789",
                "status": "completed",
                "message": "Tempo processing completed successfully",
                "original_analysis": {
                    "bpm": 120.5,
                    "key": "C major",
                    "duration": 180.0,
                },
                "tempo_processing": {
                    "preset": "slowed_reverb",
                    "tempo_factor": 0.75,
                    "pitch_shift_semitones": -2.0,
                    "final_bpm": 90.4,
                    "processing_method": "full_mix",
                    "effects_applied": ["pitch_shift", "reverb"],
                },
                "output_files": {
                    "processed_audio": "processed/123/2025/08/13/song_tempo_slowed_reverb.wav"
                },
                "public_urls": {
                    "processed_audio": "https://yourdomain.com/storage/processed/123/2025/08/13/song_tempo_slowed_reverb.wav"
                },
                "processing_time": 45.2,
                "storage_type": "local",
            }
        }
    )


class TempoPresetConfig(BaseModel):
    """Configuration for tempo processing presets"""

    name: str = Field(..., description="Preset name")
    tempo_factor: float = Field(
        ..., ge=0.25, le=4.0, description="Tempo multiplication factor"
    )
    pitch_shift_semitones: float = Field(
        ..., ge=-12.0, le=12.0, description="Pitch shift in semitones"
    )
    preserve_pitch: bool = Field(default=False, description="Whether to preserve pitch")
    effects: List[str] = Field(default=[], description="List of effects to apply")
    reverb_settings: Optional[Dict[str, float]] = Field(
        None, description="Reverb effect settings"
    )
    filter_settings: Optional[Dict[str, float]] = Field(
        None, description="Filter effect settings"
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name": "slowed_reverb",
                "tempo_factor": 0.75,
                "pitch_shift_semitones": -2.0,
                "preserve_pitch": False,
                "effects": ["pitch_shift", "reverb"],
                "reverb_settings": {"wet_level": 0.3, "room_size": 0.4, "damping": 0.5},
            }
        }
    )


class TempoCallbackData(BaseModel):
    """Model for tempo processing callback data sent to external services"""

    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Final status (completed/failed)")
    processing_type: str = Field(default="tempo", description="Type of processing")
    original_analysis: Optional[Dict[str, Any]] = Field(
        None, description="Original audio analysis"
    )
    tempo_processing: Optional[Dict[str, Any]] = Field(
        None, description="Tempo processing details"
    )
    storage_paths: Dict[str, Any] = Field(..., description="Relevant storage paths")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    processing_time: float = Field(..., description="Total processing time")
    storage_type: str = Field(..., description="Type of storage used (local/r2)")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v not in ["completed", "failed", "pending", "processing"]:
            raise ValueError(
                "status must be one of: completed, failed, pending, processing"
            )
        return v

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_id": "abc123-def456-ghi789",
                "status": "completed",
                "processing_type": "tempo",
                "original_analysis": {
                    "bpm": 120.5,
                    "key": "C major",
                    "duration": 180.0,
                },
                "tempo_processing": {
                    "preset": "slowed_reverb",
                    "tempo_factor": 0.75,
                    "pitch_shift_semitones": -2.0,
                    "final_bpm": 90.4,
                    "processing_method": "stems_separate",
                    "effects_applied": ["pitch_shift", "reverb"],
                },
                "storage_paths": {
                    "processed_audio": "processed/123/2025/08/13/song_tempo_slowed_reverb.wav",
                    "original": "uploads/123/2025/08/13/song.wav",
                },
                "processing_time": 45.2,
                "storage_type": "local",
            }
        }
    )
