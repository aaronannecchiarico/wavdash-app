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



