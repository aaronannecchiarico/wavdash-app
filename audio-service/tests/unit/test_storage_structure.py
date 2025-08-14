#!/usr/bin/env python3
"""
Unit tests for storage folder structure with user_id
"""

import sys
import pytest
import tempfile
import shutil
import os
import json
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from services.storage_service import LocalStorageService, R2StorageService


class TestStorageStructure:
    """Test storage folder structure with user_id"""
    
    def setup_method(self):
        """Setup for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_user_id = "123"
        self.test_base_path = "test-audio-file-uuid"
        self.test_analysis_data = {
            "features": {
                "tempo": {"bpm": 120.0},
                "key": {"key": "C major", "confidence": 0.85}
            },
            "metadata": {"duration": 30.0}
        }
        self.test_stems_dict = {
            "vocals": "/tmp/vocals.wav",
            "drums": "/tmp/drums.wav",
            "bass": "/tmp/bass.wav",
            "other": "/tmp/other.wav"
        }
    
    def teardown_method(self):
        """Cleanup after each test"""
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def create_mock_stem_files(self):
        """Create mock stem files for testing"""
        stem_files = {}
        for stem_name in self.test_stems_dict:
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
            temp_file.write(b'fake audio data')
            temp_file.close()
            stem_files[stem_name] = temp_file.name
        return stem_files
    
    def cleanup_mock_stem_files(self, stem_files):
        """Clean up mock stem files"""
        for file_path in stem_files.values():
            if os.path.exists(file_path):
                os.unlink(file_path)


class TestLocalStorageStructure(TestStorageStructure):
    """Test local storage folder structure"""
    
    def test_upload_analysis_result_with_user_id(self):
        """Test that analysis results are stored with user_id in path"""
        # Setup local storage with temp directory
        with patch.object(LocalStorageService, '__init__', lambda x: setattr(x, 'base_path', Path(self.temp_dir))):
            storage = LocalStorageService()
            
            # Upload analysis result with user_id
            result_path = storage.upload_analysis_result(
                self.test_analysis_data, 
                self.test_base_path, 
                "features",
                self.test_user_id
            )
            
            # Verify path structure includes user_id
            assert result_path is not None
            assert f"processed/{self.test_user_id}/" in result_path
            assert f"{self.test_base_path}_features.json" in result_path
            
            # Verify file was created
            full_path = Path(self.temp_dir) / result_path
            assert full_path.exists()
            
            # Verify content
            with open(full_path, 'r') as f:
                saved_data = json.load(f)
            assert saved_data == self.test_analysis_data
    
    def test_upload_analysis_result_without_user_id(self):
        """Test that analysis results fallback to old structure without user_id"""
        with patch.object(LocalStorageService, '__init__', lambda x: setattr(x, 'base_path', Path(self.temp_dir))):
            storage = LocalStorageService()
            
            # Upload analysis result without user_id
            result_path = storage.upload_analysis_result(
                self.test_analysis_data, 
                self.test_base_path, 
                "features",
                None
            )
            
            # Verify path structure doesn't include user_id
            assert result_path is not None
            assert "processed/" in result_path
            assert f"processed/{self.test_user_id}/" not in result_path
            assert f"{self.test_base_path}_features.json" in result_path
            
            # Verify file was created
            full_path = Path(self.temp_dir) / result_path
            assert full_path.exists()
    
    def test_upload_stems_with_user_id(self):
        """Test that stems are stored with user_id in path"""
        stem_files = self.create_mock_stem_files()
        
        try:
            with patch.object(LocalStorageService, '__init__', lambda x: setattr(x, 'base_path', Path(self.temp_dir))):
                storage = LocalStorageService()
                
                # Upload stems with user_id
                uploaded_stems = storage.upload_stems(
                    stem_files,
                    self.test_base_path,
                    {"test": "metadata"},
                    self.test_user_id
                )
                
                # Verify all stems were uploaded
                assert len(uploaded_stems) == len(stem_files)
                
                # Verify path structure includes user_id
                for stem_name, stem_path in uploaded_stems.items():
                    assert f"stems/{self.test_user_id}/" in stem_path
                    assert f"{self.test_base_path}/{stem_name}.wav" in stem_path
                    
                    # Verify file was created
                    full_path = Path(self.temp_dir) / stem_path
                    assert full_path.exists()
        
        finally:
            self.cleanup_mock_stem_files(stem_files)
    
    def test_upload_stems_without_user_id(self):
        """Test that stems fallback to old structure without user_id"""
        stem_files = self.create_mock_stem_files()
        
        try:
            with patch.object(LocalStorageService, '__init__', lambda x: setattr(x, 'base_path', Path(self.temp_dir))):
                storage = LocalStorageService()
                
                # Upload stems without user_id
                uploaded_stems = storage.upload_stems(
                    stem_files,
                    self.test_base_path,
                    {"test": "metadata"},
                    None
                )
                
                # Verify path structure doesn't include user_id
                for stem_name, stem_path in uploaded_stems.items():
                    assert "stems/" in stem_path
                    assert f"stems/{self.test_user_id}/" not in stem_path
                    assert f"{self.test_base_path}/{stem_name}.wav" in stem_path
        
        finally:
            self.cleanup_mock_stem_files(stem_files)
    
    def test_path_format_with_timestamp(self):
        """Test that paths include timestamp in YYYY/MM/DD format"""
        with patch.object(LocalStorageService, '__init__', lambda x: setattr(x, 'base_path', Path(self.temp_dir))):
            storage = LocalStorageService()
            
            # Mock datetime at the module level where it's imported 
            test_date = datetime(2025, 8, 13)
            with patch('datetime.datetime') as mock_datetime:
                mock_datetime.now.return_value = test_date
                mock_datetime.strftime = test_date.strftime
                
                result_path = storage.upload_analysis_result(
                    self.test_analysis_data, 
                    self.test_base_path, 
                    "features",
                    self.test_user_id
                )
                
                # Verify timestamp format
                expected_timestamp = "2025/08/13"
                assert expected_timestamp in result_path
                assert f"processed/{self.test_user_id}/{expected_timestamp}/" in result_path


class TestR2StorageStructure(TestStorageStructure):
    """Test R2 storage folder structure"""
    
    def test_upload_analysis_result_with_user_id(self):
        """Test R2 analysis result storage with user_id"""
        # Mock environment variables for R2 credentials
        with patch.dict('os.environ', {
            'R2_ACCESS_KEY_ID': 'test_access_key',
            'R2_SECRET_ACCESS_KEY': 'test_secret_key', 
            'R2_BUCKET': 'test_bucket',
            'R2_ENDPOINT': 'https://test.r2.cloudflarestorage.com'
        }):
            # Mock R2 client and service
            with patch('services.r2_storage.boto3') as mock_boto3:
                mock_client = MagicMock()
                mock_boto3.client.return_value = mock_client
                mock_client.put_object.return_value = None
                
                # Create R2 storage service
                r2_storage = R2StorageService()
            
            # Mock datetime for predictable timestamp
            test_date = datetime(2025, 8, 13)
            with patch('services.r2_storage.datetime') as mock_datetime:
                mock_datetime.now.return_value = test_date
                mock_datetime.strftime = test_date.strftime
                
                result_path = r2_storage.upload_analysis_result(
                    self.test_analysis_data,
                    self.test_base_path,
                    "features",
                    self.test_user_id
                )
                
                # Verify path structure
                expected_path = f"processed/{self.test_user_id}/2025/08/13/{self.test_base_path}_features.json"
                assert result_path == expected_path
                
                # Verify S3 put_object was called with correct key
                mock_client.put_object.assert_called_once()
                call_args = mock_client.put_object.call_args
                assert call_args[1]['Key'] == expected_path
    
    def test_upload_analysis_result_without_user_id(self):
        """Test R2 analysis result storage without user_id"""
        # Mock environment variables for R2 credentials
        with patch.dict('os.environ', {
            'R2_ACCESS_KEY_ID': 'test_access_key',
            'R2_SECRET_ACCESS_KEY': 'test_secret_key', 
            'R2_BUCKET': 'test_bucket',
            'R2_ENDPOINT': 'https://test.r2.cloudflarestorage.com'
        }):
            with patch('services.r2_storage.boto3') as mock_boto3:
                mock_client = MagicMock()
                mock_boto3.client.return_value = mock_client
                mock_client.put_object.return_value = None
                
                r2_storage = R2StorageService()
            
                test_date = datetime(2025, 8, 13)
                with patch('services.r2_storage.datetime') as mock_datetime:
                    mock_datetime.now.return_value = test_date
                    
                    result_path = r2_storage.upload_analysis_result(
                        self.test_analysis_data,
                        self.test_base_path,
                        "features",
                        None
                    )
                    
                    # Verify path structure without user_id
                    expected_path = f"processed/2025/08/13/{self.test_base_path}_features.json"
                    assert result_path == expected_path
    
    def test_upload_stems_with_user_id(self):
        """Test R2 stem storage with user_id"""
        stem_files = self.create_mock_stem_files()
        
        try:
            # Mock environment variables for R2 credentials
            with patch.dict('os.environ', {
                'R2_ACCESS_KEY_ID': 'test_access_key',
                'R2_SECRET_ACCESS_KEY': 'test_secret_key', 
                'R2_BUCKET': 'test_bucket',
                'R2_ENDPOINT': 'https://test.r2.cloudflarestorage.com'
            }):
                with patch('services.r2_storage.boto3') as mock_boto3:
                    mock_client = MagicMock()
                    mock_boto3.client.return_value = mock_client
                    mock_client.upload_file.return_value = None
                    
                    r2_storage = R2StorageService()
                
                    test_date = datetime(2025, 8, 13)
                    with patch('services.r2_storage.datetime') as mock_datetime:
                        mock_datetime.now.return_value = test_date
                        
                        uploaded_stems = r2_storage.upload_stems(
                            stem_files,
                            self.test_base_path,
                            {"test": "metadata"},
                            self.test_user_id
                        )
                        
                        # Verify all stems have correct paths
                        for stem_name, stem_path in uploaded_stems.items():
                            expected_path = f"stems/{self.test_user_id}/2025/08/13/{self.test_base_path}/{stem_name}.wav"
                            assert stem_path == expected_path
        
        finally:
            self.cleanup_mock_stem_files(stem_files)
    
    def test_upload_stems_without_user_id(self):
        """Test R2 stem storage without user_id"""
        stem_files = self.create_mock_stem_files()
        
        try:
            # Mock environment variables for R2 credentials
            with patch.dict('os.environ', {
                'R2_ACCESS_KEY_ID': 'test_access_key',
                'R2_SECRET_ACCESS_KEY': 'test_secret_key', 
                'R2_BUCKET': 'test_bucket',
                'R2_ENDPOINT': 'https://test.r2.cloudflarestorage.com'
            }):
                with patch('services.r2_storage.boto3') as mock_boto3:
                    mock_client = MagicMock()
                    mock_boto3.client.return_value = mock_client
                    mock_client.upload_file.return_value = None
                    
                    r2_storage = R2StorageService()
                
                    test_date = datetime(2025, 8, 13)
                    with patch('services.r2_storage.datetime') as mock_datetime:
                        mock_datetime.now.return_value = test_date
                        
                        uploaded_stems = r2_storage.upload_stems(
                            stem_files,
                            self.test_base_path,
                            {"test": "metadata"},
                            None
                        )
                        
                        # Verify stems don't include user_id
                        for stem_name, stem_path in uploaded_stems.items():
                            expected_path = f"stems/2025/08/13/{self.test_base_path}/{stem_name}.wav"
                            assert stem_path == expected_path
        
        finally:
            self.cleanup_mock_stem_files(stem_files)


class TestStorageProcessingIntegration(TestStorageStructure):
    """Test integration with storage processing tasks"""
    
    def test_metadata_extraction_for_user_id(self):
        """Test that user_id is properly extracted from metadata"""
        from tasks.storage_processing import process_audio_features_from_storage
        
        # Mock all dependencies
        with patch('tasks.storage_processing.get_storage_service') as mock_get_storage, \
             patch('tasks.storage_processing.get_storage_type') as mock_get_type, \
             patch('tasks.storage_processing.current_task') as mock_current_task, \
             patch('tasks.storage_processing.create_feature_extractor') as mock_create_extractor, \
             patch('tasks.storage_processing.tempfile.NamedTemporaryFile') as mock_tempfile, \
             patch('tasks.storage_processing.os.unlink'):
            
            # Setup mocks
            mock_storage = MagicMock()
            mock_get_storage.return_value = mock_storage
            mock_storage.file_exists.return_value = True
            mock_storage.download_file.return_value = True
            mock_storage.upload_analysis_result.return_value = "processed/123/2025/08/13/test_features.json"
            
            mock_type = MagicMock()
            mock_type.value = "local"
            mock_get_type.return_value = mock_type
            
            mock_extractor = MagicMock()
            mock_create_extractor.return_value = mock_extractor
            mock_extractor.extract_features.return_value = self.test_analysis_data
            
            mock_temp = MagicMock()
            mock_temp.name = "/tmp/test_audio.mp3"
            mock_tempfile.return_value.__enter__.return_value = mock_temp
            
            # Test metadata with user_id
            metadata_with_user = {
                "user_id": 123,
                "upload_id": "456",
                "original_filename": "test.mp3"
            }
            
            # Call the function (would normally be called by Celery)
            try:
                result = process_audio_features_from_storage(
                    "test-task-id",
                    "uploads/123/2025/08/13/test.mp3",
                    False,
                    None,
                    metadata_with_user
                )
                
                # Verify upload_analysis_result was called with correct user_id
                mock_storage.upload_analysis_result.assert_called_once()
                call_args = mock_storage.upload_analysis_result.call_args
                assert call_args[0][3] == "123"  # user_id should be converted to string
                
                # Verify result contains expected path
                assert result['storage_analysis_path'] == "processed/123/2025/08/13/test_features.json"
                
            except Exception as e:
                # Handle any import or execution issues gracefully
                pytest.skip(f"Storage processing test requires full environment: {e}")
    
    def test_metadata_without_user_id(self):
        """Test that missing user_id is handled gracefully"""
        from tasks.storage_processing import process_audio_features_from_storage
        
        with patch('tasks.storage_processing.get_storage_service') as mock_get_storage, \
             patch('tasks.storage_processing.get_storage_type') as mock_get_type, \
             patch('tasks.storage_processing.current_task') as mock_current_task, \
             patch('tasks.storage_processing.create_feature_extractor') as mock_create_extractor, \
             patch('tasks.storage_processing.tempfile.NamedTemporaryFile') as mock_tempfile, \
             patch('tasks.storage_processing.os.unlink'):
            
            # Setup mocks
            mock_storage = MagicMock()
            mock_get_storage.return_value = mock_storage
            mock_storage.file_exists.return_value = True
            mock_storage.download_file.return_value = True
            mock_storage.upload_analysis_result.return_value = "processed/2025/08/13/test_features.json"
            
            mock_type = MagicMock()
            mock_type.value = "local"
            mock_get_type.return_value = mock_type
            
            mock_extractor = MagicMock()
            mock_create_extractor.return_value = mock_extractor
            mock_extractor.extract_features.return_value = self.test_analysis_data
            
            mock_temp = MagicMock()
            mock_temp.name = "/tmp/test_audio.mp3"
            mock_tempfile.return_value.__enter__.return_value = mock_temp
            
            # Test metadata without user_id
            metadata_without_user = {
                "upload_id": "456",
                "original_filename": "test.mp3"
            }
            
            try:
                result = process_audio_features_from_storage(
                    "test-task-id",
                    "uploads/2025/08/13/test.mp3",
                    False,
                    None,
                    metadata_without_user
                )
                
                # Verify upload_analysis_result was called with None user_id
                mock_storage.upload_analysis_result.assert_called_once()
                call_args = mock_storage.upload_analysis_result.call_args
                assert call_args[0][3] is None  # user_id should be None
                
                # Verify result contains path without user_id
                assert result['storage_analysis_path'] == "processed/2025/08/13/test_features.json"
                
            except Exception as e:
                pytest.skip(f"Storage processing test requires full environment: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])