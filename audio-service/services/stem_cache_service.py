"""
Stem Cache Service
Handles intelligent caching and retrieval of audio stems to optimize effects processing
"""

import os
import tempfile
import logging
import hashlib
import librosa
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from datetime import datetime

from services.storage_service import get_storage_service, get_storage_type
from utils.audio_utils import load_audio_from_bytes

logger = logging.getLogger(__name__)


class StemCacheService:
    """Service for managing stem caching and retrieval"""
    
    def __init__(self):
        self.storage = get_storage_service()
        self.storage_type = get_storage_type()
        
    def generate_audio_hash(self, audio_path: str) -> str:
        """Generate a hash of the audio file for cache key generation"""
        try:
            # Create hash based on file content and size for uniqueness
            with open(audio_path, 'rb') as f:
                file_content = f.read()
                
            # Use SHA256 for reliable hashing
            hash_obj = hashlib.sha256()
            hash_obj.update(file_content)
            
            return hash_obj.hexdigest()[:16]  # Use first 16 chars for shorter keys
            
        except Exception as e:
            logger.error(f"Failed to generate audio hash for {audio_path}: {e}")
            # Fallback to filename + size + modification time
            try:
                stat = os.stat(audio_path)
                fallback_str = f"{Path(audio_path).name}_{stat.st_size}_{stat.st_mtime}"
                return hashlib.sha256(fallback_str.encode()).hexdigest()[:16]
            except Exception:
                # Last resort: use filename only
                return hashlib.sha256(Path(audio_path).name.encode()).hexdigest()[:16]
    
    def build_stem_cache_paths(self, storage_path: str, user_id: Optional[str] = None) -> Dict[str, str]:
        """Build expected cache paths for stems based on storage path and user"""
        try:
            # Extract base filename without extension
            base_path = Path(storage_path).stem
            
            # Find existing stems by scanning storage
            return self._scan_for_existing_stems(base_path, user_id)
            
        except Exception as e:
            logger.error(f"Failed to build stem cache paths: {e}")
            return {}
    
    def _scan_for_existing_stems(self, base_path: str, user_id: Optional[str] = None) -> Dict[str, str]:
        """Scan storage for existing stems matching the base path"""
        try:
            # Define stem names to look for
            stem_names = ["vocals", "drums", "bass", "other"]
            found_stems = {}
            
            # Search pattern: stems/{user_id}/YYYY/MM/DD/{base_path}/{stem_name}.wav
            if user_id:
                search_prefix = f"stems/{user_id}"
            else:
                search_prefix = "stems"
            
            # List files in stems directory
            files = self.storage.list_files(prefix=search_prefix)
            
            for file_info in files:
                file_path = file_info['key']
                
                # Check if this file belongs to our base_path
                if f"/{base_path}/" in file_path or file_path.endswith(f"/{base_path}"):
                    # Extract stem name from filename
                    filename = Path(file_path).name
                    stem_name = Path(filename).stem
                    
                    if stem_name in stem_names:
                        found_stems[stem_name] = file_path
                        logger.debug(f"Found cached stem: {stem_name} at {file_path}")
            
            if found_stems:
                logger.info(f"Found {len(found_stems)} cached stems for {base_path}: {list(found_stems.keys())}")
            
            return found_stems
            
        except Exception as e:
            logger.error(f"Failed to scan for existing stems: {e}")
            return {}
    
    def check_stem_cache_availability(self, storage_path: str, user_id: Optional[str] = None) -> Tuple[bool, Dict[str, str]]:
        """Check if cached stems are available for the given audio file"""
        try:
            stem_paths = self.build_stem_cache_paths(storage_path, user_id)
            
            # Check if we have all 4 stems (vocals, drums, bass, other)
            required_stems = {"vocals", "drums", "bass", "other"}
            available_stems = set(stem_paths.keys())
            
            has_complete_cache = required_stems.issubset(available_stems)
            
            if has_complete_cache:
                logger.info(f"Complete stem cache available for {storage_path}")
                return True, stem_paths
            elif available_stems:
                logger.info(f"Partial stem cache available for {storage_path}: {list(available_stems)}")
                return False, stem_paths
            else:
                logger.debug(f"No stem cache found for {storage_path}")
                return False, {}
                
        except Exception as e:
            logger.error(f"Error checking stem cache availability: {e}")
            return False, {}
    
    def load_cached_stems(self, stem_paths: Dict[str, str]) -> Dict[str, np.ndarray]:
        """Load cached stems from storage into memory"""
        loaded_stems = {}
        temp_files = []
        
        try:
            for stem_name, remote_path in stem_paths.items():
                # Create temporary file for download
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_file_path = temp_file.name
                    temp_files.append(temp_file_path)
                
                # Download stem from storage
                if self.storage.download_file(remote_path, temp_file_path):
                    try:
                        # Load audio data
                        audio_data, sample_rate = librosa.load(temp_file_path, sr=None, mono=True)
                        loaded_stems[stem_name] = audio_data.astype(np.float32)
                        logger.debug(f"Loaded cached stem: {stem_name} ({len(audio_data)} samples)")
                        
                    except Exception as e:
                        logger.error(f"Failed to load audio from cached stem {stem_name}: {e}")
                else:
                    logger.error(f"Failed to download cached stem: {stem_name} from {remote_path}")
            
            if loaded_stems:
                logger.info(f"Successfully loaded {len(loaded_stems)} cached stems")
            
            return loaded_stems
            
        except Exception as e:
            logger.error(f"Error loading cached stems: {e}")
            return {}
            
        finally:
            # Cleanup temporary files
            for temp_file_path in temp_files:
                try:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temp file {temp_file_path}: {cleanup_error}")
    
    def cache_stems_to_storage(self, stems: Dict[str, np.ndarray], sample_rate: int, storage_path: str, user_id: Optional[str] = None) -> Dict[str, str]:
        """Cache stems to storage for future use"""
        try:
            base_path = Path(storage_path).stem
            temp_files = {}
            temp_file_paths = []
            
            # Save stems to temporary files
            for stem_name, audio_data in stems.items():
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                    temp_file_path = temp_file.name
                    temp_file_paths.append(temp_file_path)
                    
                    # Save audio to temporary file
                    import soundfile as sf
                    sf.write(temp_file_path, audio_data, sample_rate)
                    temp_files[stem_name] = temp_file_path
            
            # Upload stems to storage
            uploaded_stems = self.storage.upload_stems(
                stems_dict=temp_files,
                base_path=base_path,
                metadata={"cached_at": datetime.now().isoformat(), "sample_rate": sample_rate},
                user_id=user_id
            )
            
            logger.info(f"Cached {len(uploaded_stems)} stems to storage for {storage_path}")
            return uploaded_stems
            
        except Exception as e:
            logger.error(f"Failed to cache stems to storage: {e}")
            return {}
            
        finally:
            # Cleanup temporary files
            for temp_file_path in temp_file_paths:
                try:
                    if os.path.exists(temp_file_path):
                        os.unlink(temp_file_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temp file {temp_file_path}: {cleanup_error}")
    
    def get_or_create_stems(self, audio_data: np.ndarray, sample_rate: int, storage_path: str, user_id: Optional[str] = None) -> Dict[str, np.ndarray]:
        """Get cached stems or create new ones if not available"""
        try:
            # First, check if we have cached stems
            has_cache, cached_paths = self.check_stem_cache_availability(storage_path, user_id)
            
            if has_cache:
                logger.info(f"Using cached stems for {storage_path}")
                cached_stems = self.load_cached_stems(cached_paths)
                
                if cached_stems and len(cached_stems) >= 4:  # Ensure we have all stems
                    return cached_stems
                else:
                    logger.warning(f"Cached stems incomplete or failed to load, falling back to separation")
            
            # No cache available or cache failed, perform stem separation
            logger.info(f"Performing stem separation for {storage_path}")
            stems = self._perform_stem_separation(audio_data, sample_rate)
            
            # Cache the newly separated stems for future use
            if stems:
                self.cache_stems_to_storage(stems, sample_rate, storage_path, user_id)
            
            return stems
            
        except Exception as e:
            logger.error(f"Error in get_or_create_stems: {e}")
            return {}
    
    def _perform_stem_separation(self, audio_data: np.ndarray, sample_rate: int) -> Dict[str, np.ndarray]:
        """Perform actual stem separation using Demucs"""
        try:
            # Import stem separation functionality from existing code
            from tasks.effects_processing import _separate_stems
            
            return _separate_stems(audio_data, sample_rate)
            
        except Exception as e:
            logger.error(f"Stem separation failed: {e}")
            # Return empty dict on failure
            return {}


# Global instance for easy access
_stem_cache_service = None

def get_stem_cache_service() -> StemCacheService:
    """Get global stem cache service instance"""
    global _stem_cache_service
    if _stem_cache_service is None:
        _stem_cache_service = StemCacheService()
    return _stem_cache_service