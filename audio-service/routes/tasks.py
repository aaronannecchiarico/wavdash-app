"""
Task Management Routes
Handles task status, results, and task lifecycle management
"""

import logging

from fastapi import APIRouter, HTTPException
import redis

from celery_app import celery_app
from config import settings

router = APIRouter(prefix="/task", tags=["Task Management"])

# Redis connection for tracking deleted tasks
redis_client = None


def get_redis_client():
    """Get Redis client for deleted task tracking"""
    global redis_client
    if redis_client is None:
        try:
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=settings.REDIS_DB,
                password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                decode_responses=True,
            )
            redis_client.ping()  # Test connection
        except Exception as e:
            logging.error(f"Failed to connect to Redis for deleted task tracking: {e}")
            redis_client = None
    return redis_client


def is_task_deleted(task_id: str) -> bool:
    """Check if a task has been marked as deleted"""
    client = get_redis_client()
    if client is None:
        return False
    try:
        return client.exists(f"deleted_task:{task_id}") == 1
    except Exception as e:
        logging.error(f"Error checking deleted task status for {task_id}: {e}")
        return False


@router.get("/status/{task_id}")
def get_task_status(task_id: str, include_result: bool = False):
    """
    Get task status. Use include_result=true to get full results (may be large).
    """
    try:
        # Check if task has been deleted
        if is_task_deleted(task_id):
            return {
                "task_id": task_id,
                "status": "deleted",
                "message": "Task has been deleted",
            }

        task = celery_app.AsyncResult(task_id)

        # Safely get task state
        try:
            state = task.state
        except (ValueError, KeyError) as e:
            logging.error(f"Error getting task state for {task_id}: {e}")
            return {
                "task_id": task_id,
                "status": "error",
                "error": "Task state corrupted or invalid",
            }

        if state == "PENDING":
            # Double-check if task was deleted but state check missed it
            if is_task_deleted(task_id):
                return {
                    "task_id": task_id,
                    "status": "deleted",
                    "message": "Task has been deleted",
                }
            return {
                "task_id": task_id,
                "status": "pending",
                "message": "Task is waiting to be processed",
            }
        elif state == "PROGRESS":
            try:
                progress_info = task.info or {}
                return {
                    "task_id": task_id,
                    "status": "processing",
                    "progress": progress_info.get("progress", 0),
                }
            except Exception:
                return {"task_id": task_id, "status": "processing", "progress": 0}
        elif state == "SUCCESS":
            try:
                result = task.result
                if include_result:
                    return {"task_id": task_id, "status": "completed", "result": result}
                else:
                    # Return summary without full result data
                    result_summary = {"status": "completed", "task_id": task_id}
                    if result and isinstance(result, dict):
                        # Add basic metadata without the large feature arrays
                        if "metadata" in result and isinstance(
                            result["metadata"], dict
                        ):
                            metadata = result["metadata"]
                            result_summary["filename"] = metadata.get(
                                "filename", "unknown"
                            )
                            result_summary["duration"] = metadata.get("duration", 0)
                            result_summary["sample_rate"] = metadata.get(
                                "sample_rate", 0
                            )
                            result_summary["processing_time"] = metadata.get(
                                "processing_time", 0
                            )

                        if "features" in result:
                            features = result["features"]
                            result_summary["features_available"] = (
                                list(features.keys())
                                if isinstance(features, dict)
                                else True
                            )
                        # For stem separation results
                        if "stems" in result:
                            stems = result["stems"]
                            result_summary["stems_available"] = (
                                list(stems.keys()) if isinstance(stems, dict) else True
                            )
                        if "stem_count" in result:
                            result_summary["stem_count"] = result["stem_count"]

                    result_summary["message"] = (
                        "Task completed successfully. Use include_result=true to get full data."
                    )
                    return result_summary
            except Exception as e:
                logging.error(f"Error accessing task result for {task_id}: {e}")
                return {
                    "task_id": task_id,
                    "status": "error",
                    "error": "Task result corrupted or inaccessible",
                }
        elif state == "FAILURE":
            try:
                error_info = task.info or "Unknown error"
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "error": str(error_info),
                }
            except Exception:
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "error": "Task failed with unknown error",
                }
        else:
            return {"task_id": task_id, "status": state}

    except Exception as e:
        logging.error(f"Critical error in get_task_status for {task_id}: {e}")
        return {
            "task_id": task_id,
            "status": "error",
            "error": f"Unable to retrieve task status: {str(e)}",
        }


