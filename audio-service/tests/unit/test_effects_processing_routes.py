"""
Unit tests for effects processing routes
"""

import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestEffectsProcessingRoutes:
    """Test effects processing route functionality"""
    
    def test_celery_task_import_conflict_prevention(self):
        """
        Ensure that Celery tasks are properly imported and don't conflict with route function names.
        This test prevents the 'function' object has no attribute 'delay' error.
        """
        # Import the route module to check for naming conflicts
        from routes import effects_processing as effects_routes
        from tasks import effects_processing as effects_tasks
        
        # Verify that the Celery task has the delay method
        assert hasattr(effects_tasks.process_audio_with_effects, 'delay'), \
            "Celery task process_audio_with_effects should have 'delay' method"
        
        # Verify that the imported task in routes has the delay method
        assert hasattr(effects_routes.process_audio_with_effects, 'delay'), \
            "Imported process_audio_with_effects in routes should have 'delay' method"
        
        # Verify that route function doesn't shadow the Celery task
        route_func = getattr(effects_routes, 'process_audio_with_effects_route', None)
        assert route_func is not None, "Route function should be named process_audio_with_effects_route"
        
        # Ensure the route function doesn't have delay method (it's not a Celery task)
        assert not hasattr(route_func, 'delay'), \
            "Route function should not have 'delay' method"

    @patch('routes.effects_processing.is_storage_enabled')
    @patch('routes.effects_processing.get_storage_service')
    @patch('routes.effects_processing.get_effects_processor')
    @patch('routes.effects_processing.process_audio_with_effects')
    def test_process_audio_with_effects_calls_correct_task(
        self, mock_task, mock_processor, mock_storage_service, mock_storage_enabled
    ):
        """
        Test that the effects processing route calls the correct Celery task
        """
        # Setup mocks
        mock_storage_enabled.return_value = True
        mock_storage = MagicMock()
        mock_storage.file_exists.return_value = True
        mock_storage_service.return_value = mock_storage
        
        # Mock effects processor
        mock_effects_processor = MagicMock()
        mock_effects_processor.is_available.return_value = True
        mock_effects_processor.validate_configuration.return_value = (True, [])
        mock_processor.return_value = mock_effects_processor
        
        # Mock the Celery task
        mock_celery_task = MagicMock()
        mock_celery_task.delay.return_value = MagicMock(id="test-task-id")
        mock_task.delay = mock_celery_task.delay
        
        # Test data with valid effects configuration
        request_data = {
            "storage_path": "uploads/test/file.mp3",
            "effects_config": {
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
                                    "release_ms": 100.0,
                                    "knee_db": 2.0,
                                    "makeup_gain_db": 0.0
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
            },
            "callback_url": "http://localhost:8000/callback",
            "user_id": "test_user",
            "output_format": "wav",
            "separate_stems": True
        }
        
        # Make request
        response = client.post("/effects/process", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "processing"
        assert "Effects processing started" in response_data["message"]
        assert "task_id" in response_data
        
        # Verify that the Celery task was called with delay
        mock_task.delay.assert_called_once()
        call_args = mock_task.delay.call_args
        assert "task_id" in call_args.kwargs
        assert call_args.kwargs["storage_path"] == "uploads/test/file.mp3"
        assert call_args.kwargs["user_id"] == "test_user"
        assert call_args.kwargs["output_format"] == "wav"

    @patch('routes.effects_processing.is_storage_enabled')
    def test_storage_disabled_error(self, mock_storage_enabled):
        """
        Test that proper error is returned when storage is not enabled
        """
        mock_storage_enabled.return_value = False
        
        request_data = {
            "storage_path": "uploads/test/file.mp3",
            "effects_config": {
                "stem_chains": [
                    {
                        "stem": "vocals",
                        "effects": [],
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
        }
        
        response = client.post("/effects/process", json=request_data)
        
        assert response.status_code == 503
        assert "Storage is not properly configured" in response.json()["detail"]

    @patch('routes.effects_processing.is_storage_enabled')
    @patch('routes.effects_processing.get_storage_service')
    def test_file_not_found_error(self, mock_storage_service, mock_storage_enabled):
        """
        Test that proper error is returned when file doesn't exist in storage
        """
        mock_storage_enabled.return_value = True
        mock_storage = MagicMock()
        mock_storage.file_exists.return_value = False
        mock_storage_service.return_value = mock_storage
        
        request_data = {
            "storage_path": "uploads/test/nonexistent.mp3",
            "effects_config": {
                "stem_chains": [
                    {
                        "stem": "vocals",
                        "effects": [],
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
        }
        
        response = client.post("/effects/process", json=request_data)
        
        assert response.status_code == 404
        assert "File not found in storage" in response.json()["detail"]

    @patch('routes.effects_processing.get_effects_processor')
    def test_effects_processor_unavailable_error(self, mock_processor):
        """
        Test that proper error is returned when effects processor is not available
        """
        mock_effects_processor = MagicMock()
        mock_effects_processor.is_available.return_value = False
        mock_processor.return_value = mock_effects_processor
        
        request_data = {
            "storage_path": "uploads/test/file.mp3",
            "effects_config": {
                "stem_chains": [
                    {
                        "stem": "vocals",
                        "effects": [],
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
        }
        
        with patch('routes.effects_processing.is_storage_enabled', return_value=True), \
             patch('routes.effects_processing.get_storage_service') as mock_storage_service:
            
            mock_storage = MagicMock()
            mock_storage.file_exists.return_value = True
            mock_storage_service.return_value = mock_storage
            
            response = client.post("/effects/process", json=request_data)
        
        assert response.status_code == 503
        assert "Effects processing is not available" in response.json()["detail"]

    def test_missing_required_fields(self):
        """
        Test validation errors for missing required fields
        """
        # Test missing storage_path
        request_data = {
            "effects_config": {
                "stem_chains": [],
                "master_chain": {"effects": [], "volume": 1.0}
            }
        }
        response = client.post("/effects/process", json=request_data)
        assert response.status_code == 422

        # Test missing effects_config
        request_data = {"storage_path": "uploads/test/file.mp3"}
        response = client.post("/effects/process", json=request_data)
        assert response.status_code == 422

    @patch('routes.effects_processing.get_effects_processor')
    def test_get_effects_catalog_success(self, mock_processor):
        """
        Test successful retrieval of effects catalog
        """
        mock_effects_processor = MagicMock()
        mock_effects_processor.is_available.return_value = True
        mock_effects_processor.get_supported_effects.return_value = [
            {
                "type": "compressor",
                "name": "Compressor",
                "category": "dynamics",
                "description": "Dynamic range compression",
                "parameters": {
                    "threshold_db": {"min": -60, "max": 0, "default": -20, "unit": "dB"}
                }
            }
        ]
        mock_processor.return_value = mock_effects_processor
        
        response = client.get("/effects/catalog")
        
        assert response.status_code == 200
        data = response.json()
        assert data["available"] == True
        assert data["total_effects"] == 1
        assert len(data["effects"]) == 1
        assert data["effects"][0]["type"] == "compressor"

    @patch('routes.effects_processing.get_effects_processor')
    def test_get_effects_catalog_unavailable(self, mock_processor):
        """
        Test effects catalog when processor is unavailable
        """
        mock_effects_processor = MagicMock()
        mock_effects_processor.is_available.return_value = False
        mock_processor.return_value = mock_effects_processor
        
        response = client.get("/effects/catalog")
        
        assert response.status_code == 200
        data = response.json()
        assert data["available"] == False
        assert data["effects"] == []
        assert "not available" in data["message"]

    def test_get_effects_presets_success(self):
        """
        Test successful retrieval of effects presets
        """
        response = client.get("/effects/presets")
        
        assert response.status_code == 200
        data = response.json()
        assert "presets" in data
        assert "total_presets" in data
        assert len(data["presets"]) > 0
        
        # Check that presets have required fields
        preset = data["presets"][0]
        assert "name" in preset
        assert "description" in preset
        assert "category" in preset
        assert "config" in preset

    @patch('routes.effects_processing.get_effects_processor')
    @patch('routes.effects_processing.is_storage_enabled')
    def test_get_effects_status_available(self, mock_storage_enabled, mock_processor):
        """
        Test effects status when processor is available
        """
        mock_storage_enabled.return_value = True
        mock_effects_processor = MagicMock()
        mock_effects_processor.is_available.return_value = True
        mock_effects_processor.get_supported_effects.return_value = [
            {"category": "dynamics"},
            {"category": "time_based"}
        ]
        mock_processor.return_value = mock_effects_processor
        
        response = client.get("/effects/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["available"] == True
        assert data["storage_enabled"] == True
        assert data["supported_effects"] == 2
        assert "ready" in data["message"]

    @patch('routes.effects_processing.get_effects_processor')
    @patch('routes.effects_processing.is_storage_enabled')
    def test_get_effects_status_unavailable(self, mock_storage_enabled, mock_processor):
        """
        Test effects status when processor is not available
        """
        mock_storage_enabled.return_value = False
        mock_effects_processor = MagicMock()
        mock_effects_processor.is_available.return_value = False
        mock_processor.return_value = mock_effects_processor
        
        response = client.get("/effects/status")
        
        assert response.status_code == 200
        data = response.json()
        assert data["available"] == False
        assert data["storage_enabled"] == False
        assert data["supported_effects"] == 0
        assert "not available" in data["message"]

    def test_route_function_naming_convention(self):
        """
        Test that route functions follow naming convention to prevent conflicts
        """
        from routes import effects_processing as effects_routes
        
        # Check that the route function is properly named to avoid conflicts
        assert hasattr(effects_routes, 'process_audio_with_effects_route'), \
            "Route function should be named with '_route' suffix to avoid conflicts"
        
        # Ensure the imported Celery task is available
        assert hasattr(effects_routes, 'process_audio_with_effects'), \
            "Celery task should be imported and available"
        
        # Ensure they are different objects
        route_func = effects_routes.process_audio_with_effects_route
        celery_task = effects_routes.process_audio_with_effects
        assert route_func != celery_task, \
            "Route function and Celery task should be different objects"


class TestEffectsTaskAvailability:
    """Test that effects tasks are properly configured"""
    
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


class TestEffectsTaskImports:
    """Test critical imports for effects processing"""
    
    def test_effects_processor_imports_available(self):
        """Test that effects processor imports are available"""
        try:
            from services.effects_processor import get_effects_processor, EffectsProcessor
            from models.effects_models import EffectsConfiguration, EffectsProcessingResult
            assert True, "All imports successful"
        except ImportError as e:
            pytest.fail(f"Critical import failed: {e}")

    def test_all_critical_imports_available(self):
        """Test that all critical imports for effects processing are available"""
        try:
            from tasks.effects_processing import process_audio_with_effects
            from routes.effects_processing import router
            from services.effects_processor import get_effects_processor
            from models.effects_models import EffectsConfiguration
            assert True, "All critical imports successful"
        except ImportError as e:
            pytest.fail(f"Critical import failed: {e}")

    def test_function_imports_not_causing_import_errors(self):
        """Test that importing functions doesn't cause circular imports or other issues"""
        try:
            # These imports should not raise any exceptions
            from routes.effects_processing import (
                process_audio_with_effects_route,
                get_effects_catalog,
                get_effects_presets,
                get_effects_status
            )
            from tasks.effects_processing import process_audio_with_effects
            
            # Check that functions are callable
            assert callable(process_audio_with_effects_route)
            assert callable(get_effects_catalog)
            assert callable(get_effects_presets)
            assert callable(get_effects_status)
            assert callable(process_audio_with_effects)
            
        except Exception as e:
            pytest.fail(f"Function import or validation failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__])