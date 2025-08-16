"""
Audio Processing Routes
Handles direct file upload processing for audio feature extraction and stem separation
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
import logging

from models.audio_models import AudioProcessingRequest, AudioProcessingResponse
from tasks.audio_processing import process_audio_features, separate_audio_stems

router = APIRouter(prefix="/audio", tags=["Audio Processing"])


@router.post("/extract-features", response_model=AudioProcessingResponse)
async def extract_audio_features(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    async_processing: bool = True
):
    """Extract audio features from uploaded file"""
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


@router.post("/separate-stems", response_model=AudioProcessingResponse)
async def separate_stems(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(...),
    model_name: str = "htdemucs",
    async_processing: bool = True
):
    """Separate audio stems from uploaded file"""
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


@router.post("/extract-features-sync")
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
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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