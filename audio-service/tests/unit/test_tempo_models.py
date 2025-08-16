"""
Unit tests for models.tempo_models module
"""

import pytest
import sys
from pathlib import Path
from pydantic import ValidationError

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.tempo_models import (
    TempoPresetEnum,
    TempoProcessingRequest,
    StorageTempoProcessingRequest,
    TempoProcessingResponse,
    TempoPresetConfig,
    TempoCallbackData
)


class TestTempoModels:
    """Test cases for tempo processing data models"""
    
    def test_tempo_preset_enum_values(self):
        """Test that all tempo preset enum values are valid"""
        expected_values = ["custom", "sped_up", "slowed_reverb", "nightcore", "chopped_screwed", "time_stretched"]
        
        for value in expected_values:
            preset = TempoPresetEnum(value)
            assert preset.value == value
    
    def test_tempo_processing_request_valid(self):
        """Test creating valid TempoProcessingRequest"""
        request = TempoProcessingRequest(
            filename="test.wav",
            preset=TempoPresetEnum.SLOWED_REVERB,
            tempo_factor=0.8,
            pitch_shift_semitones=-1.5,
            preserve_pitch=False,
            add_reverb=True,
            use_stems=False,
            async_processing=True
        )
        
        assert request.filename == "test.wav"
        assert request.preset == TempoPresetEnum.SLOWED_REVERB
        assert request.tempo_factor == 0.8
        assert request.pitch_shift_semitones == -1.5
        assert request.preserve_pitch == False
        assert request.add_reverb == True
        assert request.use_stems == False
        assert request.async_processing == True
    
    def test_tempo_processing_request_defaults(self):
        """Test TempoProcessingRequest with default values"""
        request = TempoProcessingRequest(filename="test.wav")
        
        assert request.filename == "test.wav"
        assert request.preset == TempoPresetEnum.CUSTOM
        assert request.tempo_factor == 1.0
        assert request.pitch_shift_semitones == 0.0
        assert request.preserve_pitch == False
        assert request.add_reverb == False
        assert request.use_stems == False
        assert request.async_processing == True
    
    def test_tempo_processing_request_invalid_filename(self):
        """Test TempoProcessingRequest with invalid filename"""
        with pytest.raises(ValidationError):
            TempoProcessingRequest(filename="")  # Empty filename
    
    def test_tempo_processing_request_invalid_tempo_factor(self):
        """Test TempoProcessingRequest with invalid tempo factor"""
        with pytest.raises(ValidationError):
            TempoProcessingRequest(filename="test.wav", tempo_factor=0.1)  # Too low
        
        with pytest.raises(ValidationError):
            TempoProcessingRequest(filename="test.wav", tempo_factor=5.0)  # Too high
    
    def test_tempo_processing_request_invalid_pitch_shift(self):
        """Test TempoProcessingRequest with invalid pitch shift"""
        with pytest.raises(ValidationError):
            TempoProcessingRequest(filename="test.wav", pitch_shift_semitones=-15.0)  # Too low
        
        with pytest.raises(ValidationError):
            TempoProcessingRequest(filename="test.wav", pitch_shift_semitones=15.0)  # Too high
    
    def test_tempo_processing_request_boundary_values(self):
        """Test TempoProcessingRequest with boundary values"""
        # Test minimum values
        request_min = TempoProcessingRequest(
            filename="test.wav",
            tempo_factor=0.25,
            pitch_shift_semitones=-12.0
        )
        assert request_min.tempo_factor == 0.25
        assert request_min.pitch_shift_semitones == -12.0
        
        # Test maximum values
        request_max = TempoProcessingRequest(
            filename="test.wav", 
            tempo_factor=4.0,
            pitch_shift_semitones=12.0
        )
        assert request_max.tempo_factor == 4.0
        assert request_max.pitch_shift_semitones == 12.0
    
    def test_storage_tempo_processing_request_valid(self):
        """Test creating valid StorageTempoProcessingRequest"""
        request = StorageTempoProcessingRequest(
            storage_path="uploads/123/2025/08/13/test.wav",
            preset=TempoPresetEnum.NIGHTCORE,
            callback_url="https://example.com/callback",
            metadata={"user_id": "123", "upload_id": "456"}
        )
        
        assert request.storage_path == "uploads/123/2025/08/13/test.wav"
        assert request.preset == TempoPresetEnum.NIGHTCORE
        assert request.callback_url == "https://example.com/callback"
        assert request.metadata == {"user_id": "123", "upload_id": "456"}
    
    def test_storage_tempo_processing_request_invalid_storage_path(self):
        """Test StorageTempoProcessingRequest with invalid storage path"""
        with pytest.raises(ValidationError):
            StorageTempoProcessingRequest(storage_path="")  # Empty path
        
        with pytest.raises(ValidationError):
            StorageTempoProcessingRequest(storage_path="   ")  # Whitespace only
    
    def test_storage_tempo_processing_request_defaults(self):
        """Test StorageTempoProcessingRequest with default values"""
        request = StorageTempoProcessingRequest(storage_path="uploads/test.wav")
        
        assert request.storage_path == "uploads/test.wav"
        assert request.preset == TempoPresetEnum.CUSTOM
        assert request.tempo_factor == 1.0
        assert request.pitch_shift_semitones == 0.0
        assert request.preserve_pitch == False
        assert request.add_reverb == False
        assert request.use_stems == False
        assert request.callback_url is None
        assert request.metadata == {}
    
    def test_tempo_processing_response_minimal(self):
        """Test creating minimal TempoProcessingResponse"""
        response = TempoProcessingResponse(
            status="processing",
            message="Processing started"
        )
        
        assert response.status == "processing"
        assert response.message == "Processing started"
        assert response.task_id is None
        assert response.original_analysis is None
        assert response.tempo_processing is None
        assert response.output_files is None
        assert response.public_urls is None
        assert response.processing_time is None
        assert response.storage_type is None
    
    def test_tempo_processing_response_complete(self):
        """Test creating complete TempoProcessingResponse"""
        response = TempoProcessingResponse(
            task_id="abc123",
            status="completed",
            message="Processing completed",
            original_analysis={"bpm": 120.0, "duration": 180.0},
            tempo_processing={"preset": "slowed_reverb", "final_bpm": 90.0},
            output_files={"processed_audio": "path/to/processed.wav"},
            public_urls={"processed_audio": "https://example.com/processed.wav"},
            processing_time=45.2,
            storage_type="local"
        )
        
        assert response.task_id == "abc123"
        assert response.status == "completed"
        assert response.original_analysis["bpm"] == 120.0
        assert response.tempo_processing["preset"] == "slowed_reverb"
        assert response.output_files["processed_audio"] == "path/to/processed.wav"
        assert response.processing_time == 45.2
    
    def test_tempo_preset_config_valid(self):
        """Test creating valid TempoPresetConfig"""
        config = TempoPresetConfig(
            name="Test Preset",
            tempo_factor=1.2,
            pitch_shift_semitones=2.0,
            preserve_pitch=False,
            effects=["pitch_shift", "reverb"],
            reverb_settings={"wet_level": 0.3}
        )
        
        assert config.name == "Test Preset"
        assert config.tempo_factor == 1.2
        assert config.pitch_shift_semitones == 2.0
        assert config.preserve_pitch == False
        assert config.effects == ["pitch_shift", "reverb"]
        assert config.reverb_settings == {"wet_level": 0.3}
    
    def test_tempo_preset_config_invalid_ranges(self):
        """Test TempoPresetConfig with invalid ranges"""
        with pytest.raises(ValidationError):
            TempoPresetConfig(
                name="Invalid", 
                tempo_factor=0.1,  # Too low
                pitch_shift_semitones=0.0
            )
        
        with pytest.raises(ValidationError):
            TempoPresetConfig(
                name="Invalid",
                tempo_factor=1.0,
                pitch_shift_semitones=15.0  # Too high
            )
    
    def test_tempo_callback_data_valid(self):
        """Test creating valid TempoCallbackData"""
        callback_data = TempoCallbackData(
            task_id="abc123",
            status="completed",
            processing_type="tempo",
            storage_paths={"original": "uploads/test.wav", "processed": "processed/test_tempo.wav"},
            processing_time=30.5,
            storage_type="local"
        )
        
        assert callback_data.task_id == "abc123"
        assert callback_data.status == "completed"
        assert callback_data.processing_type == "tempo"
        assert callback_data.storage_paths["original"] == "uploads/test.wav"
        assert callback_data.processing_time == 30.5
        assert callback_data.storage_type == "local"
    
    def test_tempo_callback_data_with_optional_fields(self):
        """Test TempoCallbackData with optional fields"""
        callback_data = TempoCallbackData(
            task_id="abc123",
            status="failed",
            processing_type="tempo",
            storage_paths={"original": "uploads/test.wav"},
            error_message="Processing failed",
            processing_time=15.2,
            storage_type="r2",
            original_analysis={"bpm": 120.0},
            tempo_processing={"preset": "sped_up", "final_bpm": 150.0}
        )
        
        assert callback_data.error_message == "Processing failed"
        assert callback_data.original_analysis["bpm"] == 120.0
        assert callback_data.tempo_processing["preset"] == "sped_up"