"""
Unit tests for new stem management features in storage service
"""

import sys
import pytest
import tempfile
import os
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class TestStorageServiceStemFeatures:
    """Test new stem management features in storage service"""
    
    def test_check_stems_exist_all_present(self):
        """Test checking stems existence when all stems are present"""
        from services.storage_service import LocalStorageService
        
        storage = LocalStorageService()
        
        with patch.object(storage, 'find_existing_stems') as mock_find:
            mock_find.return_value = {
                "vocals": "stems/user123/2025/08/20/test_song/vocals.wav",
                "drums": "stems/user123/2025/08/20/test_song/drums.wav",
                "bass": "stems/user123/2025/08/20/test_song/bass.wav",
                "other": "stems/user123/2025/08/20/test_song/other.wav"
            }
            
            result = storage.check_stems_exist("test_song", "user123")
            
            assert result["vocals"] is True
            assert result["drums"] is True
            assert result["bass"] is True
            assert result["other"] is True

    def test_check_stems_exist_partial(self):
        """Test checking stems existence when only some stems are present"""
        from services.storage_service import LocalStorageService
        
        storage = LocalStorageService()
        
        with patch.object(storage, 'find_existing_stems') as mock_find:
            mock_find.return_value = {
                "vocals": "stems/user123/2025/08/20/test_song/vocals.wav",
                "drums": "stems/user123/2025/08/20/test_song/drums.wav"
            }
            
            result = storage.check_stems_exist("test_song", "user123")
            
            assert result["vocals"] is True
            assert result["drums"] is True
            assert result["bass"] is False
            assert result["other"] is False

    def test_check_stems_exist_error_handling(self):
        """Test error handling in check_stems_exist"""
        from services.storage_service import LocalStorageService
        
        storage = LocalStorageService()
        
        with patch.object(storage, 'find_existing_stems') as mock_find:
            mock_find.side_effect = Exception("Storage error")
            
            result = storage.check_stems_exist("test_song", "user123")
            
            # Should return all False on error
            assert result["vocals"] is False
            assert result["drums"] is False
            assert result["bass"] is False
            assert result["other"] is False

    def test_find_existing_stems_with_user_id(self):
        """Test finding existing stems with user ID"""
        from services.storage_service import LocalStorageService
        
        storage = LocalStorageService()
        
        with patch.object(storage, 'list_files') as mock_list:
            # Mock should only return files for the requested user
            mock_list.return_value = [
                {'key': 'stems/user123/2025/08/20/test_song/vocals.wav'},
                {'key': 'stems/user123/2025/08/20/test_song/drums.wav'}
            ]
            
            result = storage.find_existing_stems("test_song", "user123")
            
            assert len(result) == 2
            assert "vocals" in result
            assert "drums" in result
            assert "user123" in result["vocals"]
            assert "user123" in result["drums"]
            
            # Verify list_files was called with correct prefix
            mock_list.assert_called_once_with(prefix="stems/user123")

    def test_find_existing_stems_without_user_id(self):
        """Test finding existing stems without user ID"""
        from services.storage_service import LocalStorageService
        
        storage = LocalStorageService()
        
        with patch.object(storage, 'list_files') as mock_list:
            mock_list.return_value = [
                {'key': 'stems/2025/08/20/test_song/vocals.wav'},
                {'key': 'stems/2025/08/20/test_song/drums.wav'}
            ]
            
            result = storage.find_existing_stems("test_song", None)
            
            assert len(result) == 2
            assert "vocals" in result
            assert "drums" in result
            
            # Verify list_files was called with correct prefix
            mock_list.assert_called_once_with(prefix="stems")

    def test_find_existing_stems_error_handling(self):
        """Test error handling in find_existing_stems"""
        from services.storage_service import LocalStorageService
        
        storage = LocalStorageService()
        
        with patch.object(storage, 'list_files') as mock_list:
            mock_list.side_effect = Exception("Storage error")
            
            result = storage.find_existing_stems("test_song", "user123")
            
            assert result == {}

    @patch('tempfile.NamedTemporaryFile')
    @patch('soundfile.write')
    def test_save_processed_audio_with_user_id(self, mock_sf_write, mock_temp_file):
        """Test saving processed audio with user ID"""
        from services.storage_service import LocalStorageService
        
        storage = LocalStorageService()
        
        # Mock temporary file
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_audio.wav"
        
        with patch.object(storage, 'upload_file') as mock_upload, \
             patch('datetime.datetime') as mock_datetime:
            
            mock_datetime.now.return_value.strftime.return_value = "2025/08/20"
            mock_upload.return_value = True
            
            audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)
            
            result = storage.save_processed_audio(
                audio_data=audio_data,
                sample_rate=44100,
                storage_path="uploads/user123/test_song.mp3",
                user_id="user123",
                suffix="effects_processed",
                format="wav"
            )
            
            assert result is not None
            assert "processed/user123/2025/08/20/test_song_effects_processed.wav" == result
            
            # Verify soundfile.write was called
            mock_sf_write.assert_called_once_with("/tmp/test_audio.wav", audio_data, 44100)
            
            # Verify upload_file was called
            mock_upload.assert_called_once()

    @patch('tempfile.NamedTemporaryFile')
    @patch('soundfile.write')
    def test_save_processed_audio_without_user_id(self, mock_sf_write, mock_temp_file):
        """Test saving processed audio without user ID"""
        from services.storage_service import LocalStorageService
        
        storage = LocalStorageService()
        
        # Mock temporary file
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_audio.wav"
        
        with patch.object(storage, 'upload_file') as mock_upload, \
             patch('datetime.datetime') as mock_datetime:
            
            mock_datetime.now.return_value.strftime.return_value = "2025/08/20"
            mock_upload.return_value = True
            
            audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)
            
            result = storage.save_processed_audio(
                audio_data=audio_data,
                sample_rate=44100,
                storage_path="uploads/test_song.mp3",
                user_id=None,
                suffix="effects_processed",
                format="mp3"
            )
            
            assert result is not None
            assert "processed/2025/08/20/test_song_effects_processed.mp3" == result

    @patch('tempfile.NamedTemporaryFile')
    @patch('soundfile.write')
    def test_save_processed_audio_upload_failure(self, mock_sf_write, mock_temp_file):
        """Test handling upload failure in save_processed_audio"""
        from services.storage_service import LocalStorageService
        
        storage = LocalStorageService()
        
        # Mock temporary file
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_audio.wav"
        
        with patch.object(storage, 'upload_file') as mock_upload:
            mock_upload.return_value = False  # Upload fails
            
            audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)
            
            result = storage.save_processed_audio(
                audio_data=audio_data,
                sample_rate=44100,
                storage_path="uploads/test_song.mp3",
                user_id="user123"
            )
            
            assert result is None

    @patch('tempfile.NamedTemporaryFile')
    def test_save_processed_audio_soundfile_error(self, mock_temp_file):
        """Test handling soundfile write error in save_processed_audio"""
        from services.storage_service import LocalStorageService
        
        storage = LocalStorageService()
        
        # Mock temporary file
        mock_temp_file.return_value.__enter__.return_value.name = "/tmp/test_audio.wav"
        
        with patch('soundfile.write') as mock_sf_write:
            mock_sf_write.side_effect = Exception("Soundfile error")
            
            audio_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)
            
            result = storage.save_processed_audio(
                audio_data=audio_data,
                sample_rate=44100,
                storage_path="uploads/test_song.mp3",
                user_id="user123"
            )
            
            assert result is None


