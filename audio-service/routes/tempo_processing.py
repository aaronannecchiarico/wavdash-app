"""
Tempo Processing Routes
Handles sped-up and slowed-down audio processing
"""

import logging
import time
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from models.tempo_models import (
    StorageTempoProcessingRequest,
    TempoProcessingResponse,
    TempoPresetEnum,
)
from services.storage_service import (
    get_storage_service,
    is_storage_enabled,
    get_storage_type,
)
from services.tempo_presets import get_tempo_presets_service
from celery_app import celery_app
from tasks.tempo_processing import process_tempo_from_storage
from utils.route_helpers import (
    generate_task_id,
    validate_storage_and_file,
    get_storage_type_value,
    handle_route_error,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/tempo", tags=["Tempo Processing"])


@router.post("/storage/process", response_model=TempoProcessingResponse)
def process_tempo_from_storage_route(request: StorageTempoProcessingRequest):
    """
    Process audio file with tempo/pitch modifications (storage-based)

    This is the recommended endpoint for Laravel integration.
    Processes files already stored in the configured storage system.
    """
    try:
        # Validate storage and file existence
        validate_storage_and_file(request.storage_path)

        # Generate unique task ID
        task_id = generate_task_id()

        # Submit to Celery - use the imported task function
        task = process_tempo_from_storage.delay(task_id=task_id, **request.model_dump())

        return TempoProcessingResponse(
            task_id=task_id,
            status="processing",
            message=f"Tempo processing started for {request.storage_path} with preset '{request.preset.value}'",
            storage_type=get_storage_type_value(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in storage-based tempo processing: {str(e)}")
        handle_route_error(e, "storage-based tempo processing")


@router.get("/presets")
def get_tempo_presets():
    """
    Get available tempo processing presets

    Returns information about available presets and their configurations.
    """
    presets_service = get_tempo_presets_service()

    # Get all preset configurations
    all_presets = presets_service.get_all_presets_info()

    # Add custom preset information
    all_presets["custom"] = {
        "name": "Custom",
        "tempo_factor": 1.0,
        "pitch_shift_semitones": 0.0,
        "preserve_pitch": False,
        "effects": [],
    }

    # Add descriptions for each preset
    for preset_key, preset_info in all_presets.items():
        try:
            preset_enum = TempoPresetEnum(preset_key)
            preset_info["description"] = presets_service.get_preset_description(
                preset_enum
            )
        except ValueError:
            if preset_key == "custom":
                preset_info["description"] = "Custom tempo/pitch settings"

    return {
        "available_presets": all_presets,
        "default_preset": "custom",
        "tempo_factor_range": {"min": 0.25, "max": 4.0},
        "pitch_shift_range": {"min": -12.0, "max": 12.0},
        "supported_effects": [
            "pitch_shift",
            "reverb",
            "time_stretch",
            "brightness_boost",
            "compression",
            "low_pass_filter",
        ],
    }


@router.get("/system/compatibility")
def check_system_compatibility():
    """
    Check system compatibility for tempo processing

    Returns information about available libraries, system resources,
    and recommendations for optimal performance.
    """
    from tasks.tempo_processing import check_system_compatibility

    try:
        compatibility_info = check_system_compatibility()
        return {
            "status": "success",
            "compatibility": compatibility_info,
            "phase": (
                "Phase 2: Enhanced pedalboard processing available"
                if compatibility_info["pedalboard_available"]
                else "Phase 1: Basic librosa processing"
            ),
        }
    except Exception as e:
        logger.error(f"Error checking system compatibility: {str(e)}")
        return {"status": "error", "error": str(e), "fallback_available": True}


@router.get("/suggest-presets")
def suggest_presets_for_audio(current_bpm: float, duration_seconds: float):
    """
    Get intelligent preset suggestions based on audio characteristics

    Analyzes the provided BPM and duration to suggest optimal presets
    for tempo processing.
    """
    from tasks.tempo_processing import get_smart_preset_suggestions

    try:
        suggestions = get_smart_preset_suggestions(current_bpm, duration_seconds)

        # Convert enum values to strings for JSON serialization
        serializable_suggestions = {}
        for key, suggestion in suggestions.items():
            serializable_suggestions[key] = {
                "preset": suggestion["preset"].value,
                "reason": suggestion["reason"],
                "optimal_factor": suggestion["optimal_factor"],
            }

        return {
            "status": "success",
            "audio_analysis": {
                "bpm": current_bpm,
                "duration_seconds": duration_seconds,
                "classification": (
                    "fast"
                    if current_bpm > 140
                    else "slow" if current_bpm < 80 else "moderate"
                ),
            },
            "suggestions": serializable_suggestions,
        }

    except Exception as e:
        logger.error(f"Error generating preset suggestions: {str(e)}")
        return {"status": "error", "error": str(e)}


@router.get("/performance/metrics")
def get_performance_metrics():
    """
    Get performance metrics and cache statistics

    Provides insights into processing times, cache hit rates, and system performance.
    """
    try:
        from services.performance_cache import (
            get_performance_monitor,
            get_performance_cache,
        )

        monitor = get_performance_monitor()
        cache = get_performance_cache()

        # Get performance summary
        performance_summary = monitor.get_performance_summary()

        # Get cache statistics
        cache_stats = cache.get_cache_stats()

        return {
            "status": "success",
            "timestamp": time.time(),
            "performance_metrics": performance_summary,
            "cache_statistics": cache_stats,
            "recommendations": _generate_performance_recommendations(
                performance_summary, cache_stats
            ),
        }

    except Exception as e:
        logger.error(f"Error getting performance metrics: {str(e)}")
        return {"status": "error", "error": str(e)}


@router.post("/performance/cache/clear")
def clear_performance_cache(cache_type: str = "all"):
    """
    Clear performance cache

    Parameters:
    - cache_type: Type of cache to clear ("all", "audio", "bpm", "preset")
    """
    try:
        from services.performance_cache import get_performance_cache
        import shutil

        cache = get_performance_cache()

        if cache_type == "all":
            # Clear entire cache directory
            if cache.cache_dir.exists():
                shutil.rmtree(cache.cache_dir)
                cache.cache_dir.mkdir(exist_ok=True)
                # Recreate subdirectories
                cache.audio_cache_dir.mkdir(exist_ok=True)
                cache.bpm_cache_dir.mkdir(exist_ok=True)
                cache.preset_cache_dir.mkdir(exist_ok=True)
            cleared_files = "all cache files"
        else:
            # Clear specific cache type
            cache_dirs = {
                "audio": cache.audio_cache_dir,
                "bpm": cache.bpm_cache_dir,
                "preset": cache.preset_cache_dir,
            }

            if cache_type not in cache_dirs:
                raise ValueError(f"Invalid cache type: {cache_type}")

            cache_dir = cache_dirs[cache_type]
            files_removed = 0
            for cache_file in cache_dir.glob("*.cache"):
                cache_file.unlink()
                files_removed += 1

            cleared_files = f"{files_removed} {cache_type} cache files"

        logger.info(f"Performance cache cleared: {cleared_files}")

        return {
            "status": "success",
            "message": f"Cleared {cleared_files}",
            "cache_type": cache_type,
        }

    except Exception as e:
        logger.error(f"Error clearing cache: {str(e)}")
        return {"status": "error", "error": str(e)}


def _generate_performance_recommendations(
    performance_summary: dict, cache_stats: dict
) -> list:
    """Generate performance optimization recommendations based on metrics"""
    recommendations = []

    # Cache hit rate recommendations
    cache_hit_rate = performance_summary.get("cache_hit_rate_percent", 0)
    if cache_hit_rate < 30:
        recommendations.append(
            {
                "type": "cache_optimization",
                "priority": "high",
                "message": f"Low cache hit rate ({cache_hit_rate:.1f}%). Consider increasing cache TTL or processing similar audio files.",
                "action": "Review cache settings and processing patterns",
            }
        )
    elif cache_hit_rate > 80:
        recommendations.append(
            {
                "type": "performance",
                "priority": "info",
                "message": f"Excellent cache hit rate ({cache_hit_rate:.1f}%). System is well optimized.",
                "action": "No action needed",
            }
        )

    # Processing time recommendations
    processing_times = performance_summary.get("processing_times", {})
    avg_time = processing_times.get("average_seconds", 0)
    p95_time = processing_times.get("p95_seconds", 0)

    if avg_time > 30:
        recommendations.append(
            {
                "type": "performance",
                "priority": "high",
                "message": f"High average processing time ({avg_time:.1f}s). Consider optimizing processing parameters.",
                "action": "Review preset complexity and file sizes",
            }
        )

    if p95_time > 60:
        recommendations.append(
            {
                "type": "performance",
                "priority": "medium",
                "message": f"95th percentile processing time is high ({p95_time:.1f}s). Some requests are taking very long.",
                "action": "Monitor for large files or complex presets causing delays",
            }
        )

    # Error rate recommendations
    error_rate = performance_summary.get("error_rate_percent", 0)
    if error_rate > 5:
        recommendations.append(
            {
                "type": "reliability",
                "priority": "high",
                "message": f"High error rate ({error_rate:.1f}%). System reliability needs attention.",
                "action": "Review error logs and common failure patterns",
            }
        )

    # Cache size recommendations
    cache_size_mb = cache_stats.get("total_size_mb", 0)
    if cache_size_mb > 400:  # Close to 500MB limit
        recommendations.append(
            {
                "type": "storage",
                "priority": "medium",
                "message": f"Cache size is high ({cache_size_mb:.1f}MB). May need cleanup soon.",
                "action": "Consider manual cache cleanup or reducing TTL",
            }
        )

    # File size recommendations
    avg_file_size = performance_summary.get("average_file_size_mb", 0)
    if avg_file_size > 20:
        recommendations.append(
            {
                "type": "optimization",
                "priority": "medium",
                "message": f"Large average file size ({avg_file_size:.1f}MB). Consider preprocessing optimization.",
                "action": "Review input file formats and sizes",
            }
        )

    return recommendations
