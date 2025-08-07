from fastapi import FastAPI, HTTPException, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from contextlib import asynccontextmanager

from config import settings
from models.audio_models import AudioProcessingRequest, AudioProcessingResponse
from tasks.audio_processing import process_audio_features, separate_audio_stems
from celery_app import celery_app


@asynccontextmanager
async def lifespan(app: FastAPI):
    logging.info("Starting audio processing microservice")
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


@app.get("/")
async def root():
    return {"message": "Audio Processing Microservice", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    from utils.device_utils import get_device_info, get_memory_usage
    
    device_info = get_device_info()
    memory_usage = get_memory_usage()
    redis_status = celery_app.control.ping()
    
    return {
        "status": "healthy", 
        "redis_connected": redis_status,
        "device_info": device_info,
        "memory_usage": memory_usage
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


@app.get("/task-status/{task_id}")
async def get_task_status(task_id: str, include_result: bool = False):
    """
    Get task status. Use include_result=true to get full results (may be large).
    """
    try:
        task = celery_app.AsyncResult(task_id)
        
        # Safely get task state
        try:
            state = task.state
        except (ValueError, KeyError) as e:
            logging.error(f"Error getting task state for {task_id}: {e}")
            return {"task_id": task_id, "status": "error", "error": "Task state corrupted or invalid"}
        
        if state == 'PENDING':
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


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )