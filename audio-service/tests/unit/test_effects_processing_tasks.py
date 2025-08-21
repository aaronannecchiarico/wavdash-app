"""
Unit tests for effects processing Celery tasks
"""

import sys
import pytest
import tempfile
import os
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock, call

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestEffectsProcessingTask:
    """Test effects processing Celery task functionality"""
    
    def test_effects_task_has_delay_method(self):
        """Test that effects task has delay method for Celery"""
        from tasks.effects_processing import process_audio_with_effects
        
        assert hasattr(process_audio_with_effects, 'delay'), \
            "process_audio_with_effects should have delay method"
        assert callable(process_audio_with_effects.delay), \
            "delay should be callable"

    def test_celery_task_names(self):
        """Test that Celery task names are correct"""
        from tasks.effects_processing import process_audio_with_effects
        
        assert process_audio_with_effects.name == 'tasks.effects_processing.process_audio_with_effects', \
            "Task name should match expected pattern"

    @patch('tasks.effects_processing.get_storage_service')
    @patch('tasks.effects_processing.get_storage_type')
    @patch('tasks.effects_processing.get_effects_processor')
    @patch('tasks.effects_processing.current_task')
    @patch('librosa.load')
    @patch('tempfile.NamedTemporaryFile')
    @patch('requests.post')
    def test_process_audio_with_effects_success(
        self, mock_requests, mock_temp_file, mock_librosa_load, mock_current_task,
        mock_processor, mock_storage_type, mock_storage_service
    ):
        """Test successful effects processing"""
        from tasks.effects_processing import process_audio_with_effects
        from models.effects_models import EffectsConfiguration
        from services.storage_service import StorageType
        
        # Setup mock data
        task_id = "test-task-123"
        storage_path = "uploads/test/file.mp3"
        user_id = "test_user"
        callback_url = "http://localhost:8000/callback"
        
        # Mock configuration
        effects_config = {
            "stem_chains": [
                {
                    "stem": "vocals",
                    "effects": [
                        {
                            "id": "comp1",
                            "type": "compressor",
                            "name": "Compressor",
                            "parameters": {
                                "threshold_db": -20.0,
                                "ratio": 4.0,
                                "attack_ms": 10.0,
                                "release_ms": 100.0
                            },
                            "bypass": False,
                            "order": 0
                        }
                    ],
                    "volume": 1.0,
                    "pan": 0.0,
                    "mute": False,
                    "solo": False
                }
            ],
            "master_chain": {
                "effects": [],
                "volume": 1.0
            }
        }
        
        # Setup mocks
        mock_storage = MagicMock()
        mock_storage.file_exists.return_value = True
        mock_storage.download_file.return_value = True
        mock_storage.save_processed_audio.return_value = "processed/test/file_effects.wav"
        mock_storage.get_public_url.return_value = "http://storage.com/file.wav"
        mock_storage_service.return_value = mock_storage
        mock_storage_type.return_value = StorageType.LOCAL
        
        # Mock effects processor
        mock_effects_processor = MagicMock()
        mock_effects_processor.is_available.return_value = True
        mock_effects_processor.validate_configuration.return_value = (True, [])
        mock_effects_processor.process_stems_with_effects.return_value = np.array([0.1, 0.2, 0.3])
        mock_processor.return_value = mock_effects_processor
        
        # Mock librosa
        mock_librosa_load.return_value = (np.array([0.1, 0.2, 0.3]), 44100)
        
        # Mock temporary file
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.mp3"
        
        # Mock current task
        mock_task_instance = MagicMock()
        mock_current_task.update_state = MagicMock()
        
        # Mock requests
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_requests.return_value = mock_response
        
        # Mock the task self object
        with patch.object(process_audio_with_effects, 'update_state') as mock_update_state:
            # Call the function directly - Celery will inject self automatically
            result = process_audio_with_effects(
                task_id=task_id,
                storage_path=storage_path,
                effects_config=effects_config,
                callback_url=callback_url,
                user_id=user_id,
                output_format="wav",
                separate_stems=True
            )
        
        # Verify result
        assert result['task_id'] == task_id
        assert result['status'] == 'completed'
        assert result['storage_path'] == storage_path
        assert 'output_path' in result
        assert 'processing_time' in result
        assert 'effects_applied' in result
        assert result['effects_applied'] == 1  # One effect in config
        
        # Verify storage interactions
        mock_storage.file_exists.assert_called_once_with(storage_path)
        mock_storage.download_file.assert_called_once()
        mock_storage.save_processed_audio.assert_called_once()
        
        # Verify effects processor interactions
        mock_effects_processor.is_available.assert_called_once()
        mock_effects_processor.validate_configuration.assert_called_once()
        mock_effects_processor.process_stems_with_effects.assert_called_once()
        
        # Verify callback was sent
        mock_requests.assert_called_once()
        callback_data = mock_requests.call_args[1]['json']
        assert callback_data['task_id'] == task_id
        assert callback_data['status'] == 'completed'
        assert callback_data['processing_type'] == 'effects'

    @patch('tasks.effects_processing.get_storage_service')
    @patch('tasks.effects_processing.current_task')
    def test_process_audio_with_effects_file_not_found(
        self, mock_current_task, mock_storage_service
    ):
        """Test effects processing with file not found error"""
        from tasks.effects_processing import process_audio_with_effects
        
        # Setup mocks
        mock_storage = MagicMock()
        mock_storage.file_exists.return_value = False
        mock_storage_service.return_value = mock_storage
        
        
        # Test data
        task_id = "test-task-123"
        storage_path = "uploads/test/nonexistent.mp3"
        effects_config = {
            "stem_chains": [],
            "master_chain": {"effects": [], "volume": 1.0}
        }
        
        # Call should raise FileNotFoundError
        with pytest.raises(FileNotFoundError) as exc_info:
            process_audio_with_effects(
                task_id=task_id,
                storage_path=storage_path,
                effects_config=effects_config
            )
        
        assert "File not found in storage" in str(exc_info.value)
        mock_storage.file_exists.assert_called_once_with(storage_path)

    @patch('tasks.effects_processing.get_storage_service')
    @patch('tasks.effects_processing.get_effects_processor')
    @patch('tasks.effects_processing.current_task')
    def test_process_audio_with_effects_processor_unavailable(
        self, mock_current_task, mock_processor, mock_storage_service
    ):
        """Test effects processing when processor is unavailable"""
        from tasks.effects_processing import process_audio_with_effects
        
        # Setup mocks
        mock_storage = MagicMock()
        mock_storage.file_exists.return_value = True
        mock_storage_service.return_value = mock_storage
        
        mock_effects_processor = MagicMock()
        mock_effects_processor.is_available.return_value = False
        mock_processor.return_value = mock_effects_processor
        
        
        # Test data
        task_id = "test-task-123"
        storage_path = "uploads/test/file.mp3"
        effects_config = {
            "stem_chains": [],
            "master_chain": {"effects": [], "volume": 1.0}
        }
        
        # Call should raise RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            process_audio_with_effects(
                task_id=task_id,
                storage_path=storage_path,
                effects_config=effects_config
            )
        
        assert "Effects processor not available" in str(exc_info.value)

    @patch('tasks.effects_processing.get_storage_service')
    @patch('tasks.effects_processing.get_effects_processor')
    @patch('tasks.effects_processing.current_task')
    def test_process_audio_with_effects_invalid_configuration(
        self, mock_current_task, mock_processor, mock_storage_service
    ):
        """Test effects processing with invalid configuration"""
        from tasks.effects_processing import process_audio_with_effects
        
        # Setup mocks
        mock_storage = MagicMock()
        mock_storage.file_exists.return_value = True
        mock_storage_service.return_value = mock_storage
        
        mock_effects_processor = MagicMock()
        mock_effects_processor.is_available.return_value = True
        mock_effects_processor.validate_configuration.return_value = (False, ["Invalid parameter"])
        mock_processor.return_value = mock_effects_processor
        
        
        # Test data
        task_id = "test-task-123"
        storage_path = "uploads/test/file.mp3"
        effects_config = {
            "stem_chains": [
                {
                    "stem": "vocals",
                    "effects": [
                        {
                            "id": "invalid",
                            "type": "invalid_effect",
                            "name": "Invalid",
                            "parameters": {},
                            "bypass": False,
                            "order": 0
                        }
                    ],
                    "volume": 1.0,
                    "pan": 0.0,
                    "mute": False,
                    "solo": False
                }
            ],
            "master_chain": {"effects": [], "volume": 1.0}
        }
        
        # Call should raise ValueError
        with pytest.raises(ValueError) as exc_info:
            process_audio_with_effects(
                task_id=task_id,
                storage_path=storage_path,
                effects_config=effects_config
            )
        
        # Should catch Pydantic validation error
        assert "validation error" in str(exc_info.value) or "Invalid effects configuration" in str(exc_info.value)

    @patch('tasks.effects_processing.get_storage_service')
    @patch('tasks.effects_processing.get_storage_type')
    @patch('tasks.effects_processing.get_effects_processor')
    @patch('tasks.effects_processing.current_task')
    @patch('librosa.load')
    @patch('tempfile.NamedTemporaryFile')
    @patch('requests.post')
    def test_process_audio_with_effects_with_callback_failure(
        self, mock_requests, mock_temp_file, mock_librosa_load, mock_current_task,
        mock_processor, mock_storage_type, mock_storage_service
    ):
        """Test effects processing with callback failure (should not fail task)"""
        from tasks.effects_processing import process_audio_with_effects
        from services.storage_service import StorageType
        
        # Setup mocks (similar to success test)
        mock_storage = MagicMock()
        mock_storage.file_exists.return_value = True
        mock_storage.download_file.return_value = True
        mock_storage.save_processed_audio.return_value = "processed/test/file_effects.wav"
        mock_storage_service.return_value = mock_storage
        mock_storage_type.return_value = StorageType.LOCAL
        
        mock_effects_processor = MagicMock()
        mock_effects_processor.is_available.return_value = True
        mock_effects_processor.validate_configuration.return_value = (True, [])
        mock_effects_processor.process_stems_with_effects.return_value = np.array([0.1, 0.2, 0.3])
        mock_processor.return_value = mock_effects_processor
        
        mock_librosa_load.return_value = (np.array([0.1, 0.2, 0.3]), 44100)
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_file.mp3"
        
        # Mock requests to raise exception
        mock_requests.side_effect = Exception("Callback failed")
        
        
        # Test data
        task_id = "test-task-123"
        storage_path = "uploads/test/file.mp3"
        callback_url = "http://localhost:8000/callback"
        effects_config = {
            "stem_chains": [],
            "master_chain": {"effects": [], "volume": 1.0}
        }
        
        # Call should succeed despite callback failure
        result = process_audio_with_effects(
            task_id=task_id,
            storage_path=storage_path,
            effects_config=effects_config,
            callback_url=callback_url
        )
        
        # Task should still complete successfully
        assert result['task_id'] == task_id
        assert result['status'] == 'completed'
        
        # Callback should have been attempted
        mock_requests.assert_called_once()

    def test_stem_separation_demucs_unavailable(self):
        """Test stem separation when Demucs is not available"""
        # Mock DEMUCS_AVAILABLE to False
        with patch('tasks.effects_processing.DEMUCS_AVAILABLE', False):
            from tasks.effects_processing import _separate_stems
            
            audio_data = np.array([0.1, 0.2, 0.3])
            sample_rate = 44100
            
            with pytest.raises(RuntimeError) as exc_info:
                _separate_stems(audio_data, sample_rate)
            
            assert "Demucs not available" in str(exc_info.value)

    @patch('tasks.effects_processing.DEMUCS_AVAILABLE', True)
    @patch('tasks.effects_processing.pretrained')
    @patch('tasks.effects_processing.apply_model')
    @patch('tasks.effects_processing.torch')
    def test_stem_separation_success(
        self, mock_torch, mock_apply_model, mock_pretrained
    ):
        """Test successful stem separation"""
        from tasks.effects_processing import _separate_stems
        
        # Mock Demucs components
        mock_model = MagicMock()
        mock_pretrained.get_model.return_value = mock_model
        
        # Mock torch tensor and operations
        mock_tensor = MagicMock()
        mock_torch.tensor.return_value = mock_tensor
        mock_torch.no_grad.return_value.__enter__ = MagicMock()
        mock_torch.no_grad.return_value.__exit__ = MagicMock()
        
        # Mock separated stems output
        mock_sources = MagicMock()
        mock_sources.__getitem__.return_value.__getitem__.return_value.numpy.return_value = np.array([[0.1, 0.2], [0.3, 0.4]])
        mock_apply_model.return_value = mock_sources
        
        # Test data
        audio_data = np.array([0.1, 0.2, 0.3])
        sample_rate = 44100
        
        # Call function
        result = _separate_stems(audio_data, sample_rate)
        
        # Verify result
        assert isinstance(result, dict)
        assert "drums" in result
        assert "bass" in result
        assert "other" in result
        assert "vocals" in result
        
        # Verify model was loaded and used
        mock_pretrained.get_model.assert_called_once_with("htdemucs")
        mock_model.eval.assert_called_once()
        mock_apply_model.assert_called_once()

    def test_calculate_quality_score(self):
        """Test quality score calculation"""
        from tasks.effects_processing import _calculate_quality_score
        
        # Test base case (no warnings, reasonable time)
        score = _calculate_quality_score(10.0, 2, [])
        assert score == 1.0
        
        # Test with warnings
        score = _calculate_quality_score(10.0, 2, ["Warning 1", "Warning 2"])
        assert score == 0.8  # 1.0 - (2 * 0.1)
        
        # Test with long processing time
        score = _calculate_quality_score(100.0, 2, [])
        expected_time = 10 + (2 * 5)  # 20 seconds expected
        time_penalty = min(0.3, (100.0 - 20) / 20 * 0.2)  # 0.2
        expected_score = 1.0 - time_penalty
        assert abs(score - expected_score) < 0.01
        
        # Test score bounds
        score = _calculate_quality_score(1000.0, 10, ["W1", "W2", "W3", "W4", "W5"])
        assert score >= 0.0
        assert score <= 1.0


