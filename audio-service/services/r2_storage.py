"""
Cloudflare R2 Storage Service
Handles file operations for shared storage between Laravel app and microservice
"""

import boto3
import os
import logging
import tempfile
import json
from typing import Optional, BinaryIO, Dict, List, Tuple, Union
from pathlib import Path
from datetime import datetime
from botocore.exceptions import ClientError, NoCredentialsError
from io import BytesIO

logger = logging.getLogger(__name__)


class R2StorageError(Exception):
    """Custom exception for R2 storage operations"""
    pass


class R2StorageService:
    """
    Cloudflare R2 Storage Service for audio processing microservice
    """
    
    def __init__(self):
        """Initialize R2 client with environment variables"""
        try:
            # Load environment variables
            self.access_key = os.getenv('R2_ACCESS_KEY_ID')
            self.secret_key = os.getenv('R2_SECRET_ACCESS_KEY')
            self.endpoint_url = os.getenv('R2_ENDPOINT')
            self.bucket_name = os.getenv('R2_BUCKET', 'forge-audio')
            self.public_url = os.getenv('R2_PUBLIC_URL')
            
            if not all([self.access_key, self.secret_key, self.endpoint_url]):
                raise R2StorageError(
                    "Missing R2 credentials. Set R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY, and R2_ENDPOINT"
                )
            
            # Initialize boto3 S3 client for R2
            self.client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key,
                aws_secret_access_key=self.secret_key,
                region_name='auto'
            )
            
            # Test connection
            self._test_connection()
            logger.info(f"R2StorageService initialized successfully for bucket: {self.bucket_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize R2StorageService: {e}")
            raise R2StorageError(f"R2 initialization failed: {e}")
    
    def _test_connection(self) -> bool:
        """Test R2 connection by attempting to list bucket contents"""
        try:
            self.client.head_bucket(Bucket=self.bucket_name)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                raise R2StorageError(f"Bucket '{self.bucket_name}' not found")
            elif error_code == '403':
                raise R2StorageError("Access denied. Check R2 credentials and permissions")
            else:
                raise R2StorageError(f"Connection test failed: {e}")
    
    def download_file(self, r2_path: str, local_path: str) -> bool:
        """
        Download file from R2 to local storage
        
        Args:
            r2_path: Path in R2 bucket
            local_path: Local file path to save to
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Ensure local directory exists
            Path(local_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Download file
            self.client.download_file(self.bucket_name, r2_path, local_path)
            
            logger.info(f"Downloaded file from R2: {r2_path} -> {local_path}")
            return True
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                logger.error(f"File not found in R2: {r2_path}")
            else:
                logger.error(f"Failed to download file from R2 {r2_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error downloading from R2 {r2_path}: {e}")
            return False
    
    def download_to_bytes(self, r2_path: str) -> Optional[bytes]:
        """
        Download file from R2 directly to bytes
        
        Args:
            r2_path: Path in R2 bucket
            
        Returns:
            bytes: File contents or None if failed
        """
        try:
            response = self.client.get_object(Bucket=self.bucket_name, Key=r2_path)
            content = response['Body'].read()
            
            logger.info(f"Downloaded file from R2 to bytes: {r2_path} ({len(content)} bytes)")
            return content
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'NoSuchKey':
                logger.error(f"File not found in R2: {r2_path}")
            else:
                logger.error(f"Failed to download file from R2 {r2_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error downloading from R2 {r2_path}: {e}")
            return None
    
    def upload_file(self, local_path: str, r2_path: str, metadata: Optional[Dict[str, str]] = None) -> bool:
        """
        Upload file from local storage to R2
        
        Args:
            local_path: Local file path
            r2_path: Destination path in R2 bucket
            metadata: Optional metadata dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not Path(local_path).exists():
                logger.error(f"Local file does not exist: {local_path}")
                return False
            
            extra_args = {}
            if metadata:
                extra_args['Metadata'] = metadata
            
            # Upload file
            self.client.upload_file(local_path, self.bucket_name, r2_path, ExtraArgs=extra_args)
            
            logger.info(f"Uploaded file to R2: {local_path} -> {r2_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload file to R2 {r2_path}: {e}")
            return False
    
    def upload_bytes(self, data: bytes, r2_path: str, content_type: str = None, metadata: Optional[Dict[str, str]] = None) -> bool:
        """
        Upload bytes data directly to R2
        
        Args:
            data: Bytes data to upload
            r2_path: Destination path in R2 bucket
            content_type: MIME type of the content
            metadata: Optional metadata dictionary
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            extra_args = {}
            if content_type:
                extra_args['ContentType'] = content_type
            if metadata:
                extra_args['Metadata'] = metadata
            
            # Upload bytes
            self.client.put_object(
                Bucket=self.bucket_name,
                Key=r2_path,
                Body=data,
                **extra_args
            )
            
            logger.info(f"Uploaded bytes to R2: {r2_path} ({len(data)} bytes)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload bytes to R2 {r2_path}: {e}")
            return False
    
    def upload_stems(self, stems_dict: Dict[str, str], base_path: str, metadata: Optional[Dict[str, str]] = None, user_id: Optional[str] = None) -> Dict[str, str]:
        """
        Upload separated stems to R2
        
        Args:
            stems_dict: Dictionary mapping stem names to local file paths
            base_path: Base path for stems (usually upload UUID)
            metadata: Optional metadata for all stems
            user_id: User ID for organizing stems
            
        Returns:
            Dict[str, str]: Mapping of stem names to R2 paths
        """
        uploaded_stems = {}
        
        # Create timestamped directory for stems
        timestamp = datetime.now().strftime('%Y/%m/%d')
        
        for stem_name, local_path in stems_dict.items():
            if not Path(local_path).exists():
                logger.warning(f"Stem file does not exist: {local_path}")
                continue
            
            # Create R2 path for stem with user_id
            if user_id:
                r2_path = f"stems/{user_id}/{timestamp}/{base_path}/{stem_name}.wav"
            else:
                r2_path = f"stems/{timestamp}/{base_path}/{stem_name}.wav"
            
            # Add stem-specific metadata
            stem_metadata = metadata.copy() if metadata else {}
            stem_metadata.update({
                'stem_type': stem_name,
                'original_file': base_path,
                'upload_timestamp': datetime.now().isoformat()
            })
            
            if self.upload_file(local_path, r2_path, stem_metadata):
                uploaded_stems[stem_name] = r2_path
                logger.info(f"Uploaded stem '{stem_name}' to R2: {r2_path}")
            else:
                logger.error(f"Failed to upload stem '{stem_name}': {local_path}")
        
        return uploaded_stems
    
    def upload_analysis_result(self, analysis_data: dict, base_path: str, analysis_type: str = "features", user_id: Optional[str] = None) -> Optional[str]:
        """
        Upload analysis results to R2 as JSON
        
        Args:
            analysis_data: Analysis results dictionary
            base_path: Base path (usually upload UUID)
            analysis_type: Type of analysis (features, full, etc.)
            user_id: User ID for organizing results
            
        Returns:
            str: R2 path of uploaded analysis or None if failed
        """
        try:
            timestamp = datetime.now().strftime('%Y/%m/%d')
            
            if user_id:
                r2_path = f"processed/{user_id}/{timestamp}/{base_path}_{analysis_type}.json"
            else:
                r2_path = f"processed/{timestamp}/{base_path}_{analysis_type}.json"
            
            # Prepare analysis data with metadata
            analysis_with_metadata = {
                'analysis_data': analysis_data,
                'metadata': {
                    'analysis_type': analysis_type,
                    'processed_at': datetime.now().isoformat(),
                    'microservice_version': '1.0.0',
                    'original_file': base_path
                }
            }
            
            # Convert to JSON bytes
            json_data = json.dumps(analysis_with_metadata, indent=2).encode('utf-8')
            
            # Upload to R2
            if self.upload_bytes(json_data, r2_path, 'application/json'):
                logger.info(f"Uploaded analysis results to R2: {r2_path}")
                return r2_path
            else:
                return None
                
        except Exception as e:
            logger.error(f"Failed to upload analysis results: {e}")
            return None
    
    def file_exists(self, r2_path: str) -> bool:
        """
        Check if file exists in R2
        
        Args:
            r2_path: Path in R2 bucket
            
        Returns:
            bool: True if file exists
        """
        try:
            self.client.head_object(Bucket=self.bucket_name, Key=r2_path)
            return True
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                return False
            else:
                logger.warning(f"Error checking file existence {r2_path}: {e}")
                return False
    
    def delete_file(self, r2_path: str) -> bool:
        """
        Delete file from R2
        
        Args:
            r2_path: Path in R2 bucket
            
        Returns:
            bool: True if successful
        """
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=r2_path)
            logger.info(f"Deleted file from R2: {r2_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete file from R2 {r2_path}: {e}")
            return False
    
    def delete_stems(self, stems_paths: Dict[str, str]) -> Dict[str, bool]:
        """
        Delete multiple stem files from R2
        
        Args:
            stems_paths: Dictionary mapping stem names to R2 paths
            
        Returns:
            Dict[str, bool]: Deletion results for each stem
        """
        results = {}
        for stem_name, r2_path in stems_paths.items():
            results[stem_name] = self.delete_file(r2_path)
        return results
    
    def get_public_url(self, r2_path: str) -> Optional[str]:
        """
        Get public URL for R2 file
        
        Args:
            r2_path: Path in R2 bucket
            
        Returns:
            str: Public URL or None if not available
        """
        if not self.public_url:
            logger.warning("R2_PUBLIC_URL not configured")
            return None
        
        return f"{self.public_url.rstrip('/')}/{r2_path}"
    
    def get_signed_url(self, r2_path: str, expires_in: int = 3600) -> Optional[str]:
        """
        Generate signed URL for private R2 file access
        
        Args:
            r2_path: Path in R2 bucket
            expires_in: URL expiration time in seconds (default: 1 hour)
            
        Returns:
            str: Signed URL or None if failed
        """
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': self.bucket_name, 'Key': r2_path},
                ExpiresIn=expires_in
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate signed URL for {r2_path}: {e}")
            return None
    
    def list_files(self, prefix: str = "", max_keys: int = 1000) -> List[Dict[str, any]]:
        """
        List files in R2 bucket with optional prefix filter
        
        Args:
            prefix: Prefix to filter files
            max_keys: Maximum number of keys to return
            
        Returns:
            List of file information dictionaries
        """
        try:
            response = self.client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'etag': obj['ETag'].strip('"')
                })
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files with prefix '{prefix}': {e}")
            return []
    
    def get_file_info(self, r2_path: str) -> Optional[Dict[str, any]]:
        """
        Get file metadata from R2
        
        Args:
            r2_path: Path in R2 bucket
            
        Returns:
            Dict with file information or None if not found
        """
        try:
            response = self.client.head_object(Bucket=self.bucket_name, Key=r2_path)
            
            return {
                'key': r2_path,
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'content_type': response.get('ContentType', 'unknown'),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                return None
            else:
                logger.error(f"Failed to get file info for {r2_path}: {e}")
                return None


# Global instance
_r2_storage_instance = None


def get_r2_storage() -> R2StorageService:
    """
    Get global R2 storage instance (singleton pattern)
    
    Returns:
        R2StorageService: Global instance
    """
    global _r2_storage_instance
    
    if _r2_storage_instance is None:
        _r2_storage_instance = R2StorageService()
    
    return _r2_storage_instance


def is_r2_enabled() -> bool:
    """
    Check if R2 storage is enabled and properly configured
    
    Returns:
        bool: True if R2 is available
    """
    try:
        r2_enabled = os.getenv('R2_ENABLED', 'false').lower() == 'true'
        required_vars = ['R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 'R2_ENDPOINT']
        has_credentials = all(os.getenv(var) for var in required_vars)
        
        return r2_enabled and has_credentials
    except Exception:
        return False