from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import uvicorn
import logging
import redis
from contextlib import asynccontextmanager

from config import settings
from models.audio_models import AudioProcessingRequest, AudioProcessingResponse
from models.storage_models import (
    StorageProcessingRequest, StorageProcessingResponse,
    StorageStemSeparationRequest, StorageStemSeparationResponse,
    StorageFileInfo, StorageBatchProcessingRequest
)
from tasks.audio_processing import process_audio_features, separate_audio_stems
from tasks.storage_processing import (
    process_audio_features_from_storage, 
    separate_audio_stems_from_storage,
    batch_process_from_storage
)
from services.storage_service import get_storage_service, is_storage_enabled, get_storage_type
from celery_app import celery_app
from routes.tempo_processing import router as tempo_router


# Redis connection for tracking deleted tasks
redis_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_client
    logging.info("Starting audio processing microservice")
    
    # Initialize Redis connection for deleted task tracking
    try:
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
            decode_responses=True
        )
        redis_client.ping()  # Test connection
        logging.info("Redis connection established for deleted task tracking")
    except Exception as e:
        logging.error(f"Failed to connect to Redis for deleted task tracking: {e}")
        redis_client = None
    
    yield
    logging.info("Shutting down audio processing microservice")


app = FastAPI(
    title="Audio Processing Microservice",
    description="FastAPI microservice for audio feature extraction and stem separation",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include tempo processing routes
app.include_router(tempo_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors with detailed logging"""
    request_body = None
    try:
        request_body = await request.body()
        if request_body:
            request_body = request_body.decode('utf-8')
    except Exception:
        request_body = "Unable to read request body"
    
    logging.error(f"422 Validation Error on {request.method} {request.url}")
    logging.error(f"Request body: {request_body}")
    logging.error(f"Validation errors: {exc.errors()}")
    
    return JSONResponse(
        status_code=422,
        content={
            "detail": exc.errors(),
            "body": request_body if request_body != "Unable to read request body" else None
        }
    )


@app.get("/")
async def root():
    return {"message": "Audio Processing Microservice", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    from utils.device_utils import get_device_info, get_memory_usage
    
    device_info = get_device_info()
    memory_usage = get_memory_usage()
    redis_status = celery_app.control.ping()
    
    # Check storage configuration
    storage_enabled = is_storage_enabled()
    storage_type = get_storage_type().value if storage_enabled else "unavailable"
    
    return {
        "status": "healthy", 
        "redis_connected": redis_status,
        "device_info": device_info,
        "memory_usage": memory_usage,
        "storage_enabled": storage_enabled,
        "storage_type": storage_type
    }


@app.post("/extract-features", response_model=AudioProcessingResponse)
async def extract_audio_features(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    async_processing: bool = True
):
    if not audio_file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    try:
        audio_content = await audio_file.read()
        
        if async_processing:
            task = process_audio_features.delay(audio_content, audio_file.filename)
            return AudioProcessingResponse(
                task_id=task.id,
                status="processing",
                message="Audio feature extraction started"
            )
        else:
            result = process_audio_features(audio_content, audio_file.filename)
            return AudioProcessingResponse(
                task_id=None,
                status="completed",
                message="Audio features extracted successfully",
                result=result
            )
    
    except Exception as e:
        logging.error(f"Error processing audio features: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


@app.post("/separate-stems", response_model=AudioProcessingResponse)
async def separate_stems(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    model_name: str = "htdemucs",
    async_processing: bool = True
):
    if not audio_file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    try:
        audio_content = await audio_file.read()
        
        if async_processing:
            task = separate_audio_stems.delay(audio_content, audio_file.filename, model_name)
            return AudioProcessingResponse(
                task_id=task.id,
                status="processing",
                message="Audio stem separation started"
            )
        else:
            result = separate_audio_stems(audio_content, audio_file.filename, model_name)
            return AudioProcessingResponse(
                task_id=None,
                status="completed",
                message="Audio stems separated successfully",
                result=result
            )
    
    except Exception as e:
        logging.error(f"Error separating stems: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


def is_task_deleted(task_id: str) -> bool:
    """Check if a task has been marked as deleted"""
    if redis_client is None:
        return False
    try:
        return redis_client.exists(f"deleted_task:{task_id}") == 1
    except Exception as e:
        logging.error(f"Error checking deleted task status for {task_id}: {e}")
        return False


@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str, include_result: bool = False):
    """
    Get task status. Use include_result=true to get full results (may be large).
    """
    try:
        # Check if task has been deleted
        if is_task_deleted(task_id):
            return {"task_id": task_id, "status": "deleted", "message": "Task has been deleted"}
        
        task = celery_app.AsyncResult(task_id)
        
        # Safely get task state
        try:
            state = task.state
        except (ValueError, KeyError) as e:
            logging.error(f"Error getting task state for {task_id}: {e}")
            return {"task_id": task_id, "status": "error", "error": "Task state corrupted or invalid"}
        
        if state == 'PENDING':
            # Double-check if task was deleted but state check missed it
            if is_task_deleted(task_id):
                return {"task_id": task_id, "status": "deleted", "message": "Task has been deleted"}
            return {"task_id": task_id, "status": "pending", "message": "Task is waiting to be processed"}
        elif state == 'PROGRESS':
            try:
                progress_info = task.info or {}
                return {"task_id": task_id, "status": "processing", "progress": progress_info.get('progress', 0)}
            except Exception:
                return {"task_id": task_id, "status": "processing", "progress": 0}
        elif state == 'SUCCESS':
            try:
                result = task.result
                if include_result:
                    return {"task_id": task_id, "status": "completed", "result": result}
                else:
                    # Return summary without full result data
                    result_summary = {"status": "completed", "task_id": task_id}
                    if result and isinstance(result, dict):
                        # Add basic metadata without the large feature arrays
                        if 'metadata' in result and isinstance(result['metadata'], dict):
                            metadata = result['metadata']
                            result_summary['filename'] = metadata.get('filename', 'unknown')
                            result_summary['duration'] = metadata.get('duration', 0)
                            result_summary['sample_rate'] = metadata.get('sample_rate', 0)
                            result_summary['processing_time'] = metadata.get('processing_time', 0)
                        
                        if 'features' in result:
                            features = result['features']
                            result_summary['features_available'] = list(features.keys()) if isinstance(features, dict) else True
                        # For stem separation results
                        if 'stems' in result:
                            stems = result['stems']
                            result_summary['stems_available'] = list(stems.keys()) if isinstance(stems, dict) else True
                        if 'stem_count' in result:
                            result_summary['stem_count'] = result['stem_count']
                    
                    result_summary['message'] = "Task completed successfully. Use include_result=true to get full data."
                    return result_summary
            except Exception as e:
                logging.error(f"Error accessing task result for {task_id}: {e}")
                return {"task_id": task_id, "status": "error", "error": "Task result corrupted or inaccessible"}
        elif state == 'FAILURE':
            try:
                error_info = task.info or "Unknown error"
                return {"task_id": task_id, "status": "failed", "error": str(error_info)}
            except Exception:
                return {"task_id": task_id, "status": "failed", "error": "Task failed with unknown error"}
        else:
            return {"task_id": task_id, "status": state}
            
    except Exception as e:
        logging.error(f"Critical error in get_task_status for {task_id}: {e}")
        return {"task_id": task_id, "status": "error", "error": f"Unable to retrieve task status: {str(e)}"}


@app.get("/task-result/{task_id}")
async def get_task_result(task_id: str):
    """
    Get the full task result data. Warning: May be very large for audio features.
    """
    task = celery_app.AsyncResult(task_id)
    
    if task.state == 'SUCCESS':
        return {"task_id": task_id, "status": "completed", "result": task.result}
    elif task.state == 'PENDING':
        raise HTTPException(status_code=202, detail="Task is still pending")
    elif task.state == 'PROGRESS':
        raise HTTPException(status_code=202, detail="Task is still in progress")
    elif task.state == 'FAILURE':
        raise HTTPException(status_code=500, detail=f"Task failed: {str(task.info)}")
    else:
        raise HTTPException(status_code=404, detail=f"Task not found or in unknown state: {task.state}")


@app.get("/task-summary/{task_id}")
async def get_task_summary(task_id: str):
    """
    Get a lightweight summary of audio processing results - optimized for Laravel integration.
    Returns only essential metrics without large feature arrays.
    """
    try:
        # Check if task has been deleted
        if is_task_deleted(task_id):
            return {"task_id": task_id, "status": "deleted", "message": "Task has been deleted"}
        
        task = celery_app.AsyncResult(task_id)
        
        # Safely get task state
        try:
            state = task.state
        except (ValueError, KeyError) as e:
            logging.error(f"Error getting task state for {task_id}: {e}")
            return {"task_id": task_id, "status": "error", "error": "Task state corrupted or invalid"}
        
        if state == 'SUCCESS':
            try:
                result = task.result
                if not result or 'error' in result:
                    return {"task_id": task_id, "status": "failed", "error": result.get('error', 'Unknown error') if result else 'No result data'}
                
                # Extract lightweight summary
                summary = {
                    "task_id": task_id,
                    "status": "completed",
                    "metadata": result.get('metadata', {}),
                }
                
                # Extract key musical features
                if 'features' in result:
                    features = result['features']
                    summary['musical_analysis'] = {}
                    
                    # Key detection
                    if 'key' in features:
                        key_info = features['key']
                        summary['musical_analysis']['key'] = key_info.get('key', 'unknown')
                        summary['musical_analysis']['key_confidence'] = key_info.get('confidence', 0.0)
                    
                    # Tempo/BPM
                    if 'tempo' in features:
                        tempo_info = features['tempo']
                        summary['musical_analysis']['bpm'] = tempo_info.get('bpm', 0.0)
                        summary['musical_analysis']['beat_regularity'] = tempo_info.get('beat_regularity', 0.0)
                    
                    # Energy/Loudness
                    if 'energy' in features:
                        energy_info = features['energy']
                        summary['musical_analysis']['loudness_db'] = energy_info.get('overall_loudness_db', 0.0)
                        summary['musical_analysis']['dynamic_range_db'] = energy_info.get('dynamic_range_db', 0.0)
                    
                    # Spectral characteristics
                    if 'spectral' in features:
                        spectral_info = features['spectral']
                        if 'spectral_centroid' in spectral_info:
                            summary['musical_analysis']['brightness'] = spectral_info['spectral_centroid'].get('mean', 0.0)
                    
                    # MFCC summary (just overall stats)
                    if 'mfcc' in features:
                        mfcc_info = features['mfcc']
                        summary['musical_analysis']['timbral_complexity'] = mfcc_info.get('overall_std', 0.0)
                
                # Handle chunked results
                elif 'aggregated_features' in result:
                    agg_features = result['aggregated_features']
                    summary['musical_analysis'] = {}
                    
                    if 'tempo' in agg_features:
                        summary['musical_analysis']['bpm'] = agg_features['tempo'].get('mean_bpm', 0.0)
                        summary['musical_analysis']['bpm_stability'] = agg_features['tempo'].get('std_bpm', 0.0)
                    
                    if 'key' in agg_features:
                        summary['musical_analysis']['key'] = agg_features['key'].get('most_likely_key', 'unknown')
                        summary['musical_analysis']['key_confidence'] = agg_features['key'].get('confidence', 0.0)
                        summary['musical_analysis']['key_changes'] = agg_features['key'].get('key_changes', 0)
                    
                    summary['chunk_count'] = result.get('chunk_count', 0)
                
                return summary
                
            except Exception as e:
                logging.error(f"Error processing task result for {task_id}: {e}")
                return {"task_id": task_id, "status": "error", "error": "Failed to process task result"}
                
        elif state == 'PENDING':
            return {"task_id": task_id, "status": "pending", "message": "Task is waiting to be processed"}
        elif state == 'PROGRESS':
            try:
                progress_info = task.info or {}
                return {"task_id": task_id, "status": "processing", "progress": progress_info.get('progress', 0)}
            except Exception:
                return {"task_id": task_id, "status": "processing", "progress": 0}
        elif state == 'FAILURE':
            try:
                error_info = task.info or "Unknown error"
                return {"task_id": task_id, "status": "failed", "error": str(error_info)}
            except Exception:
                return {"task_id": task_id, "status": "failed", "error": "Task failed with unknown error"}
        else:
            return {"task_id": task_id, "status": state}
            
    except Exception as e:
        logging.error(f"Critical error in get_task_summary for {task_id}: {e}")
        return {"task_id": task_id, "status": "error", "error": f"Unable to retrieve task summary: {str(e)}"}


@app.delete("/task/{task_id}")
async def delete_task(task_id: str):
    """
    Delete a corrupted or stuck task from Redis
    """
    try:
        task = celery_app.AsyncResult(task_id)
        task.forget()  # Remove from backend
        
        # Mark task as deleted in our tracking system
        if redis_client is not None:
            try:
                # Store deleted task ID with expiration (24 hours)
                redis_client.setex(f"deleted_task:{task_id}", 86400, "1")
                logging.info(f"Marked task {task_id} as deleted in tracking system")
            except Exception as e:
                logging.error(f"Error marking task {task_id} as deleted: {e}")
        
        return {"task_id": task_id, "status": "deleted", "message": "Task removed from backend"}
    except Exception as e:
        logging.error(f"Error deleting task {task_id}: {e}")
        return {"task_id": task_id, "status": "error", "error": f"Failed to delete task: {str(e)}"}


@app.post("/extract-features-sync")
async def extract_features_sync(
    audio_file: UploadFile = File(...),
    extract_detailed: bool = False
):
    """
    Synchronous feature extraction for small files - returns results immediately.
    Ideal for quick analysis without task queuing.
    """
    if not audio_file.content_type.startswith('audio/'):
        raise HTTPException(status_code=400, detail="File must be an audio file")
    
    try:
        import sys
        import os
        
        # Add project root to path if not already there
        project_root = os.path.dirname(os.path.abspath(__file__))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from services.audio_feature_extraction import create_feature_extractor
        from io import BytesIO
        
        # Read file content
        audio_content = await audio_file.read()
        audio_buffer = BytesIO(audio_content)
        
        # Create extractor
        extractor = create_feature_extractor(
            extract_detailed=extract_detailed,
            chunk_duration=30.0,
            timeout=60  # Shorter timeout for sync processing
        )
        
        # Extract features
        result = extractor.extract_features(audio_buffer)
        
        # Update filename
        if 'metadata' in result:
            result['metadata']['filename'] = audio_file.filename
        
        result['processing_mode'] = 'synchronous'
        return result
        
    except Exception as e:
        logging.error(f"Sync feature extraction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")


# Storage-based endpoints
@app.get("/storage/status")
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


@app.post("/storage/extract-features", response_model=StorageProcessingResponse)
async def extract_features_from_storage(request: StorageProcessingRequest, background_tasks: BackgroundTasks):
    """
    Extract audio features from file in configured storage (async)
    """
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
        import uuid
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


@app.post("/storage/separate-stems", response_model=StorageStemSeparationResponse)
async def separate_stems_from_storage(request: StorageStemSeparationRequest, background_tasks: BackgroundTasks):
    """
    Separate audio stems from file in configured storage (async)
    """
    if not is_storage_enabled():
        raise HTTPException(status_code=503, detail="Storage is not properly configured")
    
    try:
        storage = get_storage_service()
        
        # Check if file exists in storage
        if not storage.file_exists(request.storage_path):
            raise HTTPException(status_code=404, detail=f"File not found in storage: {request.storage_path}")
        
        # Generate task ID
        import uuid
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


@app.get("/storage/file-info/{storage_path:path}", response_model=StorageFileInfo)
async def get_storage_file_info(storage_path: str):
    """
    Get information about a file in configured storage
    """
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


@app.get("/storage/list-files")
async def list_storage_files(prefix: str = "", max_keys: int = 100):
    """
    List files in configured storage with optional prefix filter
    """
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


@app.delete("/storage/file/{storage_path:path}")
async def delete_storage_file(storage_path: str):
    """
    Delete a file from configured storage
    """
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


@app.post("/storage/batch-process")
async def batch_process_storage(request: StorageBatchProcessingRequest, background_tasks: BackgroundTasks):
    """
    Process multiple files from configured storage in batch
    """
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
        import uuid
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


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )