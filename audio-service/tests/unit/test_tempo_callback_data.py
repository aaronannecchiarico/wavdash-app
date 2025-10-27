"""
Tests for enhanced tempo processing callback data structure
"""

from unittest.mock import MagicMock, Mock, patch

import pytest

from models.tempo_models import TempoCallbackData


class TestTempoCallbackData:
    """Test the enhanced tempo callback data structure"""

    def test_complete_callback_data_structure(self):
        """Test that callback data includes all required fields"""
        callback_data = TempoCallbackData(
            task_id="test-task-123",
            status="completed",
            processing_type="tempo",
            original_analysis={
                "bpm": 120.0,
                "duration": 180.0,
                "sample_rate": 44100,
                "key": "C major",
            },
            tempo_processing={
                "preset": "nightcore",
                "tempo_factor": 1.4,
                "pitch_shift_semitones": 4.0,
                "preserve_pitch": False,
                "processing_method": "direct",
                "effects_applied": ["tempo_change", "pitch_shift", "brightness_boost"],
                "final_bpm": 168.0,
                "quality_score": 0.9,
                "processing_warnings": [],
            },
            storage_paths={
                "processed_audio": "processed/123/2025/08/17/song_tempo_nightcore-140.wav",
                "original": "uploads/123/2025/08/15/song.mp3",
            },
            processing_time=45.2,
            storage_type="local",
        )

        # Verify all required fields are present
        data_dict = callback_data.model_dump()

        assert data_dict["task_id"] == "test-task-123"
        assert data_dict["status"] == "completed"
        assert data_dict["processing_type"] == "tempo"
        assert data_dict["processing_time"] == 45.2
        assert data_dict["storage_type"] == "local"

        # Verify original_analysis structure
        original = data_dict["original_analysis"]
        assert original["bpm"] == 120.0
        assert original["duration"] == 180.0
        assert original["sample_rate"] == 44100
        assert original["key"] == "C major"

        # Verify tempo_processing structure
        tempo = data_dict["tempo_processing"]
        assert tempo["preset"] == "nightcore"
        assert tempo["tempo_factor"] == 1.4
        assert tempo["pitch_shift_semitones"] == 4.0
        assert tempo["preserve_pitch"] is False
        assert tempo["processing_method"] == "direct"
        assert tempo["final_bpm"] == 168.0
        assert tempo["quality_score"] == 0.9
        assert tempo["processing_warnings"] == []
        assert "tempo_change" in tempo["effects_applied"]
        assert "pitch_shift" in tempo["effects_applied"]
        assert "brightness_boost" in tempo["effects_applied"]

        # Verify storage_paths structure
        paths = data_dict["storage_paths"]
        assert "processed_audio" in paths
        assert "original" in paths
        assert paths["processed_audio"].endswith("song_tempo_nightcore-140.wav")

    def test_callback_data_with_warnings(self):
        """Test callback data with processing warnings"""
        callback_data = TempoCallbackData(
            task_id="test-task-456",
            status="completed",
            processing_type="tempo",
            tempo_processing={
                "preset": "custom",
                "tempo_factor": 2.5,
                "pitch_shift_semitones": 10.0,
                "preserve_pitch": False,
                "processing_method": "direct",
                "effects_applied": ["tempo_change", "pitch_shift"],
                "final_bpm": 300.0,
                "quality_score": 0.6,
                "processing_warnings": [
                    "Very fast tempo may cause audio artifacts",
                    "Large pitch shifts may cause unnatural sound",
                    "Combining high tempo and pitch changes may degrade quality",
                ],
            },
            storage_paths={
                "processed_audio": "processed/456/2025/08/17/track_tempo_custom-250-pitch+10.wav",
                "original": "uploads/456/2025/08/15/track.wav",
            },
            processing_time=120.5,
            storage_type="local",
        )

        data_dict = callback_data.model_dump()
        tempo = data_dict["tempo_processing"]

        assert tempo["quality_score"] == 0.6
        assert len(tempo["processing_warnings"]) == 3
        assert (
            "Very fast tempo may cause audio artifacts" in tempo["processing_warnings"]
        )
        assert (
            "Large pitch shifts may cause unnatural sound"
            in tempo["processing_warnings"]
        )
        assert (
            "Combining high tempo and pitch changes may degrade quality"
            in tempo["processing_warnings"]
        )

    def test_failed_callback_data(self):
        """Test callback data for failed processing"""
        callback_data = TempoCallbackData(
            task_id="test-task-789",
            status="failed",
            processing_type="tempo",
            storage_paths={"original": "uploads/789/2025/08/15/corrupted.mp3"},
            error_message="File format not supported",
            processing_time=5.2,
            storage_type="local",
        )

        data_dict = callback_data.model_dump()

        assert data_dict["status"] == "failed"
        assert data_dict["error_message"] == "File format not supported"
        assert data_dict["processing_time"] == 5.2
        assert "original" in data_dict["storage_paths"]
        assert "processed_audio" not in data_dict["storage_paths"]

    def test_callback_data_with_stem_processing(self):
        """Test callback data for stem-based processing"""
        callback_data = TempoCallbackData(
            task_id="test-task-stems",
            status="completed",
            processing_type="tempo",
            tempo_processing={
                "preset": "slowed_reverb",
                "tempo_factor": 0.75,
                "pitch_shift_semitones": -2.0,
                "preserve_pitch": False,
                "processing_method": "stems_separate",
                "effects_applied": ["tempo_change", "pitch_shift", "reverb"],
                "final_bpm": 90.0,
                "quality_score": 0.95,
                "processing_warnings": [],
            },
            storage_paths={
                "processed_audio": "processed/999/2025/08/17/track_tempo_slowed-reverb-75-pitch-2.wav",
                "original": "uploads/999/2025/08/15/track.wav",
            },
            processing_time=180.3,
            storage_type="r2",
        )

        data_dict = callback_data.model_dump()
        tempo = data_dict["tempo_processing"]

        assert tempo["processing_method"] == "stems_separate"
        assert "reverb" in tempo["effects_applied"]
        assert data_dict["storage_type"] == "r2"
        assert tempo["quality_score"] == 0.95