@router.get("/summary/{task_id}")
def get_task_summary(task_id: str):
    """
    Get a lightweight summary of audio processing results - optimized for Laravel integration.
    Returns only essential metrics without large feature arrays.
    """
    try:
        # Check if task has been deleted
        if is_task_deleted(task_id):
            return {
                "task_id": task_id,
                "status": "deleted",
                "message": "Task has been deleted",
            }

        task = celery_app.AsyncResult(task_id)

        # Safely get task state
        try:
            state = task.state
        except (ValueError, KeyError) as e:
            logging.error(f"Error getting task state for {task_id}: {e}")
            return {
                "task_id": task_id,
                "status": "error",
                "error": "Task state corrupted or invalid",
            }

        if state == "SUCCESS":
            try:
                result = task.result
                if not result or "error" in result:
                    return {
                        "task_id": task_id,
                        "status": "failed",
                        "error": (
                            result.get("error", "Unknown error")
                            if result
                            else "No result data"
                        ),
                    }

                # Extract lightweight summary
                summary = {
                    "task_id": task_id,
                    "status": "completed",
                    "metadata": result.get("metadata", {}),
                }

                # Extract key musical features
                if "features" in result:
                    features = result["features"]
                    summary["musical_analysis"] = {}

                    # Key detection
                    if "key" in features:
                        key_info = features["key"]
                        summary["musical_analysis"]["key"] = key_info.get(
                            "key", "unknown"
                        )
                        summary["musical_analysis"]["key_confidence"] = key_info.get(
                            "confidence", 0.0
                        )

                    # Tempo/BPM
                    if "tempo" in features:
                        tempo_info = features["tempo"]
                        summary["musical_analysis"]["bpm"] = tempo_info.get("bpm", 0.0)
                        summary["musical_analysis"]["beat_regularity"] = tempo_info.get(
                            "beat_regularity", 0.0
                        )

                    # Energy/Loudness
                    if "energy" in features:
                        energy_info = features["energy"]
                        summary["musical_analysis"]["loudness_db"] = energy_info.get(
                            "overall_loudness_db", 0.0
                        )
                        summary["musical_analysis"]["dynamic_range_db"] = (
                            energy_info.get("dynamic_range_db", 0.0)
                        )

                    # Spectral characteristics
                    if "spectral" in features:
                        spectral_info = features["spectral"]
                        if "spectral_centroid" in spectral_info:
                            summary["musical_analysis"]["brightness"] = spectral_info[
                                "spectral_centroid"
                            ].get("mean", 0.0)

                    # MFCC summary (just overall stats)
                    if "mfcc" in features:
                        mfcc_info = features["mfcc"]
                        summary["musical_analysis"]["timbral_complexity"] = (
                            mfcc_info.get("overall_std", 0.0)
                        )

                # Handle chunked results
                elif "aggregated_features" in result:
                    agg_features = result["aggregated_features"]
                    summary["musical_analysis"] = {}

                    if "tempo" in agg_features:
                        summary["musical_analysis"]["bpm"] = agg_features["tempo"].get(
                            "mean_bpm", 0.0
                        )
                        summary["musical_analysis"]["bpm_stability"] = agg_features[
                            "tempo"
                        ].get("std_bpm", 0.0)

                    if "key" in agg_features:
                        summary["musical_analysis"]["key"] = agg_features["key"].get(
                            "most_likely_key", "unknown"
                        )
                        summary["musical_analysis"]["key_confidence"] = agg_features[
                            "key"
                        ].get("confidence", 0.0)
                        summary["musical_analysis"]["key_changes"] = agg_features[
                            "key"
                        ].get("key_changes", 0)

                    summary["chunk_count"] = result.get("chunk_count", 0)

                return summary

            except Exception as e:
                logging.error(f"Error processing task result for {task_id}: {e}")
                return {
                    "task_id": task_id,
                    "status": "error",
                    "error": "Failed to process task result",
                }

        elif state == "PENDING":
            return {
                "task_id": task_id,
                "status": "pending",
                "message": "Task is waiting to be processed",
            }
        elif state == "PROGRESS":
            try:
                progress_info = task.info or {}
                return {
                    "task_id": task_id,
                    "status": "processing",
                    "progress": progress_info.get("progress", 0),
                }
            except Exception:
                return {"task_id": task_id, "status": "processing", "progress": 0}
        elif state == "FAILURE":
            try:
                error_info = task.info or "Unknown error"
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "error": str(error_info),
                }
            except Exception:
                return {
                    "task_id": task_id,
                    "status": "failed",
                    "error": "Task failed with unknown error",
                }
        else:
            return {"task_id": task_id, "status": state}

    except Exception as e:
        logging.error(f"Critical error in get_task_summary for {task_id}: {e}")
        return {
            "task_id": task_id,
            "status": "error",
            "error": f"Unable to retrieve task summary: {str(e)}",
        }


@router.delete("/{task_id}")
def delete_task(task_id: str):
    """
    Delete a corrupted or stuck task from Redis
    """
    try:
        task = celery_app.AsyncResult(task_id)
        task.forget()  # Remove from backend

        # Mark task as deleted in our tracking system
        client = get_redis_client()
        if client is not None:
            try:
                # Store deleted task ID with expiration (24 hours)
                client.setex(f"deleted_task:{task_id}", 86400, "1")
                logging.info(f"Marked task {task_id} as deleted in tracking system")
            except Exception as e:
                logging.error(f"Error marking task {task_id} as deleted: {e}")

        return {
            "task_id": task_id,
            "status": "deleted",
            "message": "Task removed from backend",
        }
    except Exception as e:
        logging.error(f"Error deleting task {task_id}: {e}")
        return {
            "task_id": task_id,
            "status": "error",
            "error": f"Failed to delete task: {str(e)}",
        }
