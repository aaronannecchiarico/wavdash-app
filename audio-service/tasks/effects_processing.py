"""
Effects Processing Tasks
Handles advanced audio effects processing with custom effect chains using Celery
"""

import os
import tempfile
import logging
import time
import requests
from typing import Dict, Any, List, Optional
import numpy as np
from celery import current_task
from pathlib import Path

from celery_app import celery_app
from config import settings
from utils.audio_utils import save_audio_file, load_audio_from_bytes
from services.storage_service import get_storage_service, get_storage_type, StorageError
from services.effects_processor import get_effects_processor
from models.effects_models import EffectsConfiguration, EffectsProcessingResult
from models.storage_models import StorageCallbackData

# Import stem separation functionality from existing tasks
try:
    from demucs import pretrained
    from demucs.apply import apply_model
    import torch
    DEMUCS_AVAILABLE = True
except ImportError:
    DEMUCS_AVAILABLE = False

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name='tasks.effects_processing.process_audio_with_effects', queue='audio_features')
def process_audio_with_effects(
    self,
    task_id: str,
    storage_path: str,
    effects_config: dict,
    callback_url: Optional[str] = None,
    user_id: Optional[str] = None,
    output_format: str = "wav",
    separate_stems: bool = True
) -> Dict[str, Any]:
    """
    Process audio file with custom effects chains for individual stems
    
    Args:
        self: Celery task instance
        task_id: Unique task identifier
        storage_path: Path to audio file in storage
        effects_config: Effects configuration dictionary
        callback_url: Optional callback URL for completion notification
        user_id: Optional user ID for file organization
        output_format: Output format (wav, mp3, flac)
        separate_stems: Whether to perform stem separation
        
    Returns:
        Dictionary with processing results
    """
    start_time = time.time()
    temp_file_path = None
    temp_stems_files = {}
    storage = None
    
    try:
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 0, 'status': 'Initializing effects processing', 'task_id': task_id}
        )
        
        storage = get_storage_service()
        storage_type = get_storage_type()
        
        # Verify file exists in storage
        if not storage.file_exists(storage_path):
            raise FileNotFoundError(f"File not found in storage: {storage_path}")
        
        # Parse and validate effects configuration
        config = EffectsConfiguration.model_validate(effects_config)
        
        # Validate effects processor availability
        processor = get_effects_processor()
        if not processor.is_available():
            raise RuntimeError("Effects processor not available (pedalboard not installed)")
        
        # Validate the effects configuration
        is_valid, warnings = processor.validate_configuration(config)
        if not is_valid:
            raise ValueError(f"Invalid effects configuration: {'; '.join(warnings)}")
        
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 10, 'status': 'Downloading audio from storage', 'task_id': task_id}
        )
        
        # Download file from storage to temporary location
        file_extension = Path(storage_path).suffix
        with tempfile.NamedTemporaryFile(suffix=file_extension, delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        if not storage.download_file(storage_path, temp_file_path):
            raise StorageError(f"Failed to download file from storage: {storage_path}")
        
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 20, 'status': 'Loading audio file', 'task_id': task_id}
        )
        
        # Load audio file
        try:
            import librosa
            audio_data, sample_rate = librosa.load(temp_file_path, sr=None, mono=False)
            
            # Ensure audio is in the right format
            if audio_data.ndim > 1:
                # Convert stereo to mono for processing
                audio_data = np.mean(audio_data, axis=0)
            
            # Ensure it's float32
            audio_data = audio_data.astype(np.float32)
            
        except Exception as e:
            raise RuntimeError(f"Failed to load audio file: {str(e)}")
        
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 30, 'status': 'Loading or separating stems (with caching)', 'task_id': task_id}
        )
        
        # Use stem caching service for optimized stem handling
        stems = {}
        if separate_stems and any(chain.stem.value != "full_mix" for chain in config.stem_chains):
            try:
                from services.stem_cache_service import get_stem_cache_service
                
                stem_cache = get_stem_cache_service()
                
                # Get cached stems or create new ones
                stems = stem_cache.get_or_create_stems(
                    audio_data=audio_data,
                    sample_rate=sample_rate,
                    storage_path=storage_path,
                    user_id=user_id
                )
                
                if stems:
                    logger.info(f"Stems obtained for task {task_id}: {list(stems.keys())}")
                else:
                    logger.warning(f"Failed to obtain stems for task {task_id}, using full mix")
                    raise Exception("Stem processing failed")
                    
            except Exception as e:
                logger.warning(f"Stem processing failed for task {task_id}: {str(e)}. Using full mix for all stems.")
                # Fall back to using full mix for all stems
                stems = {
                    "vocals": audio_data.copy(),
                    "drums": audio_data.copy(),
                    "bass": audio_data.copy(),
                    "other": audio_data.copy()
                }
        else:
            # Use full mix for all stems
            stems = {
                "vocals": audio_data.copy(),
                "drums": audio_data.copy(), 
                "bass": audio_data.copy(),
                "other": audio_data.copy(),
                "full_mix": audio_data.copy()
            }
        
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 60, 'status': 'Applying effects to stems', 'task_id': task_id}
        )
        
        # Process stems with effects
        try:
            processed_audio = processor.process_stems_with_effects(stems, config, sample_rate)
            
            if processed_audio is None or len(processed_audio) == 0:
                raise RuntimeError("Effects processing returned empty audio")
                
        except Exception as e:
            raise RuntimeError(f"Effects processing failed: {str(e)}")
        
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 80, 'status': 'Saving processed audio', 'task_id': task_id}
        )
        
        # Save processed audio to storage
        try:
            effects_suffix = f"effects_{len(config.stem_chains)}chains"
            if config.preset_name:
                effects_suffix = f"effects_{config.preset_name.lower().replace(' ', '_')}"
            
            output_path = storage.save_processed_audio(
                audio_data=processed_audio,
                sample_rate=sample_rate,
                storage_path=storage_path,
                user_id=user_id,
                suffix=effects_suffix,
                format=output_format
            )
            
        except Exception as e:
            raise StorageError(f"Failed to save processed audio: {str(e)}")
        
        processing_time = time.time() - start_time
        
        # Count effects applied
        total_effects = sum(len(chain.effects) for chain in config.stem_chains)
        total_effects += len(config.master_chain.effects)
        
        # Determine which stems were processed
        stems_processed = [chain.stem.value for chain in config.stem_chains if chain.effects]
        
        # Calculate quality score based on processing
        quality_score = _calculate_quality_score(processing_time, total_effects, warnings)
        
        # Generate public URLs if available
        public_urls = {}
        if output_path:
            public_url = storage.get_public_url(output_path)
            if public_url:
                public_urls['processed'] = public_url
        
        result = {
            'task_id': task_id,
            'status': 'completed',
            'storage_path': storage_path,
            'output_path': output_path,
            'stems_processed': stems_processed,
            'effects_applied': total_effects,
            'processing_time': processing_time,
            'quality_score': quality_score,
            'warnings': warnings,
            'storage_type': storage_type.value,
            'public_urls': public_urls
        }
        
        current_task.update_state(
            state='PROGRESS',
            meta={'progress': 100, 'status': 'Completed', 'task_id': task_id}
        )
        
        # Send callback if provided
        if callback_url:
            try:
                callback_data = StorageCallbackData(
                    task_id=task_id,
                    status="completed",
                    processing_type="effects",
                    storage_paths={"processed": output_path, "original": storage_path},
                    analysis_summary={
                        "effects_applied": total_effects,
                        "stems_processed": stems_processed,
                        "quality_score": quality_score,
                        "preset_name": config.preset_name
                    },
                    processing_time=processing_time,
                    storage_type=storage_type.value
                )
                
                response = requests.post(
                    callback_url,
                    json=callback_data.model_dump(),
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
                logger.info(f"Effects callback sent for task {task_id}: {response.status_code}")
                
            except Exception as callback_error:
                logger.error(f"Failed to send effects callback for task {task_id}: {callback_error}")
        
        logger.info(f"Effects processing completed successfully for task {task_id} in {processing_time:.2f}s")
        return result
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e)
        
        logger.error(f"Error in effects processing task {task_id}: {error_msg}")
        
        current_task.update_state(
            state='FAILURE',
            meta={
                'error': error_msg,
                'status': 'failed',
                'task_id': task_id,
                'storage_path': storage_path,
                'processing_time': processing_time,
                'storage_type': get_storage_type().value
            }
        )
        
        # Send failure callback if provided
        if callback_url:
            try:
                callback_data = StorageCallbackData(
                    task_id=task_id,
                    status="failed",
                    processing_type="effects",
                    storage_paths={"original": storage_path},
                    error_message=error_msg,
                    processing_time=processing_time,
                    storage_type=get_storage_type().value
                )
                
                requests.post(
                    callback_url,
                    json=callback_data.model_dump(),
                    headers={'Content-Type': 'application/json'},
                    timeout=30
                )
                
            except Exception as callback_error:
                logger.error(f"Failed to send effects failure callback for task {task_id}: {callback_error}")
        
        raise
    
    finally:
        # Cleanup temporary files
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as cleanup_error:
                logger.warning(f"Failed to cleanup temp file {temp_file_path}: {cleanup_error}")
        
        # Cleanup any temporary stem files
        for stem_path in temp_stems_files.values():
            if stem_path and os.path.exists(stem_path):
                try:
                    os.unlink(stem_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to cleanup temp stem file {stem_path}: {cleanup_error}")


def _separate_stems(audio_data: np.ndarray, sample_rate: int) -> Dict[str, np.ndarray]:
    """
    Separate audio into stems using Demucs model
    
    Args:
        audio_data: Input audio data
        sample_rate: Audio sample rate
        
    Returns:
        Dictionary of stem name -> audio data
    """
    if not DEMUCS_AVAILABLE:
        raise RuntimeError("Demucs not available for stem separation")
    
    try:
        # Load the Demucs model (htdemucs is the default high-quality model)
        model = pretrained.get_model("htdemucs")
        model.eval()
        
        # Ensure audio is in the right format for Demucs (stereo)
        if audio_data.ndim == 1:
            # Convert mono to stereo
            audio_stereo = np.stack([audio_data, audio_data], axis=0)
        else:
            audio_stereo = audio_data
        
        # Convert to torch tensor
        audio_tensor = torch.tensor(audio_stereo, dtype=torch.float32).unsqueeze(0)
        
        # Apply the model
        with torch.no_grad():
            sources = apply_model(model, audio_tensor)
        
        # Extract stems - htdemucs returns [drums, bass, other, vocals]
        stems = {}
        stem_names = ["drums", "bass", "other", "vocals"]
        
        for i, stem_name in enumerate(stem_names):
            stem_audio = sources[0][i].numpy()
            # Convert stereo to mono by averaging channels
            if stem_audio.shape[0] > 1:
                stem_audio = np.mean(stem_audio, axis=0)
            else:
                stem_audio = stem_audio[0]
            
            stems[stem_name] = stem_audio.astype(np.float32)
        
        logger.info(f"Stem separation completed: {list(stems.keys())}")
        return stems
        
    except Exception as e:
        logger.error(f"Stem separation failed: {str(e)}")
        raise RuntimeError(f"Stem separation failed: {str(e)}")


def _calculate_quality_score(processing_time: float, effects_count: int, warnings: List[str]) -> float:
    """
    Calculate a quality score for the effects processing
    
    Args:
        processing_time: Time taken for processing
        effects_count: Number of effects applied
        warnings: List of warnings from configuration validation
        
    Returns:
        Quality score between 0.0 and 1.0
    """
    base_score = 1.0
    
    # Penalize for warnings
    warning_penalty = len(warnings) * 0.1
    base_score -= warning_penalty
    
    # Penalize for very long processing times (relative to effect count)
    expected_time = 10 + (effects_count * 5)  # Base time + time per effect
    if processing_time > expected_time * 2:
        time_penalty = min(0.3, (processing_time - expected_time) / expected_time * 0.2)
        base_score -= time_penalty
    
    # Ensure score is between 0.0 and 1.0
    return max(0.0, min(1.0, base_score))