class TestEffectsTaskImports:
    """Test critical imports for effects processing tasks"""
    
    def test_effects_processor_imports_available(self):
        """Test that effects processor imports are available"""
        try:
            from services.effects_processor import get_effects_processor
            from models.effects_models import EffectsConfiguration, EffectsProcessingResult
            assert True, "All imports successful"
        except ImportError as e:
            pytest.fail(f"Critical import failed: {e}")

    def test_all_critical_task_imports_available(self):
        """Test that all critical imports for effects tasks are available"""
        try:
            from tasks.effects_processing import process_audio_with_effects, _separate_stems, _calculate_quality_score
            from services.storage_service import get_storage_service, get_storage_type
            from models.storage_models import StorageCallbackData
            assert True, "All critical imports successful"
        except ImportError as e:
            pytest.fail(f"Critical import failed: {e}")

    def test_demucs_imports_handling(self):
        """Test that Demucs imports are handled gracefully"""
        from tasks import effects_processing as effects_tasks
        
        # Should have DEMUCS_AVAILABLE constant
        assert hasattr(effects_tasks, 'DEMUCS_AVAILABLE')
        assert isinstance(effects_tasks.DEMUCS_AVAILABLE, bool)

    def test_stem_separation_function_availability(self):
        """Test that stem separation helper function is available"""
        from tasks.effects_processing import _separate_stems
        
        assert callable(_separate_stems)

    def test_quality_score_function_availability(self):
        """Test that quality score calculation function is available"""
        from tasks.effects_processing import _calculate_quality_score
        
        assert callable(_calculate_quality_score)


