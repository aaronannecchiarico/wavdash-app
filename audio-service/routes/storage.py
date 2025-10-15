"""
Storage Routes
Handles storage-based processing for files already in configured storage
"""

import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from models.storage_models import (
    StorageBatchProcessingRequest,
    StorageFileInfo,
    StorageProcessingRequest,
    StorageProcessingResponse,
    StorageStemSeparationRequest,
    StorageStemSeparationResponse,
)
from services.storage_service import (
    StorageService,
)
from services.storage_service import (
    get_storage_type,
    is_storage_enabled,
)
from services.storage_service import get_storage_service as _get_storage_service
from tasks.storage_processing import (
    batch_process_from_storage,
    process_audio_features_from_storage,
    separate_audio_stems_from_storage,
)
from utils.dependencies import (
    StorageValidator,
    get_storage_service,
    get_storage_type_dependency,
)
from utils.route_helpers import (
    generate_task_id,
    get_storage_type_value,
    handle_route_error,
    validate_required_field,
    validate_storage_and_file,
    validate_storage_enabled,
)

router = APIRouter(prefix="/storage", tags=["Storage Processing"])


@router.get("/status")
def storage_status():
    """Check storage configuration and status"""
    try:
        if not is_storage_enabled():
            return {"enabled": False, "message": "Storage is not properly configured"}

        storage_type = get_storage_type()
        storage = get_storage_service()

        return {
            "enabled": True,
            "storage_type": storage_type.value,
            "message": f"{storage_type.value.title()} storage is enabled and ready",
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Storage error: {str(e)}")


@router.post("/extract-features", response_model=StorageProcessingResponse)
def extract_features_from_storage(
    request: StorageProcessingRequest,
    background_tasks: BackgroundTasks,
    storage: StorageService = Depends(get_storage_service),
    validator: StorageValidator = Depends(),
):
    """Extract audio features from file in configured storage (async)"""
    logging.info(f"Received storage feature extraction request: {request}")

    try:
        # Validate required fields and file existence
        validate_required_field(request.storage_path, "storage_path")
        validator.validate_file_exists(request.storage_path)

        logging.info(f"Processing request for storage path: {request.storage_path}")

        # Generate task ID
        task_id = generate_task_id()
        logging.info(
            f"Generated task ID: {task_id} for storage path: {request.storage_path}"
        )

        # Queue async processing
        celery_task = process_audio_features_from_storage.delay(
            task_id=task_id,
            storage_path=request.storage_path,
            extract_detailed=request.extract_detailed,
            callback_url=request.callback_url,
            metadata=request.metadata,
        )

        storage_type_value = get_storage_type_value()
        logging.info(
            f"Queued storage feature extraction: {request.storage_path} (task: {task_id}, storage: {storage_type_value})"
        )

        return StorageProcessingResponse(
            task_id=task_id,
            status="processing",
            message=f"Audio feature extraction started from {storage_type_value} storage",
            storage_analysis_path=None,
            storage_processed_path=None,
            storage_type=storage_type_value,
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error processing storage feature extraction: {e}")
        logging.error(f"Request data: {request}")
        handle_route_error(e, "storage feature extraction", {"request": str(request)})


@router.post("/separate-stems", response_model=StorageStemSeparationResponse)
def separate_stems_from_storage(
    request: StorageStemSeparationRequest,
    background_tasks: BackgroundTasks,
    storage: StorageService = Depends(get_storage_service),
    validator: StorageValidator = Depends(),
):
    """Separate audio stems from file in configured storage (async)"""
    try:
        # Validate file existence
        validator.validate_file_exists(request.storage_path)

        # Generate task ID
        task_id = generate_task_id()

        # Queue async processing
        celery_task = separate_audio_stems_from_storage.delay(
            task_id=task_id,
            storage_path=request.storage_path,
            model_name=request.model_name,
            callback_url=request.callback_url,
            metadata=request.metadata,
        )

        storage_type_value = get_storage_type_value()
        logging.info(
            f"Queued storage stem separation: {request.storage_path} (task: {task_id}, storage: {storage_type_value})"
        )

        return StorageStemSeparationResponse(
            task_id=task_id,
            status="processing",
            message=f"Audio stem separation started from {storage_type_value} storage",
            model_used=request.model_name,
            storage_stems_paths=None,
            public_urls=None,
            storage_type=storage_type_value,
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error processing storage stem separation: {e}")
        handle_route_error(e, "storage stem separation")


@router.get("/file-info/{storage_path:path}", response_model=StorageFileInfo)
def get_storage_file_info(
    storage_path: str,
    storage: StorageService = Depends(get_storage_service),
    validator: StorageValidator = Depends(),
):
    """Get information about a file in configured storage"""
    try:
        # Use validator to get file info (includes existence check)
        file_info = validator.get_file_info(storage_path)
        public_url = storage.get_public_url(storage_path)

        # Convert timestamp for consistency
        import datetime

        if "last_modified" in file_info:
            if isinstance(file_info["last_modified"], float):
                # Convert Unix timestamp to ISO format
                file_info["last_modified"] = datetime.datetime.fromtimestamp(
                    file_info["last_modified"]
                ).isoformat()

        return StorageFileInfo(
            storage_path=storage_path,
            size=file_info["size"],
            last_modified=file_info["last_modified"],
            content_type=file_info["content_type"],
            metadata=file_info["metadata"],
            public_url=public_url,
            storage_type=get_storage_type_value(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting storage file info: {e}")
        handle_route_error(e, "getting storage file info")


@router.get("/list-files")
def list_storage_files(
    prefix: str = "",
    max_keys: int = 100,
    storage: StorageService = Depends(get_storage_service),
):
    """List files in configured storage with optional prefix filter"""
    try:
        files = storage.list_files(prefix=prefix, max_keys=min(max_keys, 1000))

        # Add public URLs if available
        for file_info in files:
            public_url = storage.get_public_url(file_info["key"])
            if public_url:
                file_info["public_url"] = public_url

        return {
            "files": files,
            "count": len(files),
            "prefix": prefix,
            "truncated": len(files) == max_keys,
            "storage_type": get_storage_type_value(),
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error listing storage files: {e}")
        handle_route_error(e, "listing storage files")


@router.delete("/file/{storage_path:path}")
def delete_storage_file(
    storage_path: str,
    storage: StorageService = Depends(get_storage_service),
    validator: StorageValidator = Depends(),
):
    """Delete a file from configured storage"""
    try:
        # Validate file existence
        validator.validate_file_exists(storage_path)

        storage_type_value = get_storage_type_value()

        if storage.delete_file(storage_path):
            return {
                "message": f"File deleted successfully from {storage_type_value} storage: {storage_path}",
                "status": "deleted",
                "storage_type": storage_type_value,
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to delete file from {storage_type_value} storage",
            )

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error deleting storage file: {e}")
        handle_route_error(e, "deleting storage file")


@router.post("/batch-process")
def batch_process_storage(
    request: StorageBatchProcessingRequest,
    background_tasks: BackgroundTasks,
    storage: StorageService = Depends(get_storage_service),
):
    """Process multiple files from configured storage in batch"""
    try:
        storage_type_value = get_storage_type_value()

        # Verify all files exist
        missing_files = []
        for storage_path in request.storage_paths:
            if not storage.file_exists(storage_path):
                missing_files.append(storage_path)

        if missing_files:
            raise HTTPException(
                status_code=404,
                detail=f"Files not found in {storage_type_value} storage: {', '.join(missing_files)}",
            )

        # Generate batch task ID
        batch_id = generate_task_id()

        # Queue batch processing task
        celery_task = batch_process_from_storage.delay(
            storage_paths=request.storage_paths,
            processing_type=request.processing_type,
            model_name=request.model_name,
            callback_url=request.callback_url,
            batch_metadata={
                **request.batch_metadata,
                "batch_id": batch_id,
                "storage_type": storage_type_value,
            },
        )

        logging.info(
            f"Queued batch storage processing: {len(request.storage_paths)} files (batch: {batch_id}, storage: {storage_type_value})"
        )

        return {
            "batch_id": batch_id,
            "task_id": celery_task.id,
            "status": "processing",
            "message": f"Batch processing started for {len(request.storage_paths)} files from {storage_type_value} storage",
            "processing_type": request.processing_type,
            "file_count": len(request.storage_paths),
            "storage_type": storage_type_value,
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in batch storage processing: {e}")
        handle_route_error(e, "batch storage processing")
