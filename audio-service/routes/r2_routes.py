"""
R2 Storage Integration Routes
Handles audio processing with Cloudflare R2 storage
"""

import os
import tempfile
import time
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
import requests
import logging

from models.r2_models import (
    R2ProcessingRequest, R2ProcessingResponse,
    R2StemSeparationRequest, R2StemSeparationResponse,
    R2FileInfo, R2CallbackData, R2BatchProcessingRequest
)
from services.r2_storage import get_r2_storage, is_r2_enabled, R2StorageError
from services.audio_feature_extraction import create_feature_extractor
from tasks.audio_processing import process_audio_features_r2, separate_audio_stems_r2
from celery_app import celery_app

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/r2", tags=["R2 Storage"])


@router.get("/status")
async def r2_status():
    """Check R2 storage status and configuration"""
    try:
        if not is_r2_enabled():
            return {
                "enabled": False,
                "message": "R2 storage is not enabled or not properly configured"
            }
        
        r2_storage = get_r2_storage()
        return {
            "enabled": True,
            "bucket": r2_storage.bucket_name,
            "endpoint": r2_storage.endpoint_url,
            "public_url_available": bool(r2_storage.public_url),
            "message": "R2 storage is enabled and ready"
        }
        
    except R2StorageError as e:
        raise HTTPException(status_code=503, detail=f"R2 storage error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")


