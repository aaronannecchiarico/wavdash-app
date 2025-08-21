"""
Unit tests for stem cache service
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


class TestStemCacheService:
    """Test stem cache service functionality"""
    
    def test_stem_cache_service_initialization(self):
        """Test that stem cache service initializes correctly"""
        from services.stem_cache_service import StemCacheService
        
        with patch('services.stem_cache_service.get_storage_service') as mock_storage, \
             patch('services.stem_cache_service.get_storage_type') as mock_storage_type:
            
            mock_storage.return_value = MagicMock()
            mock_storage_type.return_value = MagicMock()
            
            cache_service = StemCacheService()
            
            assert cache_service.storage is not None
            assert cache_service.storage_type is not None
            mock_storage.assert_called_once()
            mock_storage_type.assert_called_once()

    def test_generate_audio_hash_success(self):
        """Test successful audio hash generation"""
        from services.stem_cache_service import StemCacheService
        
        with patch('services.stem_cache_service.get_storage_service'), \
             patch('services.stem_cache_service.get_storage_type'):
            
            cache_service = StemCacheService()
            
            # Create temporary audio file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(b'test audio data')
                temp_file_path = temp_file.name
            
            try:
                hash_result = cache_service.generate_audio_hash(temp_file_path)
                
                assert isinstance(hash_result, str)
                assert len(hash_result) == 16  # First 16 chars of SHA256
                
            finally:
                os.unlink(temp_file_path)

    def test_generate_audio_hash_fallback(self):
        """Test audio hash generation fallback when file read fails"""
        from services.stem_cache_service import StemCacheService
        
        with patch('services.stem_cache_service.get_storage_service'), \
             patch('services.stem_cache_service.get_storage_type'):
            
            cache_service = StemCacheService()
            
            # Test with non-existent file (should use fallback)
            hash_result = cache_service.generate_audio_hash("/nonexistent/file.wav")
            
            assert isinstance(hash_result, str)
            assert len(hash_result) == 16

    @patch('services.stem_cache_service.get_storage_service')
    @patch('services.stem_cache_service.get_storage_type')
    def test_scan_for_existing_stems(self, mock_storage_type, mock_storage_service):
        """Test scanning for existing stems"""
        from services.stem_cache_service import StemCacheService
        
        # Mock storage service
        mock_storage = MagicMock()
        mock_storage.list_files.return_value = [
            {'key': 'stems/user123/2025/08/20/test_song/vocals.wav'},
            {'key': 'stems/user123/2025/08/20/test_song/drums.wav'},
            {'key': 'stems/user123/2025/08/20/other_song/bass.wav'},
            {'key': 'uploads/user123/2025/08/20/test_song.mp3'}  # Not a stem
        ]
        mock_storage_service.return_value = mock_storage
        
        cache_service = StemCacheService()
        
        found_stems = cache_service._scan_for_existing_stems("test_song", "user123")
        
        assert len(found_stems) == 2
        assert "vocals" in found_stems
        assert "drums" in found_stems
        assert "bass" not in found_stems  # Different song
        assert found_stems["vocals"] == 'stems/user123/2025/08/20/test_song/vocals.wav'
        assert found_stems["drums"] == 'stems/user123/2025/08/20/test_song/drums.wav'

    @patch('services.stem_cache_service.get_storage_service')
    @patch('services.stem_cache_service.get_storage_type')
    def test_check_stem_cache_availability_complete(self, mock_storage_type, mock_storage_service):
        """Test checking stem cache availability when complete cache exists"""
        from services.stem_cache_service import StemCacheService
        
        # Mock storage service
        mock_storage = MagicMock()
        mock_storage.list_files.return_value = [
            {'key': 'stems/user123/2025/08/20/test_song/vocals.wav'},
            {'key': 'stems/user123/2025/08/20/test_song/drums.wav'},
            {'key': 'stems/user123/2025/08/20/test_song/bass.wav'},
            {'key': 'stems/user123/2025/08/20/test_song/other.wav'}
        ]
        mock_storage_service.return_value = mock_storage
        
        cache_service = StemCacheService()
        
        has_complete, stem_paths = cache_service.check_stem_cache_availability(
            "uploads/user123/test_song.mp3", "user123"
        )
        
        assert has_complete is True
        assert len(stem_paths) == 4
        assert all(stem in stem_paths for stem in ["vocals", "drums", "bass", "other"])

    @patch('services.stem_cache_service.get_storage_service')
    @patch('services.stem_cache_service.get_storage_type')
    def test_check_stem_cache_availability_partial(self, mock_storage_type, mock_storage_service):
        """Test checking stem cache availability when partial cache exists"""
        from services.stem_cache_service import StemCacheService
        
        # Mock storage service
        mock_storage = MagicMock()
        mock_storage.list_files.return_value = [
            {'key': 'stems/user123/2025/08/20/test_song/vocals.wav'},
            {'key': 'stems/user123/2025/08/20/test_song/drums.wav'}
        ]
        mock_storage_service.return_value = mock_storage
        
        cache_service = StemCacheService()
        
        has_complete, stem_paths = cache_service.check_stem_cache_availability(
            "uploads/user123/test_song.mp3", "user123"
        )
        
        assert has_complete is False
        assert len(stem_paths) == 2
        assert "vocals" in stem_paths
        assert "drums" in stem_paths

    @patch('services.stem_cache_service.get_storage_service')
    @patch('services.stem_cache_service.get_storage_type')
    @patch('librosa.load')
    @patch('tempfile.NamedTemporaryFile')
    def test_load_cached_stems_success(self, mock_temp_file, mock_librosa, mock_storage_type, mock_storage_service):
        """Test successful loading of cached stems"""
        from services.stem_cache_service import StemCacheService
        
        # Mock storage service
        mock_storage = MagicMock()
        mock_storage.download_file.return_value = True
        mock_storage_service.return_value = mock_storage
        
        # Mock librosa loading
        mock_audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        mock_librosa.return_value = (mock_audio_data, 44100)
        
        # Mock temporary file
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_stem.wav"
        
        cache_service = StemCacheService()
        
        stem_paths = {
            "vocals": "stems/user123/2025/08/20/test_song/vocals.wav",
            "drums": "stems/user123/2025/08/20/test_song/drums.wav"
        }
        
        loaded_stems = cache_service.load_cached_stems(stem_paths)
        
        assert len(loaded_stems) == 2
        assert "vocals" in loaded_stems
        assert "drums" in loaded_stems
        assert isinstance(loaded_stems["vocals"], np.ndarray)
        assert isinstance(loaded_stems["drums"], np.ndarray)
        
        # Verify storage downloads were called
        assert mock_storage.download_file.call_count == 2

    @patch('services.stem_cache_service.get_storage_service')
    @patch('services.stem_cache_service.get_storage_type')
    @patch('tempfile.NamedTemporaryFile')
    @patch('soundfile.write')
    def test_cache_stems_to_storage_success(self, mock_sf_write, mock_temp_file, mock_storage_type, mock_storage_service):
        """Test successful caching of stems to storage"""
        from services.stem_cache_service import StemCacheService
        
        # Mock storage service
        mock_storage = MagicMock()
        mock_storage.upload_stems.return_value = {
            "vocals": "stems/user123/2025/08/20/test_song/vocals.wav",
            "drums": "stems/user123/2025/08/20/test_song/drums.wav"
        }
        mock_storage_service.return_value = mock_storage
        
        # Mock temporary file
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_stem.wav"
        
        cache_service = StemCacheService()
        
        stems = {
            "vocals": np.array([0.1, 0.2, 0.3], dtype=np.float32),
            "drums": np.array([0.4, 0.5, 0.6], dtype=np.float32)
        }
        
        uploaded_paths = cache_service.cache_stems_to_storage(
            stems=stems,
            sample_rate=44100,
            storage_path="uploads/user123/test_song.mp3",
            user_id="user123"
        )
        
        assert len(uploaded_paths) == 2
        assert "vocals" in uploaded_paths
        assert "drums" in uploaded_paths
        
        # Verify stems were written to temporary files
        assert mock_sf_write.call_count == 2
        
        # Verify storage upload was called
        mock_storage.upload_stems.assert_called_once()

    @patch('services.stem_cache_service.get_storage_service')
    @patch('services.stem_cache_service.get_storage_type')
    def test_get_or_create_stems_with_cache(self, mock_storage_type, mock_storage_service):
        """Test get_or_create_stems when cache is available"""
        from services.stem_cache_service import StemCacheService
        
        # Mock storage service
        mock_storage = MagicMock()
        mock_storage_service.return_value = mock_storage
        
        cache_service = StemCacheService()
        
        # Mock check_stem_cache_availability to return cache available
        with patch.object(cache_service, 'check_stem_cache_availability') as mock_check, \
             patch.object(cache_service, 'load_cached_stems') as mock_load:
            
            mock_check.return_value = (True, {"vocals": "path1", "drums": "path2", "bass": "path3", "other": "path4"})
            mock_stems = {
                "vocals": np.array([0.1, 0.2]),
                "drums": np.array([0.3, 0.4]),
                "bass": np.array([0.5, 0.6]),
                "other": np.array([0.7, 0.8])
            }
            mock_load.return_value = mock_stems
            
            audio_data = np.array([0.1, 0.2, 0.3])
            
            result = cache_service.get_or_create_stems(
                audio_data=audio_data,
                sample_rate=44100,
                storage_path="uploads/test.mp3",
                user_id="user123"
            )
            
            assert result == mock_stems
            mock_check.assert_called_once()
            mock_load.assert_called_once()

    @patch('services.stem_cache_service.get_storage_service')
    @patch('services.stem_cache_service.get_storage_type')
    def test_get_or_create_stems_without_cache(self, mock_storage_type, mock_storage_service):
        """Test get_or_create_stems when no cache is available"""
        from services.stem_cache_service import StemCacheService
        
        # Mock storage service
        mock_storage = MagicMock()
        mock_storage_service.return_value = mock_storage
        
        cache_service = StemCacheService()
        
        # Mock methods
        with patch.object(cache_service, 'check_stem_cache_availability') as mock_check, \
             patch.object(cache_service, '_perform_stem_separation') as mock_separate, \
             patch.object(cache_service, 'cache_stems_to_storage') as mock_cache:
            
            mock_check.return_value = (False, {})
            mock_stems = {
                "vocals": np.array([0.1, 0.2]),
                "drums": np.array([0.3, 0.4]),
                "bass": np.array([0.5, 0.6]),
                "other": np.array([0.7, 0.8])
            }
            mock_separate.return_value = mock_stems
            mock_cache.return_value = {"vocals": "path1", "drums": "path2"}
            
            audio_data = np.array([0.1, 0.2, 0.3])
            
            result = cache_service.get_or_create_stems(
                audio_data=audio_data,
                sample_rate=44100,
                storage_path="uploads/test.mp3",
                user_id="user123"
            )
            
            assert result == mock_stems
            mock_check.assert_called_once()
            mock_separate.assert_called_once_with(audio_data, 44100)
            mock_cache.assert_called_once()

    def test_get_stem_cache_service_singleton(self):
        """Test that get_stem_cache_service returns singleton instance"""
        from services.stem_cache_service import get_stem_cache_service
        
        with patch('services.stem_cache_service.get_storage_service'), \
             patch('services.stem_cache_service.get_storage_type'):
            
            service1 = get_stem_cache_service()
            service2 = get_stem_cache_service()
            
            assert service1 is service2


class TestStemCacheIntegration:
    """Test stem cache integration with storage service"""
    
    @patch('services.stem_cache_service.get_storage_service')
    @patch('services.stem_cache_service.get_storage_type')
    def test_stem_cache_with_user_paths(self, mock_storage_type, mock_storage_service):
        """Test stem caching with user-specific paths"""
        from services.stem_cache_service import StemCacheService
        
        # Mock storage service with different responses based on prefix
        mock_storage = MagicMock()
        def mock_list_files(prefix=""):
            if prefix == "stems/user123":
                return [{'key': 'stems/user123/2025/08/20/test_song/vocals.wav'}]
            elif prefix == "stems/user456":
                return [{'key': 'stems/user456/2025/08/20/test_song/vocals.wav'}]
            else:
                return []
        
        mock_storage.list_files.side_effect = mock_list_files
        mock_storage_service.return_value = mock_storage
        
        cache_service = StemCacheService()
        
        # Test for user123
        found_stems = cache_service._scan_for_existing_stems("test_song", "user123")
        assert len(found_stems) == 1
        assert "vocals" in found_stems
        assert "user123" in found_stems["vocals"]
        
        # Test for user456
        found_stems = cache_service._scan_for_existing_stems("test_song", "user456")
        assert len(found_stems) == 1
        assert "vocals" in found_stems
        assert "user456" in found_stems["vocals"]

    @patch('services.stem_cache_service.get_storage_service')
    @patch('services.stem_cache_service.get_storage_type')
    def test_stem_cache_no_user_id(self, mock_storage_type, mock_storage_service):
        """Test stem caching without user ID"""
        from services.stem_cache_service import StemCacheService
        
        # Mock storage service
        mock_storage = MagicMock()
        mock_storage.list_files.return_value = [
            {'key': 'stems/2025/08/20/test_song/vocals.wav'}
        ]
        mock_storage_service.return_value = mock_storage
        
        cache_service = StemCacheService()
        
        found_stems = cache_service._scan_for_existing_stems("test_song", None)
        assert len(found_stems) == 1
        assert "vocals" in found_stems
        assert found_stems["vocals"] == 'stems/2025/08/20/test_song/vocals.wav'


class TestStemCacheErrorHandling:
    """Test error handling in stem cache service"""
    
    @patch('services.stem_cache_service.get_storage_service')
    @patch('services.stem_cache_service.get_storage_type')
    def test_scan_stems_storage_error(self, mock_storage_type, mock_storage_service):
        """Test handling of storage errors during stem scanning"""
        from services.stem_cache_service import StemCacheService
        
        # Mock storage service to raise exception
        mock_storage = MagicMock()
        mock_storage.list_files.side_effect = Exception("Storage error")
        mock_storage_service.return_value = mock_storage
        
        cache_service = StemCacheService()
        
        found_stems = cache_service._scan_for_existing_stems("test_song", "user123")
        assert found_stems == {}

    @patch('services.stem_cache_service.get_storage_service')
    @patch('services.stem_cache_service.get_storage_type')
    def test_cache_availability_error(self, mock_storage_type, mock_storage_service):
        """Test handling of errors during cache availability check"""
        from services.stem_cache_service import StemCacheService
        
        cache_service = StemCacheService()
        
        with patch.object(cache_service, 'build_stem_cache_paths') as mock_build:
            mock_build.side_effect = Exception("Build paths error")
            
            has_cache, paths = cache_service.check_stem_cache_availability("test.mp3")
            
            assert has_cache is False
            assert paths == {}

    @patch('services.stem_cache_service.get_storage_service')
    @patch('services.stem_cache_service.get_storage_type')
    def test_load_stems_download_failure(self, mock_storage_type, mock_storage_service):
        """Test handling of download failures during stem loading"""
        from services.stem_cache_service import StemCacheService
        
        # Mock storage service
        mock_storage = MagicMock()
        mock_storage.download_file.return_value = False  # Download fails
        mock_storage_service.return_value = mock_storage
        
        cache_service = StemCacheService()
        
        stem_paths = {"vocals": "stems/path/vocals.wav"}
        loaded_stems = cache_service.load_cached_stems(stem_paths)
        
        assert loaded_stems == {}


if __name__ == "__main__":
    pytest.main([__file__])