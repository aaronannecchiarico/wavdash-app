"""
Unified Storage Processing Tasks
Works with both local and R2 storage
"""

import logging
import os
from pathlib import Path
import tempfile
import time
from typing import Any, Dict, List, Optional

from celery import current_task
from demucs import pretrained
from demucs.apply import apply_model
import numpy as np
import requests
import torch

from celery_app import celery_app
from config import settings
from models.storage_models import StorageCallbackData
from services.audio_feature_extraction import create_feature_extractor
from services.storage_service import (
    StorageError,
    StorageType,
    get_storage_service,
    get_storage_type,
)
from utils.audio_utils import load_audio_from_bytes, save_audio_file

logger = logging.getLogger(__name__)


@celery_app.task(
    bind=True,
    name="tasks.storage_processing.process_audio_features_from_storage",
    queue="audio_features",
)
def process_audio_features_from_storage(
    self,
    task_id: str,
    storage_path: str,
    extract_detailed: bool = False,
    callback_url: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Extract audio features from storage (local or R2) with callback support
    """
    start_time = time.time()
    temp_file_path = None
    storage = None

    try:
        current_task.update_state(
            state="PROGRESS",
            meta={
                "progress": 0,
                "status": "Initializing storage connection",
                "task_id": task_id,
            },
        )

        storage = get_storage_service()
        storage_type = get_storage_type()

        # Verify file exists in storage
        if not storage.file_exists(storage_path):
            raise FileNotFoundError(f"File not found in storage: {storage_path}")

        current_task.update_state(
            state="PROGRESS",
            meta={
                "progress": 10,
                "status": "Downloading file from storage",
                "task_id": task_id,
            },
        )

        # Download file from storage to temporary location
        file_extension = Path(storage_path).suffix
        with tempfile.NamedTemporaryFile(
            suffix=file_extension, delete=False
        ) as temp_file:
            temp_file_path = temp_file.name

        if not storage.download_file(storage_path, temp_file_path):
            raise StorageError(f"Failed to download file from storage: {storage_path}")

        current_task.update_state(
            state="PROGRESS",
            meta={
                "progress": 30,
                "status": "Extracting audio features",
                "task_id": task_id,
            },
        )

        # Extract features using the enhanced service
        extractor = create_feature_extractor(
            extract_detailed=extract_detailed, timeout=settings.TASK_TIME_LIMIT
        )

        feature_result = extractor.extract_features(temp_file_path)

        # Check for extraction errors
        if "error" in feature_result:
            raise Exception(f"Feature extraction failed: {feature_result['error']}")

        current_task.update_state(
            state="PROGRESS",
            meta={
                "progress": 80,
                "status": "Uploading results to storage",
                "task_id": task_id,
            },
        )

        # Upload analysis results to storage
        base_path = Path(storage_path).stem
        analysis_type = "detailed" if extract_detailed else "features"

        # Extract user_id from metadata
        user_id = None
        if metadata and "user_id" in metadata:
            user_id = str(metadata["user_id"])

        storage_analysis_path = storage.upload_analysis_result(
            feature_result, base_path, analysis_type, user_id
        )

        processing_time = time.time() - start_time

        # Prepare summary for callback
        musical_analysis = None

        # Handle both single-chunk and multi-chunk processing
        features = None
        if "features" in feature_result:
            # Single chunk processing
            features = feature_result["features"]
            logger.debug("Using single-chunk features")
        elif "aggregated_features" in feature_result:
            # Multi-chunk processing
            features = feature_result["aggregated_features"]
            logger.debug(
                f"Using aggregated features from {feature_result.get('chunk_count', 0)} chunks"
            )

        if features:
            # Handle different data structures for single vs chunked processing
            bpm = features.get("tempo", {}).get("bpm", 0) or features.get(
                "tempo", {}
            ).get("mean_bpm", 0)

            key = features.get("key", {}).get("key") or features.get("key", {}).get(
                "most_likely_key", "unknown"
            )

            key_confidence = features.get("key", {}).get("confidence", 0)

            loudness_db = features.get("energy", {}).get(
                "overall_loudness_db", 0
            ) or features.get("energy", {}).get("mean_loudness_db", 0)

            brightness = features.get("spectral", {}).get("spectral_centroid", {}).get(
                "mean", 0
            ) or features.get("spectral", {}).get("mean_brightness", 0)

            musical_analysis = {
                "bpm": float(bpm) if bpm else 0.0,
                "key": str(key) if key != "unknown" else "unknown",
                "key_confidence": float(key_confidence) if key_confidence else 0.0,
                "loudness_db": float(loudness_db) if loudness_db else 0.0,
                "brightness": float(brightness) if brightness else 0.0,
                "duration": float(
                    feature_result.get("metadata", {}).get("duration", 0)
                ),
            }
            logger.info(
                f"Generated musical analysis: BPM={musical_analysis['bpm']:.1f}, "
                f"Key={musical_analysis['key']}, "
                f"Duration={musical_analysis['duration']:.1f}s"
            )
        else:
            logger.warning(
                f"No 'features' or 'aggregated_features' key in feature_result. Available keys: {list(feature_result.keys())}"
            )

        # Generate public URLs if available
        public_urls = {}
        if storage_analysis_path:
            public_url = storage.get_public_url(storage_analysis_path)
            if public_url:
                public_urls["analysis"] = public_url

        result = {
            "task_id": task_id,
            "status": "completed",
            "storage_path": storage_path,
            "storage_analysis_path": storage_analysis_path,
            "processing_time": processing_time,
            "analysis_summary": musical_analysis,
            "metadata": metadata or {},
            "storage_type": storage_type.value,
            "public_urls": public_urls,
        }

        current_task.update_state(
            state="PROGRESS",
            meta={"progress": 100, "status": "Completed", "task_id": task_id},
        )

        # Send callback if provided
        if callback_url:
            try:
                callback_data = StorageCallbackData(
                    task_id=task_id,
                    status="completed",
                    processing_type="features",
                    storage_paths={
                        "analysis": storage_analysis_path,
                        "original": storage_path,
                    },
                    analysis_summary=musical_analysis,
                    processing_time=processing_time,
                    storage_type=storage_type.value,
                )

                response = requests.post(
                    callback_url,
                    json=callback_data.model_dump(),
                    headers={"Content-Type": "application/json"},
                    timeout=30,
                )

                logger.info(f"Callback sent for task {task_id}: {response.status_code}")

            except Exception as callback_error:
                logger.error(
                    f"Failed to send callback for task {task_id}: {callback_error}"
                )

        return result

    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e)

        logger.error(f"Error in storage feature extraction task {task_id}: {error_msg}")

        current_task.update_state(
            state="FAILURE",
            meta={
                "error": error_msg,
                "status": "failed",
                "task_id": task_id,
                "storage_path": storage_path,
                "processing_time": processing_time,
                "storage_type": get_storage_type().value,
            },
        )

        # Send failure callback if provided
        if callback_url:
            try:
                callback_data = StorageCallbackData(
                    task_id=task_id,
                    status="failed",
                    processing_type="features",
                    storage_paths={"original": storage_path},
                    error_message=error_msg,
                    processing_time=processing_time,
                    storage_type=get_storage_type().value,
                )

                requests.post(
                    callback_url,
                    json=callback_data.model_dump(),
                    headers={"Content-Type": "application/json"},
                    timeout=30,
                )

            except Exception as callback_error:
                logger.error(
                    f"Failed to send failure callback for task {task_id}: {callback_error}"
                )

        raise

    finally:
        # Cleanup temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.unlink(temp_file_path)
            except Exception as cleanup_error:
                logger.warning(
                    f"Failed to cleanup temp file {temp_file_path}: {cleanup_error}"
                )


@celery_app.task(
    bind=True,
    name="tasks.storage_processing.separate_audio_stems_from_storage",
    queue="stem_separation",
)
def separate_audio_stems_from_storage(
    self,
    task_id: str,
    storage_path: str,
    model_name: str = "htdemucs",
    callback_url: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Separate audio stems from storage (local or R2) with callback support
    """
    start_time = time.time()
    temp_input_path = None
    temp_output_dir = None
    storage = None

    try:
        current_task.update_state(
            state="PROGRESS",
            meta={
                "progress": 0,
                "status": "Initializing storage connection",
                "task_id": task_id,
            },
        )

        storage = get_storage_service()
        storage_type = get_storage_type()

        # Verify file exists in storage
        if not storage.file_exists(storage_path):
            raise FileNotFoundError(f"File not found in storage: {storage_path}")

        current_task.update_state(
            state="PROGRESS",
            meta={
                "progress": 10,
                "status": "Downloading file from storage",
                "task_id": task_id,
            },
        )

        # Download file from storage to temporary location
        file_extension = Path(storage_path).suffix
        with tempfile.NamedTemporaryFile(
            suffix=file_extension, delete=False
        ) as temp_file:
            temp_input_path = temp_file.name

        if not storage.download_file(storage_path, temp_input_path):
            raise StorageError(f"Failed to download file from storage: {storage_path}")

        current_task.update_state(
            state="PROGRESS",
            meta={
                "progress": 20,
                "status": "Loading audio and model",
                "task_id": task_id,
            },
        )

        # Load audio - Demucs needs stereo at 44.1kHz
        y, sr = load_audio_from_bytes(
            open(temp_input_path, "rb").read(), sr=44100, mono=False
        )

        # Force CPU processing for MPS compatibility
        device = "cpu"
        logger.info(f"Using device: {device} for stem separation (storage task)")

        # Load Demucs model
        model = pretrained.get_model(model_name).to(device)
        model.eval()

        current_task.update_state(
            state="PROGRESS",
            meta={
                "progress": 30,
                "status": "Separating audio stems",
                "task_id": task_id,
            },
        )

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

        current_task.update_state(
            state="PROGRESS",
            meta={
                "progress": 70,
                "status": "Saving separated stems",
                "task_id": task_id,
            },
        )

        for i, stem_name in enumerate(stem_names):
            stem_audio = separated[0, i].cpu().numpy()

            # Convert to mono if needed and save
            if stem_audio.shape[0] == 2:  # Stereo to mono
                stem_audio = np.mean(stem_audio, axis=0)

            # Save temporary stem file
            temp_stem_path = os.path.join(temp_output_dir, f"{stem_name}.wav")
            save_audio_file(stem_audio, sr, temp_stem_path)
            stems_paths[stem_name] = temp_stem_path

        current_task.update_state(
            state="PROGRESS",
            meta={
                "progress": 85,
                "status": "Uploading stems to storage",
                "task_id": task_id,
            },
        )

        # Upload stems to storage
        base_path = Path(storage_path).stem

        # Extract user_id from metadata
        user_id = None
        if metadata and "user_id" in metadata:
            user_id = str(metadata["user_id"])

        uploaded_stems = storage.upload_stems(stems_paths, base_path, metadata, user_id)

        processing_time = time.time() - start_time

        # Generate public URLs if available
        public_urls = {}
        for stem_name, storage_stem_path in uploaded_stems.items():
            public_url = storage.get_public_url(storage_stem_path)
            if public_url:
                public_urls[stem_name] = public_url

        result = {
            "task_id": task_id,
            "status": "completed",
            "storage_path": storage_path,
            "storage_stems_paths": uploaded_stems,
            "public_urls": public_urls,
            "model_used": model_name,
            "processing_time": processing_time,
            "metadata": metadata or {},
            "storage_type": storage_type.value,
        }

        current_task.update_state(
            state="PROGRESS",
            meta={"progress": 100, "status": "Completed", "task_id": task_id},
        )

        # Send callback if provided
        if callback_url:
            try:
                callback_data = StorageCallbackData(
                    task_id=task_id,
                    status="completed",
                    processing_type="stems",
                    storage_paths={**uploaded_stems, "original": storage_path},
                    model_used=model_name,
                    processing_time=processing_time,
                    storage_type=storage_type.value,
                )

                response = requests.post(
                    callback_url,
                    json=callback_data.model_dump(),
                    headers={"Content-Type": "application/json"},
                    timeout=30,
                )

                logger.info(
                    f"Callback sent for stem task {task_id}: {response.status_code}"
                )

            except Exception as callback_error:
                logger.error(
                    f"Failed to send callback for stem task {task_id}: {callback_error}"
                )

        return result

    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e)

        logger.error(f"Error in storage stem separation task {task_id}: {error_msg}")

        current_task.update_state(
            state="FAILURE",
            meta={
                "error": error_msg,
                "status": "failed",
                "task_id": task_id,
                "storage_path": storage_path,
                "processing_time": processing_time,
                "storage_type": get_storage_type().value,
            },
        )

        # Send failure callback if provided
        if callback_url:
            try:
                callback_data = StorageCallbackData(
                    task_id=task_id,
                    status="failed",
                    processing_type="stems",
                    storage_paths={"original": storage_path},
                    error_message=error_msg,
                    processing_time=processing_time,
                    storage_type=get_storage_type().value,
                )

                requests.post(
                    callback_url,
                    json=callback_data.model_dump(),
                    headers={"Content-Type": "application/json"},
                    timeout=30,
                )

            except Exception as callback_error:
                logger.error(
                    f"Failed to send failure callback for stem task {task_id}: {callback_error}"
                )

        raise

    finally:
        # Cleanup temporary files
        if temp_input_path and os.path.exists(temp_input_path):
            try:
                os.unlink(temp_input_path)
            except Exception as cleanup_error:
                logger.warning(
                    f"Failed to cleanup temp input file {temp_input_path}: {cleanup_error}"
                )

        if temp_output_dir and os.path.exists(temp_output_dir):
            try:
                import shutil

                shutil.rmtree(temp_output_dir)
            except Exception as cleanup_error:
                logger.warning(
                    f"Failed to cleanup temp output dir {temp_output_dir}: {cleanup_error}"
                )