class TestCallbackDataIntegration:
    """Test callback data integration with the processing pipeline"""

    @patch("tasks.tempo_processing.requests.post")
    def test_callback_sent_with_complete_data(self, mock_post):
        """Test that callbacks are sent with complete data structure"""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Import here to avoid circular imports
        from tasks.tempo_processing import process_tempo_from_storage

        # Mock all the dependencies
        with (
            patch("tasks.tempo_processing.get_storage_service") as mock_storage_service,
            patch("tasks.tempo_processing.get_storage_type") as mock_storage_type,
            patch("tasks.tempo_processing.librosa.load") as mock_load,
            patch("tasks.tempo_processing.librosa.beat.tempo") as mock_tempo,
            patch("tasks.tempo_processing.apply_tempo_processing") as mock_apply,
            patch("tasks.tempo_processing.sf.write") as mock_sf_write,
            patch("tasks.tempo_processing.get_performance_cache") as mock_cache,
            patch("tasks.tempo_processing.tempfile.NamedTemporaryFile") as mock_temp,
            patch("tasks.tempo_processing.os.unlink"),
            patch("tasks.tempo_processing.current_task"),
        ):
            # Setup mocks
            mock_storage = Mock()
            mock_storage.file_exists.return_value = True
            mock_storage.download_file.return_value = True
            mock_storage.upload_file.return_value = True
            mock_storage.get_public_url.return_value = (
                "http://example.com/processed.wav"
            )
            mock_storage_service.return_value = mock_storage

            mock_storage_type.return_value.value = "local"

            # Mock audio loading
            import numpy as np

            mock_audio_data = np.array(
                [1, 2, 3, 4, 5], dtype=np.float32
            )  # Simple mock data
            mock_load.return_value = (mock_audio_data, 44100)
            mock_tempo.return_value = [120.0]

            # Mock cache
            mock_cache_instance = Mock()
            mock_cache_instance.get_cached_bpm_analysis.return_value = None
            mock_cache_instance.get_cached_processed_audio.return_value = None
            mock_cache.return_value = mock_cache_instance

            # Mock processing
            mock_apply.return_value = mock_audio_data

            # Mock temporary file
            mock_temp_file = Mock()
            mock_temp_file.name = "/tmp/test.wav"
            mock_temp.return_value.__enter__ = Mock(return_value=mock_temp_file)
            mock_temp.return_value.__exit__ = Mock()

            # Call the function directly - the 'self' parameter is handled by the task decorator
            result = process_tempo_from_storage(
                task_id="test-123",
                storage_path="uploads/1/2025/08/15/test.mp3",
                preset="nightcore",
                tempo_factor=1.4,
                pitch_shift_semitones=4.0,
                callback_url="http://example.com/callback",
                metadata={"user_id": "1", "original_filename": "test.mp3"},
            )

            # Verify callback was called
            assert mock_post.called
            call_args = mock_post.call_args

            # Verify URL - check positional args first, then keyword args
            if len(call_args[0]) > 0:
                assert (
                    call_args[0][0] == "http://example.com/callback"
                )  # Positional arg
            else:
                assert (
                    call_args[1]["url"] == "http://example.com/callback"
                )  # Keyword arg

            # Verify callback data structure
            callback_json = call_args[1]["json"]
            assert callback_json["task_id"] == "test-123"
            assert callback_json["status"] == "completed"
            assert callback_json["processing_type"] == "tempo"

            # Verify tempo_processing is populated
            assert "tempo_processing" in callback_json
            tempo_data = callback_json["tempo_processing"]
            assert tempo_data["preset"] == "nightcore"
            assert tempo_data["tempo_factor"] == 1.4
            assert tempo_data["pitch_shift_semitones"] == 4.0
            assert "quality_score" in tempo_data
            assert "processing_warnings" in tempo_data
            assert "effects_applied" in tempo_data

            # Verify original_analysis is populated
            assert "original_analysis" in callback_json
            original_data = callback_json["original_analysis"]
            assert "bpm" in original_data
            assert "duration" in original_data
            assert "sample_rate" in original_data

            # Verify storage_paths uses descriptive naming
            assert "storage_paths" in callback_json
            paths = callback_json["storage_paths"]
            assert "processed_audio" in paths
            processed_path = paths["processed_audio"]
            assert "nightcore-140" in processed_path or "nightcore" in processed_path

    def test_callback_data_validation(self):
        """Test that callback data validates according to the model"""
        # Test valid data
        valid_data = {
            "task_id": "test-123",
            "status": "completed",
            "processing_type": "tempo",
            "storage_paths": {
                "processed_audio": "processed/1/2025/08/17/test_tempo_nightcore-140.wav"
            },
            "processing_time": 30.5,
            "storage_type": "local",
        }

        callback = TempoCallbackData(**valid_data)
        assert callback.task_id == "test-123"

        # Test invalid status should raise validation error
        with pytest.raises(ValueError):
            invalid_data = valid_data.copy()
            invalid_data["status"] = "invalid_status"
            TempoCallbackData(**invalid_data)
