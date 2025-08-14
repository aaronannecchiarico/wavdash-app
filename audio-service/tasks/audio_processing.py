import os
import tempfile
import logging
import time
import requests
from typing import Dict, Any, List, Optional
import numpy as np
import librosa
from celery import current_task
from demucs import pretrained
from demucs.apply import apply_model
import torch
import io
from pathlib import Path

from celery_app import celery_app
from config import settings
from utils.audio_utils import save_audio_file, load_audio_from_bytes
from utils.feature_extraction import extract_all_features
from services.audio_feature_extraction import create_feature_extractor
from services.r2_storage import get_r2_storage, is_r2_enabled, R2StorageError
from models.r2_models import R2CallbackData


@celery_app.task(bind=True, name='tasks.audio_processing.process_audio_features')
def process_audio_features(self, audio_data: bytes, filename: str) -> Dict[str, Any]:
    """
    Extract audio features using the new feature extraction service
    """
    try:
        import sys
        import os
        
        # Add project root to path if not already there
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        
        from services.audio_feature_extraction import create_feature_extractor
        from io import BytesIO
        
        current_task.update_state(state='PROGRESS', meta={'progress': 0, 'status': 'Initializing feature extractor'})
        
        # Create feature extractor
        extractor = create_feature_extractor(
            extract_detailed=False,  # Optimized for API consumption
            chunk_duration=30.0,
            timeout=300
        )
        
        current_task.update_state(state='PROGRESS', meta={'progress': 10, 'status': 'Loading audio data'})
        
        # Convert bytes to BytesIO
        audio_buffer = BytesIO(audio_data)
        
        current_task.update_state(state='PROGRESS', meta={'progress': 20, 'status': 'Extracting features'})
        
        # Extract features using the new service
        result = extractor.extract_features(
            source=audio_buffer,
            sr=settings.SAMPLE_RATE
        )
        
        # Update filename in metadata
        if 'metadata' in result:
            result['metadata']['filename'] = filename
        
        current_task.update_state(state='PROGRESS', meta={'progress': 90, 'status': 'Finalizing results'})
        
        # Add task completion status
        result['status'] = 'completed'
        result['task_id'] = self.request.id
        
        current_task.update_state(state='PROGRESS', meta={'progress': 100, 'status': 'Completed'})
        
        logging.info(f"Feature extraction completed for {filename}")
        return result
        
    except Exception as e:
        logging.error(f"Error in feature extraction task: {str(e)}")
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': 'failed', 'filename': filename}
        )
        raise


@celery_app.task(bind=True, name='tasks.audio_processing.separate_audio_stems')
def separate_audio_stems(self, audio_data: bytes, filename: str, model_name: str = "htdemucs") -> Dict[str, Any]:
    """
    Separate audio stems using Demucs with MPS compatibility fixes
    """
    try:
        current_task.update_state(state='PROGRESS', meta={'progress': 0, 'status': 'Loading audio'})
        
        # Load audio from bytes - keep stereo for Demucs
        y, sr = load_audio_from_bytes(audio_data, sr=44100, mono=False)  # Demucs needs stereo
        
        current_task.update_state(state='PROGRESS', meta={'progress': 10, 'status': 'Loading model'})
        
        # Force CPU for Celery workers to avoid MPS multiprocessing issues
        import os
        os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"
        
        # Load Demucs model - force CPU for Celery workers
        model = pretrained.get_model(model_name)
        
        # Always use CPU for Celery workers to avoid MPS crashes
        device = torch.device("cpu")
        model = model.to(device)
        model.eval()
        
        logging.info(f"Using device: {device} for stem separation in Celery worker")
        
        current_task.update_state(state='PROGRESS', meta={'progress': 30, 'status': 'Processing stems'})
        
        # Convert to torch tensor and ensure stereo format for Demucs
        if len(y.shape) == 1:
            # Convert mono to stereo by duplicating the channel
            y_stereo = np.stack([y, y])  # Shape: [2, samples]
            y_stereo = y_stereo[None, :]  # Add batch dimension: [1, 2, samples]
        else:
            # Already stereo, just add batch dimension
            if y.shape[0] > y.shape[1]:  # If samples x channels, transpose
                y = y.T
            y_stereo = y[None, :]  # Add batch dimension: [1, channels, samples]
            
        # Ensure exactly 2 channels for Demucs
        if y_stereo.shape[1] == 1:
            # Duplicate mono to stereo
            y_stereo = np.repeat(y_stereo, 2, axis=1)
        elif y_stereo.shape[1] > 2:
            # Take only first 2 channels if more than stereo
            y_stereo = y_stereo[:, :2, :]
            
        audio_tensor = torch.from_numpy(y_stereo).float().to(device)
        logging.info(f"Audio tensor shape for Demucs: {audio_tensor.shape}")
        
        # Apply model with CPU processing
        with torch.no_grad():
            # Use CPU to avoid MPS multiprocessing crashes
            sources = apply_model(model, audio_tensor, device=device, progress=False)[0]
        
        current_task.update_state(state='PROGRESS', meta={'progress': 80, 'status': 'Saving stems'})
        
        # Convert back to numpy and save stems
        stems = {}
        stem_names = model.sources
        
        for i, stem_name in enumerate(stem_names):
            stem_audio = sources[i].cpu().numpy()
            # Save to temporary files and return file paths or base64 encoded data
            with tempfile.NamedTemporaryFile(suffix=f'_{stem_name}.wav', delete=False) as tmp:
                # Convert to mono if stereo
                if len(stem_audio.shape) > 1:
                    stem_audio = librosa.to_mono(stem_audio)
                
                # Use soundfile instead of deprecated write_wav
                import soundfile as sf
                sf.write(tmp.name, stem_audio, sr)
                stems[stem_name] = tmp.name
        
        current_task.update_state(state='PROGRESS', meta={'progress': 100, 'status': 'Completed'})
        
        result = {
            'filename': filename,
            'model_used': model_name,
            'sample_rate': sr,
            'stems': stems,
            'stem_count': len(stems),
            'status': 'completed'
        }
        
        return result
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"Error in stem separation task: {error_msg}")
        
        # Handle the exception properly for Celery serialization
        try:
            current_task.update_state(
                state='FAILURE',
                meta={
                    'error': error_msg, 
                    'status': 'failed',
                    'filename': filename,
                    'model_name': model_name,
                    'exc_type': type(e).__name__,
                    'exc_module': type(e).__module__
                }
            )
        except Exception as update_error:
            logging.error(f"Failed to update task state: {update_error}")
        
        # Create a simple exception for better serialization
        simple_error = RuntimeError(f"Stem separation failed: {error_msg}")
        raise simple_error