@celery_app.task(
    bind=True,
    name="tasks.storage_processing.batch_process_from_storage",
    queue="audio_features",
)
def batch_process_from_storage(
    self,
    storage_paths: List[str],
    processing_type: str,
    model_name: str = "htdemucs",
    callback_url: Optional[str] = None,
    batch_metadata: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Process multiple files from storage in batch
    """
    try:
        results = []
        total_files = len(storage_paths)

        for i, storage_path in enumerate(storage_paths):
            current_task.update_state(
                state="PROGRESS",
                meta={
                    "progress": (i / total_files) * 100,
                    "status": f"Processing file {i + 1}/{total_files}",
                },
            )

            # Create individual task ID for each file
            individual_task_id = f"{self.request.id}_{i}"

            # Process individual file
            if processing_type == "features":
                result = process_audio_features_from_storage.apply_async(
                    args=[
                        individual_task_id,
                        storage_path,
                        False,
                        callback_url,
                        batch_metadata,
                    ]
                ).get()
            elif processing_type == "stems":
                result = separate_audio_stems_from_storage.apply_async(
                    args=[
                        individual_task_id,
                        storage_path,
                        model_name,
                        callback_url,
                        batch_metadata,
                    ]
                ).get()
            else:
                raise ValueError(f"Invalid processing type: {processing_type}")

            results.append(result)

        current_task.update_state(
            state="PROGRESS", meta={"progress": 100, "status": "Completed"}
        )

        return {
            "processed_count": len(results),
            "results": results,
            "status": "completed",
            "processing_type": processing_type,
            "storage_type": get_storage_type().value,
        }

    except Exception as e:
        logger.error(f"Error in batch processing task: {str(e)}")
        current_task.update_state(
            state="FAILURE", meta={"error": str(e), "status": "failed"}
        )
        raise