class TestStorageServiceStemPathMatching:
    """Test path matching logic for stem finding"""
    
    def test_stem_path_matching_accuracy(self):
        """Test that stem path matching correctly identifies stems for specific songs"""
        from services.storage_service import LocalStorageService
        
        storage = LocalStorageService()
        
        with patch.object(storage, 'list_files') as mock_list:
            # Simulate complex file structure with multiple songs
            mock_list.return_value = [
                {'key': 'stems/user123/2025/08/20/song_one/vocals.wav'},
                {'key': 'stems/user123/2025/08/20/song_one/drums.wav'},
                {'key': 'stems/user123/2025/08/20/song_one_remix/vocals.wav'},  # Similar name
                {'key': 'stems/user123/2025/08/20/another_song_one/bass.wav'},  # Contains song name
                {'key': 'stems/user123/2025/08/19/song_one/other.wav'},  # Different date
                {'key': 'uploads/user123/2025/08/20/song_one.mp3'}  # Not a stem
            ]
            
            result = storage.find_existing_stems("song_one", "user123")
            
            # Should only find stems that exactly match the path structure
            assert len(result) == 3  # vocals, drums from today, other from yesterday
            assert "vocals" in result
            assert "drums" in result
            assert "other" in result
            
            # Verify exact path matching
            assert "2025/08/20/song_one/" in result["vocals"]
            assert "2025/08/20/song_one/" in result["drums"]
            assert "2025/08/19/song_one/" in result["other"]


class TestStorageServiceStemManagementIntegration:
    """Test integration of all stem management features"""
    
    def test_complete_stem_workflow(self):
        """Test complete workflow: check -> find -> cache"""
        from services.storage_service import LocalStorageService
        
        storage = LocalStorageService()
        
        with patch.object(storage, 'list_files') as mock_list:
            # Simulate finding existing stems
            mock_list.return_value = [
                {'key': 'stems/user123/2025/08/20/test_song/vocals.wav'},
                {'key': 'stems/user123/2025/08/20/test_song/drums.wav'}
            ]
            
            # Step 1: Check which stems exist
            stem_status = storage.check_stems_exist("test_song", "user123")
            assert stem_status["vocals"] is True
            assert stem_status["drums"] is True
            assert stem_status["bass"] is False
            assert stem_status["other"] is False
            
            # Step 2: Find existing stems
            existing_stems = storage.find_existing_stems("test_song", "user123")
            assert len(existing_stems) == 2
            assert "vocals" in existing_stems
            assert "drums" in existing_stems
            
            # Step 3: Could then use these for caching logic
            missing_stems = [stem for stem in ["vocals", "drums", "bass", "other"] 
                           if stem not in existing_stems]
            assert missing_stems == ["bass", "other"]


if __name__ == "__main__":
    pytest.main([__file__])