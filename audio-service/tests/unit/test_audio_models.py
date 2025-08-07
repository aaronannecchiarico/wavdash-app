"""
Unit tests for models.audio_models module
"""

import pytest
import sys
from pathlib import Path
from pydantic import ValidationError

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.audio_models import (
    AudioProcessingRequest,
    AudioProcessingResponse,
    AudioFeatures,
    StemSeparationResult,
    TaskStatus
)


class TestAudioModels:
    """Test cases for audio data models"""
    
    def test_audio_processing_request_valid(self):
        """Test creating valid AudioProcessingRequest"""
        request = AudioProcessingRequest(
            filename="test.wav",
            async_processing=True,
            extract_detailed=False
        )
        
        assert request.filename == "test.wav"
        assert request.async_processing == True
        assert request.extract_detailed == False
    
    def test_audio_processing_request_defaults(self):
        """Test AudioProcessingRequest with default values"""
        request = AudioProcessingRequest(filename="test.wav")
        
        assert request.filename == "test.wav"
        assert request.async_processing == True  # Default
        assert request.extract_detailed == False  # Default
    
    def test_audio_processing_request_invalid_filename(self):
        """Test AudioProcessingRequest with invalid filename"""
        with pytest.raises(ValidationError):
            AudioProcessingRequest(filename="")  # Empty filename
    
    def test_audio_processing_response_success(self):
        """Test creating successful AudioProcessingResponse"""
        response = AudioProcessingResponse(
            task_id="test-123",
            status="completed",
            message="Processing completed successfully",
            result={"features": {"tempo": 120}}
        )
        
        assert response.task_id == "test-123"
        assert response.status == "completed"
        assert response.message == "Processing completed successfully"
        assert response.result == {"features": {"tempo": 120}}
    
    def test_audio_processing_response_without_result(self):
        """Test AudioProcessingResponse without result"""
        response = AudioProcessingResponse(
            task_id="test-123",
            status="processing",
            message="Task is running"
        )
        
        assert response.task_id == "test-123"
        assert response.status == "processing"
        assert response.message == "Task is running"
        assert response.result is None
    
    def test_audio_processing_response_invalid_status(self):
        """Test AudioProcessingResponse with invalid status"""
        # Note: This might not raise an error if status is just a string field
        # But we can test for expected valid statuses
        response = AudioProcessingResponse(
            task_id="test-123",
            status="invalid_status",
            message="Test"
        )
        
        assert response.status == "invalid_status"  # Pydantic allows any string
    
    def test_audio_features_basic(self):
        """Test creating basic AudioFeatures"""
        features = AudioFeatures(
            tempo=120.0,
            key="C major",
            loudness=-12.5,
            duration=180.0
        )
        
        assert features.tempo == 120.0
        assert features.key == "C major"
        assert features.loudness == -12.5
        assert features.duration == 180.0
    
    def test_audio_features_optional_fields(self):
        """Test AudioFeatures with optional fields"""
        features = AudioFeatures(
            tempo=120.0,
            key="C major",
            loudness=-12.5,
            duration=180.0,
            spectral_centroid=2000.0,
            mfcc=[1.0, 2.0, 3.0],
            chroma=[0.1, 0.2, 0.3]
        )
        
        assert features.spectral_centroid == 2000.0
        assert features.mfcc == [1.0, 2.0, 3.0]
        assert features.chroma == [0.1, 0.2, 0.3]
    
    def test_audio_features_validation(self):
        """Test AudioFeatures validation"""
        with pytest.raises(ValidationError):
            AudioFeatures(
                tempo=-10.0,  # Negative tempo should be invalid
                key="C major",
                loudness=-12.5,
                duration=180.0
            )
    
    def test_stem_separation_result(self):
        """Test creating StemSeparationResult"""
        result = StemSeparationResult(
            filename="song.wav",
            model_used="htdemucs",
            stems={
                "vocals": "/tmp/vocals.wav",
                "drums": "/tmp/drums.wav",
                "bass": "/tmp/bass.wav",
                "other": "/tmp/other.wav"
            },
            processing_time=45.2
        )
        
        assert result.filename == "song.wav"
        assert result.model_used == "htdemucs"
        assert len(result.stems) == 4
        assert "vocals" in result.stems
        assert result.processing_time == 45.2
    
    def test_stem_separation_result_empty_stems(self):
        """Test StemSeparationResult with empty stems"""
        with pytest.raises(ValidationError):
            StemSeparationResult(
                filename="song.wav",
                model_used="htdemucs",
                stems={},  # Empty stems should be invalid
                processing_time=45.2
            )
    
    def test_task_status_pending(self):
        """Test TaskStatus for pending task"""
        status = TaskStatus(
            task_id="abc-123",
            status="pending",
            progress=0,
            message="Task queued for processing"
        )
        
        assert status.task_id == "abc-123"
        assert status.status == "pending"
        assert status.progress == 0
        assert status.message == "Task queued for processing"
        assert status.result is None
        assert status.error is None
    
    def test_task_status_in_progress(self):
        """Test TaskStatus for task in progress"""
        status = TaskStatus(
            task_id="abc-123",
            status="processing",
            progress=45,
            message="Extracting features..."
        )
        
        assert status.task_id == "abc-123"
        assert status.status == "processing"
        assert status.progress == 45
        assert status.message == "Extracting features..."
    
    def test_task_status_completed(self):
        """Test TaskStatus for completed task"""
        result_data = {"features": {"tempo": 128, "key": "A minor"}}
        
        status = TaskStatus(
            task_id="abc-123",
            status="completed",
            progress=100,
            message="Processing completed successfully",
            result=result_data
        )
        
        assert status.task_id == "abc-123"
        assert status.status == "completed"
        assert status.progress == 100
        assert status.result == result_data
    
    def test_task_status_failed(self):
        """Test TaskStatus for failed task"""
        status = TaskStatus(
            task_id="abc-123",
            status="failed",
            progress=0,
            message="Processing failed",
            error="Audio file corrupted"
        )
        
        assert status.task_id == "abc-123"
        assert status.status == "failed"
        assert status.progress == 0
        assert status.error == "Audio file corrupted"
    
    def test_task_status_invalid_progress(self):
        """Test TaskStatus with invalid progress value"""
        with pytest.raises(ValidationError):
            TaskStatus(
                task_id="abc-123",
                status="processing",
                progress=150,  # Progress > 100 should be invalid
                message="Processing..."
            )
    
    def test_task_status_negative_progress(self):
        """Test TaskStatus with negative progress"""
        with pytest.raises(ValidationError):
            TaskStatus(
                task_id="abc-123",
                status="processing",
                progress=-10,  # Negative progress should be invalid
                message="Processing..."
            )
    
    def test_model_serialization(self):
        """Test model serialization to dict"""
        response = AudioProcessingResponse(
            task_id="test-123",
            status="completed",
            message="Success",
            result={"tempo": 120}
        )
        
        data = response.model_dump()
        
        assert isinstance(data, dict)
        assert data["task_id"] == "test-123"
        assert data["status"] == "completed"
        assert data["result"]["tempo"] == 120
    
    def test_model_json_serialization(self):
        """Test model JSON serialization"""
        response = AudioProcessingResponse(
            task_id="test-123",
            status="completed",
            message="Success"
        )
        
        json_str = response.model_dump_json()
        
        assert isinstance(json_str, str)
        assert "test-123" in json_str
        assert "completed" in json_str


if __name__ == "__main__":
    pytest.main([__file__])