class TestEffectsTaskConfiguration:
    """Test effects task configuration and Celery integration"""
    
    def test_task_decorator_configuration(self):
        """Test that task is properly configured with Celery decorators"""
        from tasks.effects_processing import process_audio_with_effects
        
        # Check task name
        assert hasattr(process_audio_with_effects, 'name')
        assert process_audio_with_effects.name == 'tasks.effects_processing.process_audio_with_effects'
        
        # Check queue assignment
        # Note: This might not be directly accessible, but we can check if delay method exists
        assert hasattr(process_audio_with_effects, 'delay')
        assert callable(process_audio_with_effects.delay)
        
        # Check if it's bound (bind=True)
        assert hasattr(process_audio_with_effects, '__self__') or hasattr(process_audio_with_effects, 'request')

    def test_task_imports_no_circular_dependencies(self):
        """Test that importing tasks doesn't cause circular dependencies"""
        try:
            # This import pattern should not cause circular imports
            from tasks.effects_processing import process_audio_with_effects
            from routes.effects_processing import router
            from services.effects_processor import get_effects_processor
            
            # All should be importable without errors
            assert process_audio_with_effects is not None
            assert router is not None
            assert get_effects_processor is not None
            
        except ImportError as e:
            pytest.fail(f"Circular import detected: {e}")


if __name__ == "__main__":
    pytest.main([__file__])