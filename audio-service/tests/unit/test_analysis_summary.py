#!/usr/bin/env python3
"""
Unit tests for analysis summary generation in storage processing
"""

import sys
import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tasks.storage_processing import process_audio_features_from_storage


class TestAnalysisSummary:
    """Test analysis summary generation"""

    def test_analysis_summary_single_chunk(self):
        """Test analysis summary generation for single-chunk processing"""
        # Mock feature result for single chunk (short audio)
        mock_feature_result = {
            "metadata": {"duration": 30.0},
            "features": {
                "tempo": {"bpm": 120.5},
                "key": {"key": "C major", "confidence": 0.85},
                "energy": {"overall_loudness_db": -12.3},
                "spectral": {"spectral_centroid": {"mean": 2000.0}},
            },
        }

        with patch(
            "tasks.storage_processing.get_storage_service"
        ) as mock_storage_service, patch(
            "tasks.storage_processing.get_storage_type"
        ) as mock_storage_type, patch(
            "tasks.storage_processing.current_task"
        ) as mock_current_task, patch(
            "tasks.storage_processing.create_feature_extractor"
        ) as mock_extractor, patch(
            "tasks.storage_processing.tempfile.NamedTemporaryFile"
        ) as mock_tempfile, patch(
            "tasks.storage_processing.os.unlink"
        ):

            # Setup mocks
            mock_storage = MagicMock()
            mock_storage_service.return_value = mock_storage
            mock_storage.file_exists.return_value = True
            mock_storage.download_file.return_value = True
            mock_storage.upload_analysis_result.return_value = (
                "processed/1/2025/08/13/test_features.json"
            )

            mock_type_obj = MagicMock()
            mock_type_obj.value = "local"
            mock_storage_type.return_value = mock_type_obj

            mock_feature_extractor = MagicMock()
            mock_extractor.return_value = mock_feature_extractor
            mock_feature_extractor.extract_features.return_value = mock_feature_result

            mock_temp = MagicMock()
            mock_temp.name = "/tmp/test.mp3"
            mock_tempfile.return_value.__enter__.return_value = mock_temp

            # Execute
            result = process_audio_features_from_storage(
                "test-task-id",
                "uploads/1/2025/08/13/test.mp3",
                False,
                None,
                {"user_id": "1", "upload_id": "123"},
            )

            # Verify analysis summary
            analysis = result["analysis_summary"]
            assert analysis is not None
            assert analysis["bpm"] == 120.5
            assert analysis["key"] == "C major"
            assert analysis["key_confidence"] == 0.85
            assert analysis["loudness_db"] == -12.3
            assert analysis["brightness"] == 2000.0
            assert analysis["duration"] == 30.0

            # Verify storage path includes user_id
            assert (
                result["storage_analysis_path"]
                == "processed/1/2025/08/13/test_features.json"
            )

    def test_analysis_summary_multi_chunk(self):
        """Test analysis summary generation for multi-chunk processing"""
        # Mock feature result for multi-chunk (long audio)
        mock_feature_result = {
            "metadata": {"duration": 180.0},
            "chunk_count": 6,
            "aggregated_features": {
                "tempo": {"mean_bpm": 115.2, "std_bpm": 2.1},
                "key": {
                    "most_likely_key": "A minor",
                    "confidence": 0.75,
                    "key_changes": 2,
                },
                "energy": {"mean_loudness_db": -15.8, "std_loudness_db": 1.2},
                "spectral": {"mean_brightness": 1500.5, "std_brightness": 200.3},
            },
        }

        with patch(
            "tasks.storage_processing.get_storage_service"
        ) as mock_storage_service, patch(
            "tasks.storage_processing.get_storage_type"
        ) as mock_storage_type, patch(
            "tasks.storage_processing.current_task"
        ) as mock_current_task, patch(
            "tasks.storage_processing.create_feature_extractor"
        ) as mock_extractor, patch(
            "tasks.storage_processing.tempfile.NamedTemporaryFile"
        ) as mock_tempfile, patch(
            "tasks.storage_processing.os.unlink"
        ):

            # Setup mocks
            mock_storage = MagicMock()
            mock_storage_service.return_value = mock_storage
            mock_storage.file_exists.return_value = True
            mock_storage.download_file.return_value = True
            mock_storage.upload_analysis_result.return_value = (
                "processed/2/2025/08/13/long_features.json"
            )

            mock_type_obj = MagicMock()
            mock_type_obj.value = "local"
            mock_storage_type.return_value = mock_type_obj

            mock_feature_extractor = MagicMock()
            mock_extractor.return_value = mock_feature_extractor
            mock_feature_extractor.extract_features.return_value = mock_feature_result

            mock_temp = MagicMock()
            mock_temp.name = "/tmp/long_audio.mp3"
            mock_tempfile.return_value.__enter__.return_value = mock_temp

            # Execute
            result = process_audio_features_from_storage(
                "test-task-id-2",
                "uploads/2/2025/08/13/long_audio.mp3",
                False,
                None,
                {"user_id": "2", "upload_id": "456"},
            )

            # Verify analysis summary uses aggregated features
            analysis = result["analysis_summary"]
            assert analysis is not None
            assert analysis["bpm"] == 115.2  # from mean_bpm
            assert analysis["key"] == "A minor"  # from most_likely_key
            assert analysis["key_confidence"] == 0.75
            assert analysis["loudness_db"] == -15.8  # from mean_loudness_db
            assert analysis["brightness"] == 1500.5  # from mean_brightness
            assert analysis["duration"] == 180.0

            # Verify storage path includes user_id
            assert (
                result["storage_analysis_path"]
                == "processed/2/2025/08/13/long_features.json"
            )

    def test_analysis_summary_missing_features(self):
        """Test analysis summary when some features are missing"""
        # Mock feature result with missing features
        mock_feature_result = {
            "metadata": {"duration": 45.0},
            "features": {
                "tempo": {"bpm": 90.0},
                "key": {"key": "F major", "confidence": 0.6},
                # Missing energy and spectral features
            },
        }

        with patch(
            "tasks.storage_processing.get_storage_service"
        ) as mock_storage_service, patch(
            "tasks.storage_processing.get_storage_type"
        ) as mock_storage_type, patch(
            "tasks.storage_processing.current_task"
        ) as mock_current_task, patch(
            "tasks.storage_processing.create_feature_extractor"
        ) as mock_extractor, patch(
            "tasks.storage_processing.tempfile.NamedTemporaryFile"
        ) as mock_tempfile, patch(
            "tasks.storage_processing.os.unlink"
        ):

            # Setup mocks
            mock_storage = MagicMock()
            mock_storage_service.return_value = mock_storage
            mock_storage.file_exists.return_value = True
            mock_storage.download_file.return_value = True
            mock_storage.upload_analysis_result.return_value = (
                "processed/3/2025/08/13/partial_features.json"
            )

            mock_type_obj = MagicMock()
            mock_type_obj.value = "local"
            mock_storage_type.return_value = mock_type_obj

            mock_feature_extractor = MagicMock()
            mock_extractor.return_value = mock_feature_extractor
            mock_feature_extractor.extract_features.return_value = mock_feature_result

            mock_temp = MagicMock()
            mock_temp.name = "/tmp/partial.mp3"
            mock_tempfile.return_value.__enter__.return_value = mock_temp

            # Execute
            result = process_audio_features_from_storage(
                "test-task-id-3",
                "uploads/3/2025/08/13/partial.mp3",
                False,
                None,
                {"user_id": "3", "upload_id": "789"},
            )

            # Verify analysis summary handles missing features gracefully
            analysis = result["analysis_summary"]
            assert analysis is not None
            assert analysis["bpm"] == 90.0
            assert analysis["key"] == "F major"
            assert analysis["key_confidence"] == 0.6
            assert analysis["loudness_db"] == 0.0  # Default for missing feature
            assert analysis["brightness"] == 0.0  # Default for missing feature
            assert analysis["duration"] == 45.0

    def test_analysis_summary_no_features(self):
        """Test analysis summary when no features are available"""
        # Mock feature result with no features
        mock_feature_result = {
            "metadata": {"duration": 10.0},
            "error": "Feature extraction failed",
        }

        with patch(
            "tasks.storage_processing.get_storage_service"
        ) as mock_storage_service, patch(
            "tasks.storage_processing.get_storage_type"
        ) as mock_storage_type, patch(
            "tasks.storage_processing.current_task"
        ) as mock_current_task, patch(
            "tasks.storage_processing.create_feature_extractor"
        ) as mock_extractor, patch(
            "tasks.storage_processing.tempfile.NamedTemporaryFile"
        ) as mock_tempfile, patch(
            "tasks.storage_processing.os.unlink"
        ):

            # Setup mocks
            mock_storage = MagicMock()
            mock_storage_service.return_value = mock_storage
            mock_storage.file_exists.return_value = True
            mock_storage.download_file.return_value = True
            mock_storage.upload_analysis_result.return_value = (
                "processed/4/2025/08/13/error_features.json"
            )

            mock_type_obj = MagicMock()
            mock_type_obj.value = "local"
            mock_storage_type.return_value = mock_type_obj

            mock_feature_extractor = MagicMock()
            mock_extractor.return_value = mock_feature_extractor
            mock_feature_extractor.extract_features.return_value = mock_feature_result

            mock_temp = MagicMock()
            mock_temp.name = "/tmp/error.mp3"
            mock_tempfile.return_value.__enter__.return_value = mock_temp

            # Execute - should raise an exception due to error in feature_result
            with pytest.raises(Exception, match="Feature extraction failed"):
                process_audio_features_from_storage(
                    "test-task-id-4",
                    "uploads/4/2025/08/13/error.mp3",
                    False,
                    None,
                    {"user_id": "4", "upload_id": "999"},
                )

    def test_user_id_in_storage_path(self):
        """Test that user_id is properly included in storage paths"""
        mock_feature_result = {
            "metadata": {"duration": 60.0},
            "features": {
                "tempo": {"bpm": 128.0},
                "key": {"key": "D major", "confidence": 0.9},
            },
        }

        with patch(
            "tasks.storage_processing.get_storage_service"
        ) as mock_storage_service, patch(
            "tasks.storage_processing.get_storage_type"
        ) as mock_storage_type, patch(
            "tasks.storage_processing.current_task"
        ) as mock_current_task, patch(
            "tasks.storage_processing.create_feature_extractor"
        ) as mock_extractor, patch(
            "tasks.storage_processing.tempfile.NamedTemporaryFile"
        ) as mock_tempfile, patch(
            "tasks.storage_processing.os.unlink"
        ):

            # Setup mocks
            mock_storage = MagicMock()
            mock_storage_service.return_value = mock_storage
            mock_storage.file_exists.return_value = True
            mock_storage.download_file.return_value = True

            mock_type_obj = MagicMock()
            mock_type_obj.value = "local"
            mock_storage_type.return_value = mock_type_obj

            mock_feature_extractor = MagicMock()
            mock_extractor.return_value = mock_feature_extractor
            mock_feature_extractor.extract_features.return_value = mock_feature_result

            mock_temp = MagicMock()
            mock_temp.name = "/tmp/user_test.mp3"
            mock_tempfile.return_value.__enter__.return_value = mock_temp

            # Test with different user IDs
            test_cases = [
                {
                    "user_id": "1",
                    "expected_path": "processed/1/2025/08/13/test_features.json",
                },
                {
                    "user_id": "42",
                    "expected_path": "processed/42/2025/08/13/test_features.json",
                },
                {
                    "user_id": "999",
                    "expected_path": "processed/999/2025/08/13/test_features.json",
                },
            ]

            for case in test_cases:
                # Configure mock to return expected path
                mock_storage.upload_analysis_result.return_value = case["expected_path"]

                result = process_audio_features_from_storage(
                    f"test-task-{case['user_id']}",
                    f"uploads/{case['user_id']}/2025/08/13/test.mp3",
                    False,
                    None,
                    {"user_id": case["user_id"], "upload_id": "123"},
                )

                # Verify user_id is passed to upload_analysis_result
                mock_storage.upload_analysis_result.assert_called()
                call_args = mock_storage.upload_analysis_result.call_args
                assert (
                    call_args[0][3] == case["user_id"]
                )  # 4th argument should be user_id

                # Verify storage path
                assert result["storage_analysis_path"] == case["expected_path"]

    def test_analysis_summary_without_user_id(self):
        """Test analysis summary when user_id is missing from metadata"""
        mock_feature_result = {
            "metadata": {"duration": 30.0},
            "features": {
                "tempo": {"bpm": 100.0},
                "key": {"key": "G major", "confidence": 0.7},
            },
        }

        with patch(
            "tasks.storage_processing.get_storage_service"
        ) as mock_storage_service, patch(
            "tasks.storage_processing.get_storage_type"
        ) as mock_storage_type, patch(
            "tasks.storage_processing.current_task"
        ) as mock_current_task, patch(
            "tasks.storage_processing.create_feature_extractor"
        ) as mock_extractor, patch(
            "tasks.storage_processing.tempfile.NamedTemporaryFile"
        ) as mock_tempfile, patch(
            "tasks.storage_processing.os.unlink"
        ):

            # Setup mocks
            mock_storage = MagicMock()
            mock_storage_service.return_value = mock_storage
            mock_storage.file_exists.return_value = True
            mock_storage.download_file.return_value = True
            mock_storage.upload_analysis_result.return_value = (
                "processed/2025/08/13/no_user_features.json"
            )

            mock_type_obj = MagicMock()
            mock_type_obj.value = "local"
            mock_storage_type.return_value = mock_type_obj

            mock_feature_extractor = MagicMock()
            mock_extractor.return_value = mock_feature_extractor
            mock_feature_extractor.extract_features.return_value = mock_feature_result

            mock_temp = MagicMock()
            mock_temp.name = "/tmp/no_user.mp3"
            mock_tempfile.return_value.__enter__.return_value = mock_temp

            # Execute without user_id in metadata
            result = process_audio_features_from_storage(
                "test-task-no-user",
                "uploads/2025/08/13/no_user.mp3",
                False,
                None,
                {"upload_id": "123"},  # No user_id
            )

            # Verify user_id=None is passed to upload_analysis_result
            mock_storage.upload_analysis_result.assert_called()
            call_args = mock_storage.upload_analysis_result.call_args
            assert call_args[0][3] is None  # 4th argument should be None

            # Verify storage path doesn't include user_id
            assert (
                result["storage_analysis_path"]
                == "processed/2025/08/13/no_user_features.json"
            )

            # Verify analysis summary still works
            analysis = result["analysis_summary"]
            assert analysis is not None
            assert analysis["bpm"] == 100.0
            assert analysis["key"] == "G major"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