@router.post("/extract-features", response_model=R2ProcessingResponse)
async def extract_features_r2(request: R2ProcessingRequest, background_tasks: BackgroundTasks):
    """
    Extract audio features from file in R2 storage (async)
    """
    if not is_r2_enabled():
        raise HTTPException(status_code=503, detail="R2 storage is not enabled")
    
    try:
        r2_storage = get_r2_storage()
        
        # Check if file exists in R2
        if not r2_storage.file_exists(request.r2_path):
            raise HTTPException(status_code=404, detail=f"File not found in R2: {request.r2_path}")
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Queue async processing
        celery_task = process_audio_features_r2.delay(
            task_id=task_id,
            r2_path=request.r2_path,
            extract_detailed=request.extract_detailed,
            callback_url=request.callback_url,
            metadata=request.metadata
        )
        
        logger.info(f"Queued R2 feature extraction: {request.r2_path} (task: {task_id})")
        
        return R2ProcessingResponse(
            task_id=task_id,
            status="processing",
            message="Audio feature extraction started from R2 storage",
            r2_analysis_path=None,
            r2_processed_path=None
        )
        
    except R2StorageError as e:
        raise HTTPException(status_code=503, detail=f"R2 storage error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing R2 feature extraction: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@router.post("/extract-features-sync", response_model=R2ProcessingResponse)
async def extract_features_r2_sync(request: R2ProcessingRequest):
    """
    Extract audio features from file in R2 storage (synchronous)
    """
    if not is_r2_enabled():
        raise HTTPException(status_code=503, detail="R2 storage is not enabled")
    
    start_time = time.time()
    temp_file = None
    
    try:
        r2_storage = get_r2_storage()
        
        # Check if file exists in R2
        if not r2_storage.file_exists(request.r2_path):
            raise HTTPException(status_code=404, detail=f"File not found in R2: {request.r2_path}")
        
        # Create temporary file for processing
        file_extension = Path(request.r2_path).suffix
        temp_file = tempfile.NamedTemporaryFile(suffix=file_extension, delete=False)
        temp_path = temp_file.name
        temp_file.close()
        
        # Download file from R2
        if not r2_storage.download_file(request.r2_path, temp_path):
            raise HTTPException(status_code=500, detail="Failed to download file from R2")
        
        # Extract features
        extractor = create_feature_extractor(
            extract_detailed=request.extract_detailed,
            timeout=300  # 5 minute timeout for sync processing
        )
        
        result = extractor.extract_features(temp_path)
        
        # Check for errors
        if 'error' in result:
            raise HTTPException(status_code=500, detail=f"Feature extraction failed: {result['error']}")
        
        # Upload analysis results to R2
        base_path = Path(request.r2_path).stem
        analysis_type = "detailed" if request.extract_detailed else "features"
        r2_analysis_path = r2_storage.upload_analysis_result(result, base_path, analysis_type, None)
        
        processing_time = time.time() - start_time
        
        # Generate public URLs if available
        public_urls = {}
        if r2_analysis_path and r2_storage.public_url:
            public_urls['analysis'] = r2_storage.get_public_url(r2_analysis_path)
        
        logger.info(f"Completed R2 feature extraction: {request.r2_path} in {processing_time:.2f}s")
        
        return R2ProcessingResponse(
            task_id="sync",
            status="completed",
            message="Audio feature extraction completed successfully",
            r2_analysis_path=r2_analysis_path,
            r2_processed_path=None,
            public_urls=public_urls,
            processing_time=processing_time
        )
        
    except R2StorageError as e:
        raise HTTPException(status_code=503, detail=f"R2 storage error: {str(e)}")
    except Exception as e:
        logger.error(f"Error in sync R2 feature extraction: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")
    
    finally:
        # Cleanup temporary file
        if temp_file and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except Exception as e:
                logger.warning(f"Failed to cleanup temp file {temp_path}: {e}")


@router.post("/separate-stems", response_model=R2StemSeparationResponse)
async def separate_stems_r2(request: R2StemSeparationRequest, background_tasks: BackgroundTasks):
    """
    Separate audio stems from file in R2 storage (async)
    """
    if not is_r2_enabled():
        raise HTTPException(status_code=503, detail="R2 storage is not enabled")
    
    try:
        r2_storage = get_r2_storage()
        
        # Check if file exists in R2
        if not r2_storage.file_exists(request.r2_path):
            raise HTTPException(status_code=404, detail=f"File not found in R2: {request.r2_path}")
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Queue async processing
        celery_task = separate_audio_stems_r2.delay(
            task_id=task_id,
            r2_path=request.r2_path,
            model_name=request.model_name,
            callback_url=request.callback_url,
            metadata=request.metadata
        )
        
        logger.info(f"Queued R2 stem separation: {request.r2_path} (task: {task_id})")
        
        return R2StemSeparationResponse(
            task_id=task_id,
            status="processing",
            message="Audio stem separation started from R2 storage",
            model_used=request.model_name,
            r2_stems_paths=None,
            public_urls=None
        )
        
    except R2StorageError as e:
        raise HTTPException(status_code=503, detail=f"R2 storage error: {str(e)}")
    except Exception as e:
        logger.error(f"Error processing R2 stem separation: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@router.get("/file-info/{r2_path:path}", response_model=R2FileInfo)
async def get_file_info(r2_path: str):
    """
    Get information about a file in R2 storage
    """
    if not is_r2_enabled():
        raise HTTPException(status_code=503, detail="R2 storage is not enabled")
    
    try:
        r2_storage = get_r2_storage()
        
        file_info = r2_storage.get_file_info(r2_path)
        if not file_info:
            raise HTTPException(status_code=404, detail=f"File not found in R2: {r2_path}")
        
        public_url = None
        if r2_storage.public_url:
            public_url = r2_storage.get_public_url(r2_path)
        
        return R2FileInfo(
            r2_path=r2_path,
            size=file_info['size'],
            last_modified=file_info['last_modified'].isoformat(),
            content_type=file_info['content_type'],
            metadata=file_info['metadata'],
            public_url=public_url
        )
        
    except R2StorageError as e:
        raise HTTPException(status_code=503, detail=f"R2 storage error: {str(e)}")
    except Exception as e:
        logger.error(f"Error getting R2 file info: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/list-files")
async def list_files(prefix: str = "", max_keys: int = 100):
    """
    List files in R2 storage with optional prefix filter
    """
    if not is_r2_enabled():
        raise HTTPException(status_code=503, detail="R2 storage is not enabled")
    
    try:
        r2_storage = get_r2_storage()
        
        files = r2_storage.list_files(prefix=prefix, max_keys=min(max_keys, 1000))
        
        # Add public URLs if available
        if r2_storage.public_url:
            for file_info in files:
                file_info['public_url'] = r2_storage.get_public_url(file_info['key'])
        
        return {
            "files": files,
            "count": len(files),
            "prefix": prefix,
            "truncated": len(files) == max_keys
        }
        
    except R2StorageError as e:
        raise HTTPException(status_code=503, detail=f"R2 storage error: {str(e)}")
    except Exception as e:
        logger.error(f"Error listing R2 files: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/file/{r2_path:path}")
async def delete_file(r2_path: str):
    """
    Delete a file from R2 storage
    """
    if not is_r2_enabled():
        raise HTTPException(status_code=503, detail="R2 storage is not enabled")
    
    try:
        r2_storage = get_r2_storage()
        
        if not r2_storage.file_exists(r2_path):
            raise HTTPException(status_code=404, detail=f"File not found in R2: {r2_path}")
        
        if r2_storage.delete_file(r2_path):
            return {
                "message": f"File deleted successfully from R2: {r2_path}",
                "status": "deleted"
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete file from R2")
        
    except R2StorageError as e:
        raise HTTPException(status_code=503, detail=f"R2 storage error: {str(e)}")
    except Exception as e:
        logger.error(f"Error deleting R2 file: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/batch-process")
async def batch_process_r2(request: R2BatchProcessingRequest, background_tasks: BackgroundTasks):
    """
    Process multiple files from R2 storage in batch
    """
    if not is_r2_enabled():
        raise HTTPException(status_code=503, detail="R2 storage is not enabled")
    
    try:
        r2_storage = get_r2_storage()
        
        # Verify all files exist
        missing_files = []
        for r2_path in request.r2_paths:
            if not r2_storage.file_exists(r2_path):
                missing_files.append(r2_path)
        
        if missing_files:
            raise HTTPException(
                status_code=404, 
                detail=f"Files not found in R2: {', '.join(missing_files)}"
            )
        
        # Generate batch task ID
        batch_id = str(uuid.uuid4())
        task_ids = []
        
        # Queue individual processing tasks
        for r2_path in request.r2_paths:
            task_id = str(uuid.uuid4())
            
            if request.processing_type == "features":
                celery_task = process_audio_features_r2.delay(
                    task_id=task_id,
                    r2_path=r2_path,
                    extract_detailed=False,
                    callback_url=request.callback_url,
                    metadata={**request.batch_metadata, "batch_id": batch_id}
                )
            elif request.processing_type == "stems":
                celery_task = separate_audio_stems_r2.delay(
                    task_id=task_id,
                    r2_path=r2_path,
                    model_name=request.model_name,
                    callback_url=request.callback_url,
                    metadata={**request.batch_metadata, "batch_id": batch_id}
                )
            
            task_ids.append(task_id)
        
        logger.info(f"Queued batch R2 processing: {len(request.r2_paths)} files (batch: {batch_id})")
        
        return {
            "batch_id": batch_id,
            "status": "processing",
            "message": f"Batch processing started for {len(request.r2_paths)} files",
            "task_ids": task_ids,
            "processing_type": request.processing_type,
            "file_count": len(request.r2_paths)
        }
        
    except R2StorageError as e:
        raise HTTPException(status_code=503, detail=f"R2 storage error: {str(e)}")
    except Exception as e:
        logger.error(f"Error in batch R2 processing: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


async def send_callback(callback_url: str, callback_data: R2CallbackData):
    """
    Send callback notification to Laravel app
    """
    try:
        response = requests.post(
            callback_url,
            json=callback_data.model_dump(),
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        if response.status_code == 200:
            logger.info(f"Callback sent successfully to {callback_url}")
        else:
            logger.warning(f"Callback failed with status {response.status_code}: {callback_url}")
            
    except requests.RequestException as e:
        logger.error(f"Failed to send callback to {callback_url}: {e}")
    except Exception as e:
        logger.error(f"Unexpected error sending callback: {e}")