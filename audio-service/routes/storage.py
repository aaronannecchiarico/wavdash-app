"""
Storage Routes
Handles storage-based processing for files already in configured storage
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
import logging
import uuid

from models.storage_models import (
    StorageProcessingRequest, StorageProcessingResponse,
    StorageStemSeparationRequest, StorageStemSeparationResponse,
    StorageFileInfo, StorageBatchProcessingRequest
)
from tasks.storage_processing import (
    process_audio_features_from_storage, 
    separate_audio_stems_from_storage,
    batch_process_from_storage
)
from services.storage_service import get_storage_service, is_storage_enabled, get_storage_type

router = APIRouter(prefix="/storage", tags=["Storage Processing"])


@router.get("/status")
async def storage_status():
    """Check storage configuration and status"""
    try:
        if not is_storage_enabled():
            return {
                "enabled": False,
                "message": "Storage is not properly configured"
            }
        
        storage_type = get_storage_type()
        storage = get_storage_service()
        
        return {
            "enabled": True,
            "storage_type": storage_type.value,
            "message": f"{storage_type.value.title()} storage is enabled and ready"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")


@router.post("/extract-features", response_model=StorageProcessingResponse)
async def extract_features_from_storage(request: StorageProcessingRequest, background_tasks: BackgroundTasks):
    """Extract audio features from file in configured storage (async)"""
    logging.info(f"Received storage feature extraction request: {request}")
    
    if not is_storage_enabled():
        logging.error("Storage is not properly configured")
        raise HTTPException(status_code=503, detail="Storage is not properly configured")
    
    try:
        # Validate request fields
        if not request.storage_path:
            logging.error("Missing required field: storage_path")
            raise HTTPException(status_code=422, detail="storage_path is required")
        
        logging.info(f"Processing request for storage path: {request.storage_path}")
        
        storage = get_storage_service()
        
        # Check if file exists in storage
        if not storage.file_exists(request.storage_path):
            logging.error(f"File not found in storage: {request.storage_path}")
            raise HTTPException(status_code=404, detail=f"File not found in storage: {request.storage_path}")
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        logging.info(f"Generated task ID: {task_id} for storage path: {request.storage_path}")
        
        # Queue async processing
        celery_task = process_audio_features_from_storage.delay(
            task_id=task_id,
            storage_path=request.storage_path,
            extract_detailed=request.extract_detailed,
            callback_url=request.callback_url,
            metadata=request.metadata
        )
        
        storage_type = get_storage_type()
        logging.info(f"Queued storage feature extraction: {request.storage_path} (task: {task_id}, storage: {storage_type.value})")
        
        return StorageProcessingResponse(
            task_id=task_id,
            status="processing",
            message=f"Audio feature extraction started from {storage_type.value} storage",
            storage_analysis_path=None,
            storage_processed_path=None,
            storage_type=storage_type.value
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions without wrapping
        raise
    except Exception as e:
        logging.error(f"Unexpected error processing storage feature extraction: {e}")
        logging.error(f"Request data: {request}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@router.post("/separate-stems", response_model=StorageStemSeparationResponse)
async def separate_stems_from_storage(request: StorageStemSeparationRequest, background_tasks: BackgroundTasks):
    """Separate audio stems from file in configured storage (async)"""
    if not is_storage_enabled():
        raise HTTPException(status_code=503, detail="Storage is not properly configured")
    
    try:
        storage = get_storage_service()
        
        # Check if file exists in storage
        if not storage.file_exists(request.storage_path):
            raise HTTPException(status_code=404, detail=f"File not found in storage: {request.storage_path}")
        
        # Generate task ID
        task_id = str(uuid.uuid4())
        
        # Queue async processing
        celery_task = separate_audio_stems_from_storage.delay(
            task_id=task_id,
            storage_path=request.storage_path,
            model_name=request.model_name,
            callback_url=request.callback_url,
            metadata=request.metadata
        )
        
        storage_type = get_storage_type()
        logging.info(f"Queued storage stem separation: {request.storage_path} (task: {task_id}, storage: {storage_type.value})")
        
        return StorageStemSeparationResponse(
            task_id=task_id,
            status="processing",
            message=f"Audio stem separation started from {storage_type.value} storage",
            model_used=request.model_name,
            storage_stems_paths=None,
            public_urls=None,
            storage_type=storage_type.value
        )
        
    except Exception as e:
        logging.error(f"Error processing storage stem separation: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@router.get("/file-info/{storage_path:path}", response_model=StorageFileInfo)
async def get_storage_file_info(storage_path: str):
    """Get information about a file in configured storage"""
    if not is_storage_enabled():
        raise HTTPException(status_code=503, detail="Storage is not properly configured")
    
    try:
        storage = get_storage_service()
        
        file_info = storage.get_file_info(storage_path)
        if not file_info:
            raise HTTPException(status_code=404, detail=f"File not found in storage: {storage_path}")
        
        public_url = storage.get_public_url(storage_path)
        storage_type = get_storage_type()
        
        # Convert timestamp for consistency
        import datetime
        if 'last_modified' in file_info:
            if isinstance(file_info['last_modified'], float):
                # Convert Unix timestamp to ISO format
                file_info['last_modified'] = datetime.datetime.fromtimestamp(file_info['last_modified']).isoformat()
        
        return StorageFileInfo(
            storage_path=storage_path,
            size=file_info['size'],
            last_modified=file_info['last_modified'],
            content_type=file_info['content_type'],
            metadata=file_info['metadata'],
            public_url=public_url,
            storage_type=storage_type.value
        )
        
    except Exception as e:
        logging.error(f"Error getting storage file info: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.get("/list-files")
async def list_storage_files(prefix: str = "", max_keys: int = 100):
    """List files in configured storage with optional prefix filter"""
    if not is_storage_enabled():
        raise HTTPException(status_code=503, detail="Storage is not properly configured")
    
    try:
        storage = get_storage_service()
        storage_type = get_storage_type()
        
        files = storage.list_files(prefix=prefix, max_keys=min(max_keys, 1000))
        
        # Add public URLs if available
        for file_info in files:
            public_url = storage.get_public_url(file_info['key'])
            if public_url:
                file_info['public_url'] = public_url
        
        return {
            "files": files,
            "count": len(files),
            "prefix": prefix,
            "truncated": len(files) == max_keys,
            "storage_type": storage_type.value
        }
        
    except Exception as e:
        logging.error(f"Error listing storage files: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.delete("/file/{storage_path:path}")
async def delete_storage_file(storage_path: str):
    """Delete a file from configured storage"""
    if not is_storage_enabled():
        raise HTTPException(status_code=503, detail="Storage is not properly configured")
    
    try:
        storage = get_storage_service()
        storage_type = get_storage_type()
        
        if not storage.file_exists(storage_path):
            raise HTTPException(status_code=404, detail=f"File not found in storage: {storage_path}")
        
        if storage.delete_file(storage_path):
            return {
                "message": f"File deleted successfully from {storage_type.value} storage: {storage_path}",
                "status": "deleted",
                "storage_type": storage_type.value
            }
        else:
            raise HTTPException(status_code=500, detail=f"Failed to delete file from {storage_type.value} storage")
        
    except Exception as e:
        logging.error(f"Error deleting storage file: {e}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


@router.post("/batch-process")
async def batch_process_storage(request: StorageBatchProcessingRequest, background_tasks: BackgroundTasks):
    """Process multiple files from configured storage in batch"""
    if not is_storage_enabled():
        raise HTTPException(status_code=503, detail="Storage is not properly configured")
    
    try:
        storage = get_storage_service()
        storage_type = get_storage_type()
        
        # Verify all files exist
        missing_files = []
        for storage_path in request.storage_paths:
            if not storage.file_exists(storage_path):
                missing_files.append(storage_path)
        
        if missing_files:
            raise HTTPException(
                status_code=404, 
                detail=f"Files not found in {storage_type.value} storage: {', '.join(missing_files)}"
            )
        
        # Generate batch task ID
        batch_id = str(uuid.uuid4())
        
        # Queue batch processing task
        celery_task = batch_process_from_storage.delay(
            storage_paths=request.storage_paths,
            processing_type=request.processing_type,
            model_name=request.model_name,
            callback_url=request.callback_url,
            batch_metadata={**request.batch_metadata, "batch_id": batch_id, "storage_type": storage_type.value}
        )
        
        logging.info(f"Queued batch storage processing: {len(request.storage_paths)} files (batch: {batch_id}, storage: {storage_type.value})")
        
        return {
            "batch_id": batch_id,
            "task_id": celery_task.id,
            "status": "processing",
            "message": f"Batch processing started for {len(request.storage_paths)} files from {storage_type.value} storage",
            "processing_type": request.processing_type,
            "file_count": len(request.storage_paths),
            "storage_type": storage_type.value
        }
        
    except Exception as e:
        logging.error(f"Error in batch storage processing: {e}")
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")