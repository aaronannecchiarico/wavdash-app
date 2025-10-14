"""
Tests for tempo processing routes to prevent naming conflicts and ensure proper Celery task integration
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


class TestTempoProcessingRoutes:
    """Test tempo processing route functionality and prevent regressions"""
    
    def test_celery_task_import_conflict_prevention(self):
        """
        Ensure that Celery tasks are properly imported and don't conflict with route function names.
        This test prevents the 'function' object has no attribute 'delay' error.
        """
        # Import the route module to check for naming conflicts
        from routes import tempo_processing as tempo_routes
        from tasks import tempo_processing as tempo_tasks
        
        # Verify that the Celery task has the delay method
        assert hasattr(tempo_tasks.process_tempo_from_storage, 'delay'), \
            "Celery task process_tempo_from_storage should have 'delay' method"
        
        # Verify that the imported task in routes has the delay method
        assert hasattr(tempo_routes.process_tempo_from_storage, 'delay'), \
            "Imported process_tempo_from_storage in routes should have 'delay' method"
        
        # Verify that route function doesn't shadow the Celery task
        route_func = getattr(tempo_routes, 'process_tempo_from_storage_route', None)
        assert route_func is not None, "Route function should be named process_tempo_from_storage_route"
        
        # Ensure the route function doesn't have delay method (it's not a Celery task)
        assert not hasattr(route_func, 'delay'), \
            "Route function should not have 'delay' method"

    @patch('utils.route_helpers.is_storage_enabled')
    @patch('utils.route_helpers.get_storage_service')
    @patch('routes.tempo_processing.process_tempo_from_storage')
    def test_storage_tempo_processing_calls_correct_task(self, mock_task, mock_storage_service, mock_storage_enabled):
        """
        Test that the storage tempo processing route calls the correct Celery task
        """
        # Setup mocks
        mock_storage_enabled.return_value = True
        mock_storage = MagicMock()
        mock_storage.file_exists.return_value = True
        mock_storage_service.return_value = mock_storage
        
        # Mock the Celery task
        mock_celery_task = MagicMock()
        mock_celery_task.delay.return_value = MagicMock(id="test-task-id")
        mock_task.delay = mock_celery_task.delay
        
        # Test data
        request_data = {
            "storage_path": "uploads/test/file.mp3",
            "preset": "nightcore",
            "tempo_factor": 1.4,
            "pitch_shift_semitones": 4.0,
            "preserve_pitch": False,
            "add_reverb": False,
            "use_stems": True,
            "callback_url": "http://localhost:8000/callback"
        }
        
        # Make request
        response = client.post("/tempo/storage/process", json=request_data)
        
        # Verify response
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["status"] == "processing"
        assert "Tempo processing started" in response_data["message"]
        
        # Verify that the Celery task was called with delay
        mock_task.delay.assert_called_once()
        call_args = mock_task.delay.call_args
        assert "task_id" in call_args.kwargs
        assert call_args.kwargs["storage_path"] == "uploads/test/file.mp3"

    @patch('utils.route_helpers.is_storage_enabled')
    def test_storage_disabled_error(self, mock_storage_enabled):
        """
        Test that proper error is returned when storage is not enabled
        """
        mock_storage_enabled.return_value = False
        
        request_data = {
            "storage_path": "uploads/test/file.mp3",
            "preset": "nightcore"
        }
        
        response = client.post("/tempo/storage/process", json=request_data)

        assert response.status_code == 503
        assert "Storage is not properly configured" in response.json()["detail"]

    @patch('utils.route_helpers.is_storage_enabled')
    @patch('utils.route_helpers.get_storage_service')
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
            "preset": "nightcore"
        }
        
        response = client.post("/tempo/storage/process", json=request_data)
        
        assert response.status_code == 404
        assert "File not found in storage" in response.json()["detail"]

    def test_route_function_naming_convention(self):
        """
        Test that route functions follow naming convention to prevent conflicts
        """
        from routes import tempo_processing as tempo_routes
        
        # Check that the route function is properly named to avoid conflicts
        assert hasattr(tempo_routes, 'process_tempo_from_storage_route'), \
            "Route function should be named with '_route' suffix to avoid conflicts"
        
        # Ensure the imported Celery task is available
        assert hasattr(tempo_routes, 'process_tempo_from_storage'), \
            "Celery task should be imported and available"
        
        # Ensure they are different objects
        route_func = tempo_routes.process_tempo_from_storage_route
        celery_task = tempo_routes.process_tempo_from_storage
        assert route_func != celery_task, \
            "Route function and Celery task should be different objects"


class TestCeleryTaskAvailability:
    """Test that all required Celery tasks are properly available"""
    
    def test_tempo_tasks_have_delay_method(self):
        """
        Ensure all tempo processing Celery tasks have the delay method
        """
        from tasks.tempo_processing import process_tempo_from_storage

        # Test that tasks have delay method (indicating they're properly decorated)
        assert hasattr(process_tempo_from_storage, 'delay'), \
            "process_tempo_from_storage should have delay method"

        # Test that they're callable
        assert callable(process_tempo_from_storage), \
            "process_tempo_from_storage should be callable"

    def test_celery_task_names(self):
        """
        Test that Celery tasks have proper names for queue routing
        """
        from tasks.tempo_processing import process_tempo_from_storage

        # Check task names
        assert process_tempo_from_storage.name == 'tasks.tempo_processing.process_tempo_from_storage', \
            f"Expected task name 'tasks.tempo_processing.process_tempo_from_storage', got {process_tempo_from_storage.name}"


class TestTempoTaskImports:
    """Test that all required imports are available at module level in tempo processing tasks"""
    
    def test_performance_cache_imports_available(self):
        """
        Ensure that performance cache functions are imported at module level to prevent NameError
        """
        from tasks import tempo_processing as tempo_tasks
        
        # Test that performance cache functions are available at module level
        assert hasattr(tempo_tasks, 'get_performance_cache'), \
            "get_performance_cache should be imported at module level"
        
        assert hasattr(tempo_tasks, 'get_performance_monitor'), \
            "get_performance_monitor should be imported at module level"
        
        assert hasattr(tempo_tasks, 'audio_hash'), \
            "audio_hash should be imported at module level"
        
        # Test that they are callable
        assert callable(tempo_tasks.get_performance_cache), \
            "get_performance_cache should be callable"
        
        assert callable(tempo_tasks.get_performance_monitor), \
            "get_performance_monitor should be callable"
        
        assert callable(tempo_tasks.audio_hash), \
            "audio_hash should be callable"

    def test_all_critical_imports_available(self):
        """
        Test that all critical imports needed by Celery tasks are available at module level
        """
        from tasks import tempo_processing as tempo_tasks
        
        # Core processing imports
        critical_imports = [
            'np', 'librosa', 'sf', 'tempfile', 'logging', 'time', 'requests',
            'get_storage_service', 'get_storage_type', 'StorageType', 'StorageError',
            'create_feature_extractor', 'TempoCallbackData', 'TempoPresetEnum',
            'save_audio_file', 'load_audio_from_bytes',
            'get_performance_cache', 'get_performance_monitor', 'audio_hash'
        ]
        
        missing_imports = []
        for import_name in critical_imports:
            if not hasattr(tempo_tasks, import_name):
                missing_imports.append(import_name)
        
        assert not missing_imports, \
            f"Critical imports missing from tempo_processing module: {missing_imports}"

    def test_tempo_presets_constants_available(self):
        """
        Test that tempo processing constants and presets are properly defined
        """
        from tasks import tempo_processing as tempo_tasks
        
        # Test TEMPO_PRESETS constant
        assert hasattr(tempo_tasks, 'TEMPO_PRESETS'), \
            "TEMPO_PRESETS constant should be defined"
        
        assert isinstance(tempo_tasks.TEMPO_PRESETS, dict), \
            "TEMPO_PRESETS should be a dictionary"
        
        # Test PEDALBOARD_AVAILABLE constant
        assert hasattr(tempo_tasks, 'PEDALBOARD_AVAILABLE'), \
            "PEDALBOARD_AVAILABLE constant should be defined"
        
        assert isinstance(tempo_tasks.PEDALBOARD_AVAILABLE, bool), \
            "PEDALBOARD_AVAILABLE should be a boolean"

    def test_function_imports_not_causing_import_errors(self):
        """
        Test that importing the tempo processing module doesn't cause any import errors
        """
        try:
            # Re-import to catch any import-time errors
            import importlib
            import tasks.tempo_processing
            importlib.reload(tasks.tempo_processing)

            # Test that we can access key functions without errors
            from tasks.tempo_processing import (
                process_tempo_from_storage,
                apply_tempo_processing,
                get_performance_cache,
                get_performance_monitor,
                audio_hash
            )

            # Verify they're all callable
            callables = [
                process_tempo_from_storage, apply_tempo_processing,
                get_performance_cache, get_performance_monitor, audio_hash
            ]

            for func in callables:
                assert callable(func), f"{func.__name__} should be callable"

        except ImportError as e:
            pytest.fail(f"Import error in tempo_processing module: {e}")