@celery_app.task(bind=True, name='tasks.audio_processing.batch_process_features')
def batch_process_features(self, audio_files: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Process multiple audio files for feature extraction
    """
    try:
        results = []
        total_files = len(audio_files)
        
        for i, file_data in enumerate(audio_files):
            current_task.update_state(
                state='PROGRESS', 
                meta={'progress': (i / total_files) * 100, 'status': f'Processing file {i+1}/{total_files}'}
            )
            
            # Process individual file
            result = process_audio_features.apply_async(
                args=[file_data['data'], file_data['filename']]
            ).get()
            
            results.append(result)
        
        current_task.update_state(state='PROGRESS', meta={'progress': 100, 'status': 'Completed'})
        
        return {
            'processed_count': len(results),
            'results': results,
            'status': 'completed'
        }
        
    except Exception as e:
        logging.error(f"Error in batch processing task: {str(e)}")
        current_task.update_state(
            state='FAILURE',
            meta={'error': str(e), 'status': 'failed'}
        )
        raise


# ====================================
# R2 Storage Integration Tasks
# ====================================

@celery_app.task(bind=True, name='tasks.audio_processing.process_audio_features_r2')
def process_audio_features_r2(self, task_id: str, r2_path: str, extract_detailed: bool = False, 
                             callback_url: Optional[str] = None, metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Process audio features from R2 storage with callback support
    """
    start_time = time.time()
    temp_file_path = None
    
    try:
        if not is_r2_enabled():
            raise R2StorageError("R2 storage is not enabled")
        
        current_task.update_state(state='PROGRESS', meta={'progress': 0, 'status': 'Initializing R2 connection', 'task_id': task_id})
        
        r2_storage = get_r2_storage()
        
        # Verify file exists in R2
        if not r2_storage.file_exists(r2_path):
            raise FileNotFoundError(f"File not found in R2: {r2_path}")
        
        current_task.update_state(state='PROGRESS', meta={'progress': 10, 'status': 'Downloading file from R2', 'task_id': task_id})
        
        # Download file from R2 to temporary location
        file_extension = Path(r2_path).suffix
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        if not r2_storage.download_file(r2_path, temp_file_path):
            raise R2StorageError(f"Failed to download file from R2: {r2_path}")
        
        current_task.update_state(state='PROGRESS', meta={'progress': 30, 'status': 'Extracting audio features', 'task_id': task_id})
        
        # Extract features using the enhanced service
        extractor = create_feature_extractor(
            extract_detailed=extract_detailed,
            timeout=settings.TASK_TIME_LIMIT
        )
        
        feature_result = extractor.extract_features(temp_file_path)
        
        # Check for extraction errors
        if 'error' in feature_result:
            raise Exception(f"Feature extraction failed: {feature_result['error']}")
        
        current_task.update_state(state='PROGRESS', meta={'progress': 80, 'status': 'Uploading results to R2', 'task_id': task_id})
        
        # Upload analysis results to R2
        base_path = Path(r2_path).stem
        analysis_type = "detailed" if extract_detailed else "features"
        r2_analysis_path = r2_storage.upload_analysis_result(feature_result, base_path, analysis_type, None)
        
        processing_time = time.time() - start_time
        
        # Prepare summary for callback
        musical_analysis = None
        if 'features' in feature_result:
            features = feature_result['features']
            musical_analysis = {
                'bpm': features.get('tempo', {}).get('bpm', 0),
                'key': features.get('key', {}).get('key', 'unknown'),
                'key_confidence': features.get('key', {}).get('confidence', 0),
                'loudness_db': features.get('energy', {}).get('overall_loudness_db', 0),
                'brightness': features.get('spectral', {}).get('spectral_centroid', {}).get('mean', 0),
                'duration': feature_result.get('metadata', {}).get('duration', 0)
            }
        
        result = {
            'task_id': task_id,
            'status': 'completed',
            'r2_path': r2_path,
            'r2_analysis_path': r2_analysis_path,
            'processing_time': processing_time,
            'analysis_summary': musical_analysis,
            'metadata': metadata or {}
        }
        
        current_task.update_state(state='PROGRESS', meta={'progress': 100, 'status': 'Completed', 'task_id': task_id})
        
        # Send callback if provided
        if callback_url:
            try:
                callback_data = R2CallbackData(
                    task_id=task_id,
                    status="completed",
                    processing_type="features",
                    r2_paths={"analysis": r2_analysis_path, "original": r2_path},
                    analysis_summary=musical_analysis,
                    processing_time=processing_time
                )
                
                response = requests.post(
                    callback_url,
                    json=callback_data.model_dump(),
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                logging.info(f"Callback sent for task {task_id}: {response.status_code}")
                
            except Exception as callback_error:
                logging.error(f"Failed to send callback for task {task_id}: {callback_error}")
        
        return result
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e)
        
        logging.error(f"Error in R2 feature extraction task {task_id}: {error_msg}")
        
        current_task.update_state(
            state='FAILURE',
            meta={
                'error': error_msg,
                'status': 'failed',
                'task_id': task_id,
                'r2_path': r2_path,
                'processing_time': processing_time
            }
        )
        
        # Send failure callback if provided
        if callback_url:
            try:
                callback_data = R2CallbackData(
                    task_id=task_id,
                    status="failed",
                    processing_type="features",
                    r2_paths={"original": r2_path},
                    error_message=error_msg,
                    processing_time=processing_time
                )
                
                requests.post(
                    callback_url,
                    json=callback_data.model_dump(),
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
            except Exception as callback_error:
                logging.error(f"Failed to send failure callback for task {task_id}: {callback_error}")
        
        raise
    
    finally:
        # Cleanup temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as cleanup_error:
                logging.warning(f"Failed to cleanup temp file {temp_file_path}: {cleanup_error}")


@celery_app.task(bind=True, name='tasks.audio_processing.separate_audio_stems_r2')
def separate_audio_stems_r2(self, task_id: str, r2_path: str, model_name: str = "htdemucs",
                           callback_url: Optional[str] = None, metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """
    Separate audio stems from R2 storage with callback support
    """
    start_time = time.time()
    temp_input_path = None
    temp_output_dir = None
    
    try:
        if not is_r2_enabled():
            raise R2StorageError("R2 storage is not enabled")
        
        current_task.update_state(state='PROGRESS', meta={'progress': 0, 'status': 'Initializing R2 connection', 'task_id': task_id})
        
        r2_storage = get_r2_storage()
        
        # Verify file exists in R2
        if not r2_storage.file_exists(r2_path):
            raise FileNotFoundError(f"File not found in R2: {r2_path}")
        
        current_task.update_state(state='PROGRESS', meta={'progress': 10, 'status': 'Downloading file from R2', 'task_id': task_id})
        
        # Download file from R2 to temporary location
        file_extension = Path(r2_path).suffix
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            temp_input_path = temp_file.name
        
        if not r2_storage.download_file(r2_path, temp_input_path):
            raise R2StorageError(f"Failed to download file from R2: {r2_path}")
        
        current_task.update_state(state='PROGRESS', meta={'progress': 20, 'status': 'Loading audio and model', 'task_id': task_id})
        
        # Load audio - Demucs needs stereo at 44.1kHz
        y, sr = load_audio_from_bytes(open(temp_input_path, 'rb').read(), sr=44100, mono=False)
        
        # Force CPU processing for MPS compatibility
        device = "cpu"
        logging.info(f"Using device: {device} for stem separation (R2 task)")
        
        # Load Demucs model
        model = pretrained.get_model(model_name).to(device)
        model.eval()
        
        current_task.update_state(state='PROGRESS', meta={'progress': 30, 'status': 'Separating audio stems', 'task_id': task_id})
        
        # Convert to tensor and add batch dimension
        if len(y.shape) == 1:  # Mono to stereo conversion
            y = np.stack([y, y])
        
        audio_tensor = torch.from_numpy(y).float().unsqueeze(0).to(device)
        
        # Separate stems
        with torch.no_grad():
            separated = apply_model(model, audio_tensor, device=device, progress=True)
        
        # Process each stem
        stem_names = model.sources
        stems_paths = {}
        temp_output_dir = tempfile.mkdtemp()
        
        current_task.update_state(state='PROGRESS', meta={'progress': 70, 'status': 'Saving separated stems', 'task_id': task_id})
        
        for i, stem_name in enumerate(stem_names):
            stem_audio = separated[0, i].cpu().numpy()
            
            # Convert to mono if needed and save
            if stem_audio.shape[0] == 2:  # Stereo to mono
                stem_audio = np.mean(stem_audio, axis=0)
            
            # Save temporary stem file
            temp_stem_path = os.path.join(temp_output_dir, f"{stem_name}.wav")
            save_audio_file(stem_audio, sr, temp_stem_path)
            stems_paths[stem_name] = temp_stem_path
        
        current_task.update_state(state='PROGRESS', meta={'progress': 85, 'status': 'Uploading stems to R2', 'task_id': task_id})
        
        # Upload stems to R2
        base_path = Path(r2_path).stem
        uploaded_stems = r2_storage.upload_stems(stems_paths, base_path, metadata, None)
        
        processing_time = time.time() - start_time
        
        # Generate public URLs if available
        public_urls = {}
        if r2_storage.public_url:
            for stem_name, r2_stem_path in uploaded_stems.items():
                public_urls[stem_name] = r2_storage.get_public_url(r2_stem_path)
        
        result = {
            'task_id': task_id,
            'status': 'completed',
            'r2_path': r2_path,
            'r2_stems_paths': uploaded_stems,
            'public_urls': public_urls,
            'model_used': model_name,
            'processing_time': processing_time,
            'metadata': metadata or {}
        }
        
        current_task.update_state(state='PROGRESS', meta={'progress': 100, 'status': 'Completed', 'task_id': task_id})
        
        # Send callback if provided
        if callback_url:
            try:
                callback_data = R2CallbackData(
                    task_id=task_id,
                    status="completed",
                    processing_type="stems",
                    r2_paths={**uploaded_stems, "original": r2_path},
                    processing_time=processing_time
                )
                
                response = requests.post(
                    callback_url,
                    json=callback_data.model_dump(),
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                logging.info(f"Callback sent for stem task {task_id}: {response.status_code}")
                
            except Exception as callback_error:
                logging.error(f"Failed to send callback for stem task {task_id}: {callback_error}")
        
        return result
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e)
        
        logging.error(f"Error in R2 stem separation task {task_id}: {error_msg}")
        
        current_task.update_state(
            state='FAILURE',
            meta={
                'error': error_msg,
                'status': 'failed',
                'task_id': task_id,
                'r2_path': r2_path,
                'processing_time': processing_time
            }
        )
        
        # Send failure callback if provided
        if callback_url:
            try:
                callback_data = R2CallbackData(
                    task_id=task_id,
                    status="failed",
                    processing_type="stems",
                    r2_paths={"original": r2_path},
                    error_message=error_msg,
                    processing_time=processing_time
                )
                
                requests.post(
                    callback_url,
                    json=callback_data.model_dump(),
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
            except Exception as callback_error:
                logging.error(f"Failed to send failure callback for stem task {task_id}: {callback_error}")
        
        raise
    
    finally:
        # Cleanup temporary files
        if temp_input_path and os.path.exists(temp_input_path):
            try:
                os.unlink(temp_input_path)
            except Exception as cleanup_error:
                logging.warning(f"Failed to cleanup temp input file {temp_input_path}: {cleanup_error}")
        
        if temp_output_dir and os.path.exists(temp_output_dir):
            try:
                import shutil
                shutil.rmtree(temp_output_dir)
            except Exception as cleanup_error:
                logging.warning(f"Failed to cleanup temp output dir {temp_output_dir}: {cleanup_error}")