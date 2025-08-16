"""
Unified Storage Service
Handles local file system storage
"""

import os
import logging
from typing import Optional, Dict, List, Union, BinaryIO
from pathlib import Path
from abc import ABC, abstractmethod
from enum import Enum

logger = logging.getLogger(__name__)


class StorageType(Enum):
    LOCAL = "local"


class StorageError(Exception):
    """Base exception for storage operations"""
    pass


class StorageService(ABC):
    """Abstract base class for storage services"""
    
    @abstractmethod
    def file_exists(self, path: str) -> bool:
        """Check if file exists"""
        pass
    
    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str, metadata: Optional[Dict[str, str]] = None) -> bool:
        """Upload file to storage"""
        pass
    
    @abstractmethod
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Download file from storage"""
        pass
    
    @abstractmethod
    def delete_file(self, path: str) -> bool:
        """Delete file from storage"""
        pass
    
    @abstractmethod
    def list_files(self, prefix: str = "", max_keys: int = 1000) -> List[Dict[str, any]]:
        """List files in storage"""
        pass
    
    @abstractmethod
    def get_file_info(self, path: str) -> Optional[Dict[str, any]]:
        """Get file information"""
        pass
    
    @abstractmethod
    def get_public_url(self, path: str) -> Optional[str]:
        """Get public URL for file"""
        pass
    
    @abstractmethod
    def upload_analysis_result(self, analysis_data: dict, base_path: str, analysis_type: str = "features", user_id: Optional[str] = None) -> Optional[str]:
        """Upload analysis results"""
        pass
    
    @abstractmethod
    def upload_stems(self, stems_dict: Dict[str, str], base_path: str, metadata: Optional[Dict[str, str]] = None, user_id: Optional[str] = None) -> Dict[str, str]:
        """Upload separated audio stems"""
        pass


class LocalStorageService(StorageService):
    """Local file system storage implementation"""
    
    def __init__(self):
        from config import settings
        self.base_path = Path(settings.LOCAL_STORAGE_PATH)
        self.processed_path = self.base_path / 'processed'
        self.stems_path = self.base_path / 'stems'
        self.uploads_path = self.base_path / 'uploads'
        self.temp_path = self.base_path / 'temp'
        
        # Create directories if they don't exist
        for path in [self.processed_path, self.stems_path, self.uploads_path, self.temp_path]:
            path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Local storage initialized at: {self.base_path}")
    
    def file_exists(self, path: str) -> bool:
        """Check if file exists in local storage"""
        full_path = self.base_path / path
        logger.info(f"Checking if file exists: {full_path} (base_path: {self.base_path}, relative_path: {path})")
        exists = full_path.exists()
        logger.info(f"File exists check result: {exists}")
        return exists
    
    def upload_file(self, local_path: str, remote_path: str, metadata: Optional[Dict[str, str]] = None) -> bool:
        """Copy file to local storage"""
        try:
            src = Path(local_path)
            dest = self.base_path / remote_path
            
            # Create parent directories
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            import shutil
            shutil.copy2(src, dest)
            
            # Store metadata if provided (as a sidecar file)
            if metadata:
                metadata_file = dest.with_suffix(dest.suffix + '.meta')
                import json
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)
            
            logger.info(f"File uploaded to local storage: {local_path} -> {remote_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload file to local storage: {e}")
            return False
    
    def download_file(self, remote_path: str, local_path: str) -> bool:
        """Copy file from local storage"""
        try:
            src = self.base_path / remote_path
            dest = Path(local_path)
            
            if not src.exists():
                logger.error(f"File not found in local storage: {remote_path}")
                return False
            
            # Create parent directories
            dest.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            import shutil
            shutil.copy2(src, dest)
            
            logger.info(f"File downloaded from local storage: {remote_path} -> {local_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to download file from local storage: {e}")
            return False
    
    def delete_file(self, path: str) -> bool:
        """Delete file from local storage"""
        try:
            full_path = self.base_path / path
            if full_path.exists():
                full_path.unlink()
                
                # Also delete metadata file if it exists
                metadata_file = full_path.with_suffix(full_path.suffix + '.meta')
                if metadata_file.exists():
                    metadata_file.unlink()
                
                logger.info(f"File deleted from local storage: {path}")
                return True
            else:
                logger.warning(f"File not found for deletion: {path}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to delete file from local storage: {e}")
            return False
    
    def list_files(self, prefix: str = "", max_keys: int = 1000) -> List[Dict[str, any]]:
        """List files in local storage"""
        try:
            search_path = self.base_path / prefix if prefix else self.base_path
            files = []
            
            if search_path.exists():
                for file_path in search_path.rglob('*'):
                    if file_path.is_file() and not file_path.suffix == '.meta':
                        relative_path = file_path.relative_to(self.base_path)
                        stat = file_path.stat()
                        
                        files.append({
                            'key': str(relative_path),
                            'size': stat.st_size,
                            'last_modified': stat.st_mtime,
                            'local_path': str(file_path)
                        })
                        
                        if len(files) >= max_keys:
                            break
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files from local storage: {e}")
            return []
    
    def get_file_info(self, path: str) -> Optional[Dict[str, any]]:
        """Get file information from local storage"""
        try:
            full_path = self.base_path / path
            if not full_path.exists():
                return None
            
            stat = full_path.stat()
            info = {
                'size': stat.st_size,
                'last_modified': stat.st_mtime,
                'content_type': self._get_content_type(full_path),
                'metadata': {}
            }
            
            # Load metadata if available
            metadata_file = full_path.with_suffix(full_path.suffix + '.meta')
            if metadata_file.exists():
                try:
                    import json
                    with open(metadata_file, 'r') as f:
                        info['metadata'] = json.load(f)
                except Exception:
                    pass
            
            return info
            
        except Exception as e:
            logger.error(f"Failed to get file info from local storage: {e}")
            return None
    
    def get_public_url(self, path: str) -> Optional[str]:
        """Get public URL for local file (if web server is configured)"""
        public_base_url = os.getenv('LOCAL_STORAGE_PUBLIC_URL')
        if public_base_url:
            return f"{public_base_url.rstrip('/')}/{path}"
        return None
    
    def upload_analysis_result(self, analysis_data: dict, base_path: str, analysis_type: str = "features", user_id: Optional[str] = None) -> Optional[str]:
        """Upload analysis results to local storage"""
        try:
            import json
            from datetime import datetime
            
            # Create timestamped path with user_id
            timestamp = datetime.now().strftime("%Y/%m/%d")
            filename = f"{base_path}_{analysis_type}.json"
            
            if user_id:
                analysis_path = f"processed/{user_id}/{timestamp}/{filename}"
            else:
                analysis_path = f"processed/{timestamp}/{filename}"
            
            full_path = self.base_path / analysis_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write analysis data
            with open(full_path, 'w') as f:
                json.dump(analysis_data, f, indent=2)
            
            logger.info(f"Analysis result uploaded to local storage: {analysis_path}")
            return analysis_path
            
        except Exception as e:
            logger.error(f"Failed to upload analysis result: {e}")
            return None
    
    def upload_stems(self, stems_dict: Dict[str, str], base_path: str, metadata: Optional[Dict[str, str]] = None, user_id: Optional[str] = None) -> Dict[str, str]:
        """Upload separated audio stems to local storage"""
        try:
            from datetime import datetime
            import shutil
            
            # Create timestamped path with user_id
            timestamp = datetime.now().strftime("%Y/%m/%d")
            
            if user_id:
                stems_dir = f"stems/{user_id}/{timestamp}/{base_path}"
            else:
                stems_dir = f"stems/{timestamp}/{base_path}"
            
            uploaded_stems = {}
            
            for stem_name, local_stem_path in stems_dict.items():
                if not os.path.exists(local_stem_path):
                    logger.warning(f"Stem file not found: {local_stem_path}")
                    continue
                
                # Define remote path
                stem_filename = f"{stem_name}.wav"
                remote_stem_path = f"{stems_dir}/{stem_filename}"
                
                # Upload stem
                if self.upload_file(local_stem_path, remote_stem_path, metadata):
                    uploaded_stems[stem_name] = remote_stem_path
            
            logger.info(f"Uploaded {len(uploaded_stems)} stems to local storage: {stems_dir}")
            return uploaded_stems
            
        except Exception as e:
            logger.error(f"Failed to upload stems: {e}")
            return {}
    
    def _get_content_type(self, file_path: Path) -> str:
        """Get MIME type for file"""
        import mimetypes
        content_type, _ = mimetypes.guess_type(str(file_path))
        return content_type or 'application/octet-stream'





# Global storage instance
_storage_instance: Optional[StorageService] = None


def get_storage_service() -> StorageService:
    """Get the configured storage service (singleton)"""
    global _storage_instance
    
    if _storage_instance is None:
        logger.info("Initializing local file storage")
        _storage_instance = LocalStorageService()
    
    return _storage_instance


def is_storage_enabled() -> bool:
    """Check if storage is properly configured"""
    try:
        storage = get_storage_service()
        return True
    except Exception as e:
        logger.error(f"Storage not properly configured: {e}")
        return False


def get_storage_type() -> StorageType:
    """Get the current storage type"""
    return StorageType.LOCAL