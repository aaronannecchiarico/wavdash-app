"""
Tempo Processing Tasks
Handles sped-up and slowed-down audio processing
"""

import os
import tempfile
import logging
import time
import requests
from typing import Dict, Any, Optional
import numpy as np
import librosa
import soundfile as sf
from celery import current_task
from pathlib import Path

from celery_app import celery_app
from config import settings
from utils.audio_utils import save_audio_file, load_audio_from_bytes
from services.storage_service import (
    get_storage_service,
    get_storage_type,
    StorageType,
    StorageError,
)
from services.audio_feature_extraction import create_feature_extractor
from models.tempo_models import TempoCallbackData, TempoPresetEnum

logger = logging.getLogger(__name__)

# Performance cache imports
from services.performance_cache import (
    get_performance_cache,
    get_performance_monitor,
    audio_hash,
)

# Phase 2: Enhanced audio processing imports
try:
    from pedalboard import (
        Pedalboard,
        Reverb,
        PitchShift,
        HighShelfFilter,
        LowShelfFilter,
        Compressor,
        Chorus,
    )

    PEDALBOARD_AVAILABLE = True
    logger.info("Pedalboard available - using enhanced audio effects")
except ImportError:
    PEDALBOARD_AVAILABLE = False
    logger.warning("Pedalboard not available - falling back to basic audio processing")

    # Create dummy classes for type annotations
    class Pedalboard:
        pass


# Tempo processing presets configuration
TEMPO_PRESETS = {
    TempoPresetEnum.SPED_UP: {
        "tempo_factor": 1.25,
        "pitch_shift_semitones": 3.0,
        "preserve_pitch": False,
        "effects": ["pitch_shift", "brightness_boost", "compression"],
        "compression_settings": {"threshold_db": -18, "ratio": 3.0},
        "description": "Faster tempo with higher pitch (chipmunk effect)",
    },
    TempoPresetEnum.SLOWED_REVERB: {
        "tempo_factor": 0.75,
        "pitch_shift_semitones": -2.0,
        "preserve_pitch": False,
        "effects": ["pitch_shift", "reverb", "compression"],
        "reverb_settings": {"wet_level": 0.35, "room_size": 0.5},
        "compression_settings": {"threshold_db": -20, "ratio": 2.5},
        "description": "Slower tempo with lower pitch and dreamy reverb effect",
    },
    TempoPresetEnum.NIGHTCORE: {
        "tempo_factor": 1.4,
        "pitch_shift_semitones": 4.0,
        "preserve_pitch": False,
        "effects": ["pitch_shift", "brightness_boost", "compression", "chorus"],
        "compression_settings": {"threshold_db": -16, "ratio": 4.0},
        "chorus_settings": {"rate_hz": 0.8, "depth": 0.3},
        "description": "Fast tempo, high pitch, increased brightness and energy",
    },
    TempoPresetEnum.CHOPPED_SCREWED: {
        "tempo_factor": 0.6,
        "pitch_shift_semitones": -3.0,
        "preserve_pitch": False,
        "effects": ["pitch_shift", "low_pass_filter", "compression"],
        "filter_settings": {"cutoff_hz": 1800},
        "compression_settings": {"threshold_db": -22, "ratio": 6.0},
        "description": "Slow tempo, low pitch, filtered sound with heavy compression",
    },
    TempoPresetEnum.TIME_STRETCHED: {
        "tempo_factor": 0.8,
        "pitch_shift_semitones": 0.0,
        "preserve_pitch": True,
        "effects": ["time_stretch", "compression"],
        "compression_settings": {"threshold_db": -20, "ratio": 2.0},
        "description": "Tempo change without pitch change, maintains vocal quality",
    },
}


def create_pedalboard_for_preset(
    preset_config: Dict,
    tempo_factor: float,
    pitch_shift_semitones: float,
    add_reverb: bool = False,
    stem_type: str = "full_mix",
) -> Optional[Pedalboard]:
    """
    Create a pedalboard with effects based on preset configuration
    Phase 2: Enhanced audio effects using pedalboard with stem-aware processing
    """
    if not PEDALBOARD_AVAILABLE:
        return None

    effects = []

    try:
        # Add pitch shift if specified and not traditional speed change
        if pitch_shift_semitones != 0.0:
            # Adjust pitch shift based on stem type for better quality
            adjusted_pitch = pitch_shift_semitones
            if stem_type == "vocals":
                # More conservative pitch shift for vocals to preserve naturalness
                adjusted_pitch = pitch_shift_semitones * 0.8
            elif stem_type == "drums":
                # Minimal pitch shift for drums to preserve punch
                adjusted_pitch = pitch_shift_semitones * 0.3

            effects.append(PitchShift(semitones=adjusted_pitch))
            logger.info(f"Added PitchShift: {adjusted_pitch} semitones for {stem_type}")

        # Add preset-specific effects
        if preset_config and "effects" in preset_config:
            preset_effects = preset_config["effects"]

            # Brightness boost (for sped up / nightcore)
            if "brightness_boost" in preset_effects:
                if stem_type == "vocals":
                    # More subtle boost for vocals
                    effects.append(
                        HighShelfFilter(cutoff_frequency_hz=4000, gain_db=1.5)
                    )
                elif stem_type == "drums":
                    # Enhance cymbal clarity
                    effects.append(
                        HighShelfFilter(cutoff_frequency_hz=8000, gain_db=3.0)
                    )
                else:
                    # Standard brightness boost
                    effects.append(
                        HighShelfFilter(cutoff_frequency_hz=3000, gain_db=2.0)
                    )
                logger.info(f"Added brightness boost for {stem_type}")

            # Low-pass filter (for chopped & screwed)
            if "low_pass_filter" in preset_effects:
                filter_settings = preset_config.get("filter_settings", {})

                if stem_type == "vocals":
                    # Preserve vocal clarity
                    cutoff_hz = filter_settings.get("cutoff_hz", 3000)
                    gain_db = -2.0
                elif stem_type == "drums":
                    # Reduce high-end harshness
                    cutoff_hz = filter_settings.get("cutoff_hz", 5000)
                    gain_db = -4.0
                else:
                    # Standard filtering
                    cutoff_hz = filter_settings.get("cutoff_hz", 1800)
                    gain_db = -3.0

                effects.append(
                    LowShelfFilter(cutoff_frequency_hz=cutoff_hz, gain_db=gain_db)
                )
                logger.info(f"Added low-pass filter at {cutoff_hz} Hz for {stem_type}")

            # Compression (for nightcore and dynamic effects)
            if "compression" in preset_effects:
                compression_settings = preset_config.get("compression_settings", {})
                threshold = compression_settings.get("threshold_db", -20)
                ratio = compression_settings.get("ratio", 4.0)

                if stem_type == "vocals":
                    # Gentle vocal compression
                    effects.append(
                        Compressor(
                            threshold_db=threshold + 2,
                            ratio=max(2.0, ratio * 0.75),
                            attack_ms=5,
                            release_ms=50,
                        )
                    )
                elif stem_type == "drums":
                    # Punchy drum compression
                    effects.append(
                        Compressor(
                            threshold_db=threshold - 3,
                            ratio=min(8.0, ratio * 1.5),
                            attack_ms=1,
                            release_ms=30,
                        )
                    )
                else:
                    # Use preset compression settings
                    effects.append(
                        Compressor(
                            threshold_db=threshold,
                            ratio=ratio,
                            attack_ms=10,
                            release_ms=100,
                        )
                    )
                logger.info(
                    f"Added compression (threshold: {threshold}dB, ratio: {ratio}:1) for {stem_type}"
                )

            # Chorus effect for enhanced texture
            if "chorus" in preset_effects:
                if stem_type != "drums":  # Skip chorus on drums
                    chorus_settings = preset_config.get("chorus_settings", {})
                    rate_hz = chorus_settings.get("rate_hz", 0.5)
                    depth = chorus_settings.get("depth", 0.25)

                    # Adjust chorus based on stem type
                    if stem_type == "vocals":
                        depth *= 0.8  # More subtle on vocals

                    effects.append(Chorus(rate_hz=rate_hz, depth=depth))
                    logger.info(
                        f"Added chorus effect (rate: {rate_hz}Hz, depth: {depth}) for {stem_type}"
                    )

        # Add reverb effect
        if add_reverb:
            reverb_settings = (
                preset_config.get("reverb_settings", {}) if preset_config else {}
            )

            if stem_type == "vocals":
                # Vocal-optimized reverb
                wet_level = reverb_settings.get("wet_level", 0.25)
                room_size = reverb_settings.get("room_size", 0.3)
            elif stem_type == "drums":
                # Minimal reverb on drums to maintain punch
                wet_level = reverb_settings.get("wet_level", 0.15)
                room_size = reverb_settings.get("room_size", 0.2)
            else:
                # Standard reverb settings
                wet_level = reverb_settings.get("wet_level", 0.35)
                room_size = reverb_settings.get("room_size", 0.5)

            effects.append(Reverb(wet_level=wet_level, room_size=room_size))
            logger.info(
                f"Added reverb (wet: {wet_level}, room: {room_size}) for {stem_type}"
            )

        if effects:
            return Pedalboard(effects)
        else:
            return None

    except Exception as e:
        logger.error(f"Error creating pedalboard for {stem_type}: {str(e)}")
        return None


def calculate_optimal_tempo_factor(current_bpm: float, target_style: str) -> float:
    """
    Use detected BPM to suggest optimal tempo factors for different styles
    Phase 2: BPM-aware processing suggestions
    """
    BPM_TARGETS = {
        "chill": (70, 90),
        "pop": (100, 130),
        "dance": (120, 140),
        "hyper": (140, 180),
        "slow_jam": (60, 80),
        "hip_hop": (70, 100),
        "electronic": (120, 160),
    }

    if target_style in BPM_TARGETS:
        min_bpm, max_bpm = BPM_TARGETS[target_style]
        target_bpm = (min_bpm + max_bpm) / 2
        suggested_factor = target_bpm / current_bpm

        # Clamp to reasonable range
        suggested_factor = max(0.25, min(4.0, suggested_factor))

        logger.info(
            f"BPM-aware suggestion: {current_bpm:.1f} -> {target_bpm:.1f} BPM (factor: {suggested_factor:.2f})"
        )
        return suggested_factor

    return 1.0


def get_smart_preset_suggestions(
    current_bpm: float, audio_duration: float
) -> Dict[str, Dict]:
    """
    Suggest optimal presets based on audio characteristics
    Phase 2: Intelligent preset recommendations
    """
    suggestions = {}

    # Analyze current BPM to suggest appropriate effects
    if current_bpm < 80:
        suggestions["speed_up"] = {
            "preset": TempoPresetEnum.SPED_UP,
            "reason": "Low BPM detected - speed up for more energy",
            "optimal_factor": calculate_optimal_tempo_factor(current_bpm, "pop"),
        }
    elif current_bpm > 140:
        suggestions["slow_down"] = {
            "preset": TempoPresetEnum.SLOWED_REVERB,
            "reason": "High BPM detected - slow down for chill vibes",
            "optimal_factor": calculate_optimal_tempo_factor(current_bpm, "chill"),
        }

    # Consider duration for processing suggestions
    if audio_duration > 300:  # 5+ minutes
        suggestions["time_stretch"] = {
            "preset": TempoPresetEnum.TIME_STRETCHED,
            "reason": "Long track - pitch-preserving tempo change recommended",
            "optimal_factor": 0.85,
        }

    # Always suggest nightcore for energetic transformation
    suggestions["energetic"] = {
        "preset": TempoPresetEnum.NIGHTCORE,
        "reason": "High-energy transformation with pitch and tempo boost",
        "optimal_factor": 1.3,
    }

    return suggestions


def process_stems_individually(
    stems_data: Dict[str, np.ndarray],
    sample_rate: int,
    preset_config: Dict,
    tempo_factor: float,
    pitch_shift_semitones: float,
    preserve_pitch: bool,
    add_reverb: bool,
) -> Dict[str, np.ndarray]:
    """
    Process each stem with optimized settings for stem type
    Phase 2: Stem-aware processing for higher quality results
    """
    processed_stems = {}

    for stem_name, stem_audio in stems_data.items():
        logger.info(f"Processing {stem_name} stem individually")

        try:
            # Apply tempo processing with stem-specific settings
            processed_stem = apply_tempo_processing(
                stem_audio,
                sample_rate,
                tempo_factor,
                pitch_shift_semitones,
                preserve_pitch,
                add_reverb,
                preset_config,
                stem_type=stem_name,
            )

            processed_stems[stem_name] = processed_stem
            logger.info(f"Successfully processed {stem_name} stem")

        except Exception as e:
            logger.error(f"Error processing {stem_name} stem: {str(e)}")
            # Fallback to original stem if processing fails
            processed_stems[stem_name] = stem_audio

    return processed_stems


def mix_processed_stems(
    processed_stems: Dict[str, np.ndarray],
    mixing_weights: Optional[Dict[str, float]] = None,
) -> np.ndarray:
    """
    Mix processed stems back together with optional level adjustments
    Phase 2: Intelligent stem mixing
    """
    if not processed_stems:
        raise ValueError("No processed stems to mix")

    # Default mixing weights
    if mixing_weights is None:
        mixing_weights = {"vocals": 1.0, "drums": 0.9, "bass": 0.85, "other": 0.8}

    # Get the length of the longest stem
    max_length = max(len(stem) for stem in processed_stems.values())

    # Initialize output array
    mixed_audio = np.zeros(max_length, dtype=np.float32)

    for stem_name, stem_audio in processed_stems.items():
        weight = mixing_weights.get(stem_name, 1.0)

        # Pad shorter stems to match longest
        if len(stem_audio) < max_length:
            padded_stem = np.pad(
                stem_audio, (0, max_length - len(stem_audio)), "constant"
            )
        else:
            padded_stem = stem_audio[:max_length]

        # Add weighted stem to mix
        mixed_audio += padded_stem * weight
        logger.info(f"Mixed {stem_name} stem with weight {weight}")

    # Normalize to prevent clipping
    max_amplitude = np.max(np.abs(mixed_audio))
    if max_amplitude > 0.95:
        mixed_audio = mixed_audio * (0.95 / max_amplitude)
        logger.info(f"Normalized mixed audio (peak was {max_amplitude:.3f})")

    return mixed_audio


def validate_tempo_processing_params(
    tempo_factor: float, pitch_shift_semitones: float, audio_duration: float
) -> Dict[str, str]:
    """
    Enhanced validation for tempo processing parameters
    Phase 2: Comprehensive parameter validation with warnings
    """
    warnings = {}

    # Tempo factor validation with quality warnings
    if tempo_factor < 0.25 or tempo_factor > 4.0:
        raise ValueError(f"Tempo factor {tempo_factor} out of range [0.25, 4.0]")
    elif tempo_factor < 0.5:
        warnings["tempo_extreme_slow"] = "Very slow tempo may cause audio artifacts"
    elif tempo_factor > 2.0:
        warnings["tempo_extreme_fast"] = "Very fast tempo may cause audio artifacts"

    # Pitch shift validation with quality warnings
    if pitch_shift_semitones < -12 or pitch_shift_semitones > 12:
        raise ValueError(
            f"Pitch shift {pitch_shift_semitones} out of range [-12, 12] semitones"
        )
    elif abs(pitch_shift_semitones) > 8:
        warnings["pitch_extreme"] = "Large pitch shifts may cause unnatural sound"

    # Duration-based recommendations
    if audio_duration > 600:  # 10 minutes
        warnings["long_duration"] = (
            "Long audio files may take significant processing time"
        )
    elif audio_duration < 10:  # Very short
        warnings["short_duration"] = (
            "Very short audio may not benefit from tempo processing"
        )

    # Combined effects warnings
    if tempo_factor > 1.5 and abs(pitch_shift_semitones) > 4:
        warnings["aggressive_processing"] = (
            "Combining high tempo and pitch changes may degrade quality"
        )

    return warnings


def handle_processing_error(
    error: Exception, context: str, audio_data: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Enhanced error handling with detailed context and recovery suggestions
    Phase 2: Comprehensive error handling
    """
    error_info = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        "timestamp": time.time(),
        "recovery_suggestions": [],
    }

    # Specific error handling
    if isinstance(error, ValueError):
        if "tempo_factor" in str(error).lower():
            error_info["recovery_suggestions"].append(
                "Adjust tempo_factor to range [0.25, 4.0]"
            )
        elif "pitch_shift" in str(error).lower():
            error_info["recovery_suggestions"].append(
                "Adjust pitch_shift_semitones to range [-12, 12]"
            )
        elif "audio" in str(error).lower():
            error_info["recovery_suggestions"].append(
                "Check audio file format and content"
            )

    elif isinstance(error, ImportError):
        if "pedalboard" in str(error).lower():
            error_info["recovery_suggestions"].extend(
                [
                    "Install pedalboard: pip install pedalboard",
                    "Processing will use fallback librosa methods",
                ]
            )

    elif isinstance(error, MemoryError):
        error_info["recovery_suggestions"].extend(
            [
                "Reduce audio file size or duration",
                "Use simpler presets to reduce memory usage",
                "Consider processing in chunks for large files",
            ]
        )

    elif "librosa" in str(error).lower():
        error_info["recovery_suggestions"].extend(
            [
                "Check audio file format compatibility",
                "Ensure sufficient system memory",
                "Try with a different audio file",
            ]
        )

    # Add audio-specific context if available
    if audio_data is not None:
        error_info["audio_context"] = {
            "shape": audio_data.shape if hasattr(audio_data, "shape") else None,
            "dtype": str(audio_data.dtype) if hasattr(audio_data, "dtype") else None,
            "length_seconds": (
                len(audio_data) / 44100 if hasattr(audio_data, "__len__") else None
            ),
        }

    logger.error(f"Processing error in {context}: {error_info}")
    return error_info


def check_system_compatibility() -> Dict[str, Any]:
    """
    Check system compatibility and capabilities for tempo processing
    Phase 2: System compatibility checking
    """
    compatibility = {
        "pedalboard_available": PEDALBOARD_AVAILABLE,
        "librosa_version": librosa.__version__,
        "numpy_version": np.__version__,
        "system_info": {},
        "recommendations": [],
    }

    # Check pedalboard availability
    if not PEDALBOARD_AVAILABLE:
        compatibility["recommendations"].append(
            "Install pedalboard for enhanced audio effects"
        )

    # Check memory availability (basic check)
    try:
        import psutil

        memory_info = psutil.virtual_memory()
        compatibility["system_info"]["available_memory_gb"] = memory_info.available / (
            1024**3
        )

        if memory_info.available < 2 * (1024**3):  # Less than 2GB
            compatibility["recommendations"].append(
                "Low memory detected - consider smaller audio files"
            )
    except ImportError:
        compatibility["recommendations"].append("Install psutil for memory monitoring")

    # Check for Apple Silicon compatibility
    try:
        import platform

        if platform.machine() == "arm64" and platform.system() == "Darwin":
            compatibility["system_info"]["apple_silicon"] = True
            compatibility["recommendations"].append(
                "Apple Silicon detected - CPU processing will be used for compatibility"
            )
    except Exception:
        pass

    return compatibility


def generate_tempo_filename(
    original_filename: str,
    preset: str,
    tempo_factor: float,
    pitch_shift_semitones: float = 0,
) -> str:
    """
    Generate descriptive filename for tempo processed audio following user-friendly conventions

    Args:
        original_filename: Original audio filename
        preset: Tempo preset used (e.g., "nightcore", "sped_up", "custom")
        tempo_factor: Factor applied (e.g., 1.25 for 25% faster)
        pitch_shift_semitones: Pitch shift in semitones

    Returns:
        Descriptive filename like "my-song_tempo_nightcore-140.wav"
    """
    base_name = Path(original_filename).stem  # Remove extension

    # Create descriptive suffix based on preset and parameters
    if preset == "sped_up":
        suffix = f"sped-up-{round(tempo_factor * 100)}"
    elif preset == "slowed_reverb":
        suffix = f"slowed-reverb-{round(tempo_factor * 100)}"
    elif preset == "nightcore":
        suffix = f"nightcore-{round(tempo_factor * 100)}"
    elif preset == "chopped_screwed":
        suffix = f"chopped-screwed-{round(tempo_factor * 100)}"
    elif preset == "time_stretched":
        suffix = f"time-stretched-{round(tempo_factor * 100)}"
    else:
        # Custom preset
        suffix = f"custom-{round(tempo_factor * 100)}"

    # Add pitch shift if non-zero
    if pitch_shift_semitones != 0:
        suffix += f"-pitch{int(pitch_shift_semitones):+d}"

    return f"{base_name}_tempo_{suffix}.wav"


def build_tempo_file_path(user_id: str, upload_date, filename: str) -> str:
    """
    Build consistent file path following Laravel conventions

    Args:
        user_id: User ID for folder structure
        upload_date: Date object for year/month/day structure
        filename: Generated filename

    Returns:
        Path like "processed/{user_id}/2025/08/17/{filename}"
    """
    year = upload_date.strftime("%Y")
    month = upload_date.strftime("%m")
    day = upload_date.strftime("%d")

    return f"processed/{user_id}/{year}/{month}/{day}/{filename}"


def calculate_processing_quality_score(
    processing_warnings: list,
    processing_time: float,
    audio_duration: float,
    cache_hit: bool = False,
) -> float:
    """
    Calculate a quality score for tempo processing (0.0-1.0)

    Args:
        processing_warnings: List of warnings encountered
        processing_time: Time taken to process
        audio_duration: Original audio duration
        cache_hit: Whether result was cached

    Returns:
        Quality score from 0.0 (poor) to 1.0 (excellent)
    """
    score = 1.0

    # Reduce score for warnings
    warning_penalty = len(processing_warnings) * 0.1
    score -= min(warning_penalty, 0.3)  # Max 30% penalty for warnings

    # Reduce score for very slow processing (unless cached)
    if not cache_hit:
        processing_ratio = processing_time / audio_duration
        if processing_ratio > 2.0:  # Taking more than 2x the audio duration
            time_penalty = min((processing_ratio - 2.0) * 0.1, 0.2)  # Max 20% penalty
            score -= time_penalty

    # Ensure score stays within bounds
    return max(0.0, min(1.0, score))


def get_processing_warnings(
    tempo_factor: float,
    pitch_shift_semitones: float,
    audio_duration: float,
    preset_config: dict = None,
) -> list:
    """
    Generate processing warnings based on parameters and audio characteristics

    Returns:
        List of warning messages for potentially problematic settings
    """
    warnings = []

    # Extreme tempo warnings
    if tempo_factor < 0.5:
        warnings.append("Very slow tempo may cause audio artifacts")
    elif tempo_factor > 2.0:
        warnings.append("Very fast tempo may cause audio artifacts")

    # Extreme pitch warnings
    if abs(pitch_shift_semitones) > 8:
        warnings.append("Large pitch shifts may cause unnatural sound")

    # Duration warnings
    if audio_duration > 600:  # 10 minutes
        warnings.append("Long audio files may take significant processing time")
    elif audio_duration < 10:  # Very short
        warnings.append("Very short audio may not benefit from tempo processing")

    # Combined effects warnings
    if tempo_factor > 1.5 and abs(pitch_shift_semitones) > 4:
        warnings.append("Combining high tempo and pitch changes may degrade quality")

    return warnings


def apply_tempo_processing(
    audio_data,
    sample_rate,
    tempo_factor,
    pitch_shift_semitones,
    preserve_pitch,
    add_reverb,
    preset_config=None,
    stem_type="full_mix",
):
    """
    Apply tempo and pitch processing to audio data

    Phase 3: Optimized implementation with performance caching and monitoring
    Falls back to librosa if pedalboard is not available
    """
    monitor = get_performance_monitor()
    start_time = time.time()

    try:
        # Validate inputs
        if audio_data is None or len(audio_data) == 0:
            raise ValueError("Audio data cannot be None or empty")

        if sample_rate <= 0:
            raise ValueError("Sample rate must be positive")

        # Check cache first for performance optimization
        cache = get_performance_cache()
        audio_hash_key = audio_hash(audio_data)
        processing_params = {
            "tempo_factor": tempo_factor,
            "pitch_shift_semitones": pitch_shift_semitones,
            "preserve_pitch": preserve_pitch,
            "add_reverb": add_reverb,
            "preset": (
                preset_config.get("preset", "custom") if preset_config else "custom"
            ),
            "stem_type": stem_type,
        }

        cache_key = cache.generate_audio_cache_key(audio_hash_key, processing_params)
        cached_result = cache.get_cached_processed_audio(cache_key, max_age_hours=48)

        if cached_result:
            processing_time = time.time() - start_time
            monitor.record_processing_time(
                processing_time,
                processing_params["preset"],
                len(audio_data) * 4 / (1024 * 1024),
                cache_hit=True,
            )
            logger.info(
                f"🚀 Cache hit for tempo processing: {cache_key[:8]}... (saved {processing_time:.3f}s)"
            )
            return cached_result["audio_data"].astype(np.float32)

        processed_audio = audio_data.copy()

        # Step 1: Handle tempo changes - use librosa for time stretching
        if tempo_factor != 1.0:
            if preserve_pitch:
                # Use librosa for high-quality phase vocoder time stretching
                processed_audio = librosa.effects.time_stretch(
                    processed_audio, rate=tempo_factor
                )
                logger.info(
                    f"Applied time stretch with factor {tempo_factor} (pitch preserved) for {stem_type}"
                )
            else:
                # For non-pitch preserving, we'll combine tempo + pitch changes
                processed_audio = librosa.effects.time_stretch(
                    processed_audio, rate=tempo_factor
                )
                logger.info(
                    f"Applied time stretch with factor {tempo_factor} for {stem_type}"
                )

        # Step 2: Apply pedalboard effects for enhanced audio processing
        if PEDALBOARD_AVAILABLE:
            logger.debug(
                f"Using pedalboard for audio effects processing on {stem_type}"
            )

            # Ensure audio is in the right format for pedalboard
            if processed_audio.ndim == 1:
                # Keep mono for now, pedalboard can handle it
                audio_for_processing = processed_audio
            else:
                # Convert stereo to mono for processing
                audio_for_processing = np.mean(processed_audio, axis=0)

            # Create pedalboard with preset-specific effects and stem awareness
            pedalboard_fx = create_pedalboard_for_preset(
                preset_config,
                tempo_factor,
                pitch_shift_semitones,
                add_reverb,
                stem_type,
            )

            if pedalboard_fx:
                # Apply pedalboard effects
                processed_audio = pedalboard_fx(audio_for_processing, sample_rate)

                # Ensure output is mono (flatten if needed)
                if processed_audio.ndim > 1:
                    processed_audio = processed_audio.flatten()

                logger.debug(f"Applied pedalboard effects successfully to {stem_type}")
            else:
                logger.debug(f"No pedalboard effects to apply for {stem_type}")

        else:
            # Fallback to librosa-based processing if pedalboard not available
            logger.warning(
                f"Pedalboard not available - using fallback audio processing for {stem_type}"
            )

            # Handle pitch shift without tempo change
            if pitch_shift_semitones != 0.0:
                processed_audio = librosa.effects.pitch_shift(
                    processed_audio, sr=sample_rate, n_steps=pitch_shift_semitones
                )
                logger.info(
                    f"Applied pitch shift of {pitch_shift_semitones} semitones to {stem_type}"
                )

            # Basic reverb effect using convolution (fallback)
            if add_reverb:
                reverb_length = int(0.5 * sample_rate)  # 0.5 second reverb
                decay = np.exp(-np.linspace(0, 3, reverb_length))
                reverb_impulse = np.random.normal(0, 0.1, reverb_length) * decay

                # Apply reverb
                reverb_audio = np.convolve(processed_audio, reverb_impulse, mode="same")

                # Ensure both arrays have the same length
                min_length = min(len(processed_audio), len(reverb_audio))
                processed_audio = processed_audio[:min_length]
                reverb_audio = reverb_audio[:min_length]

                # Mix with original (30% wet, 70% dry)
                processed_audio = 0.7 * processed_audio + 0.3 * reverb_audio
                logger.info(f"Applied basic reverb effect to {stem_type}")

        # Convert to float32 for consistency
        result = processed_audio.astype(np.float32)

        # Cache the result for future use (if processing took significant time)
        processing_time = time.time() - start_time
        if processing_time > 0.5:  # Only cache if processing took more than 0.5 seconds
            cache.cache_processed_audio(
                cache_key, result, sample_rate, processing_params
            )
            logger.debug(
                f"💾 Cached tempo processing result (took {processing_time:.2f}s): {cache_key[:8]}..."
            )

        # Record performance metrics
        file_size_mb = len(audio_data) * 4 / (1024 * 1024)  # Estimate for float32 array
        monitor.record_processing_time(
            processing_time, processing_params["preset"], file_size_mb, cache_hit=False
        )

        return result

    except Exception as e:
        processing_time = time.time() - start_time
        monitor.record_error()
        logger.error(f"Error in tempo processing for {stem_type}: {str(e)}")
        raise


@celery_app.task(
    bind=True,
    name="tasks.tempo_processing.process_tempo_from_storage",
    queue="tempo_processing",
)
def process_tempo_from_storage(
    self,
    task_id: str,
    storage_path: str,
    preset: str = "custom",
    tempo_factor: float = 1.0,
    pitch_shift_semitones: float = 0.0,
    preserve_pitch: bool = False,
    add_reverb: bool = False,
    use_stems: bool = False,
    callback_url: Optional[str] = None,
    metadata: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Process tempo modifications from storage (local or R2) with callback support
    Enhanced with improved file naming and complete callback data structure
    """
    start_time = time.time()
    temp_input_path = None
    temp_output_path = None
    storage = None
    cache_hit = False

    try:
        current_task.update_state(
            state="PROGRESS",
            meta={
                "progress": 0,
                "status": "Initializing tempo processing",
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
            meta={"progress": 20, "status": "Loading audio file", "task_id": task_id},
        )

        # Load audio file
        audio_data, sample_rate = librosa.load(temp_input_path, sr=None, mono=False)

        # Ensure mono for processing (Phase 1 limitation)
        if audio_data.ndim > 1:
            audio_data = np.mean(audio_data, axis=0)

        logger.info(f"Loaded audio: {audio_data.shape} samples at {sample_rate} Hz")

        # Get preset configuration if not custom
        preset_config = {}
        if preset != "custom" and preset in TEMPO_PRESETS:
            preset_config = TEMPO_PRESETS[TempoPresetEnum(preset)]
            # Override with preset values if not explicitly provided
            if tempo_factor == 1.0:
                tempo_factor = preset_config.get("tempo_factor", 1.0)
            if pitch_shift_semitones == 0.0:
                pitch_shift_semitones = preset_config.get("pitch_shift_semitones", 0.0)
            if not preserve_pitch:
                preserve_pitch = preset_config.get("preserve_pitch", False)
            if not add_reverb and "reverb" in preset_config.get("effects", []):
                add_reverb = True

        current_task.update_state(
            state="PROGRESS",
            meta={
                "progress": 40,
                "status": f"Applying tempo processing (preset: {preset})",
                "task_id": task_id,
            },
        )

        # Initialize cache for performance optimization
        cache = get_performance_cache()

        # Generate audio hash for caching
        audio_file_hash = audio_hash(audio_data)
        logger.debug(f"Audio hash generated: {audio_file_hash[:8]}...")

        # Try to get cached BPM analysis first
        cached_bpm_data = cache.get_cached_bpm_analysis(audio_file_hash)
        if cached_bpm_data:
            original_bpm = cached_bpm_data.get("bpm", 120.0)
            logger.info(f"Using cached BPM: {original_bpm:.2f}")
        else:
            # Extract original BPM for analysis
            current_task.update_state(
                state="PROGRESS",
                meta={
                    "progress": 45,
                    "status": "Analyzing BPM (not cached)",
                    "task_id": task_id,
                },
            )
            original_bpm = librosa.beat.tempo(y=audio_data, sr=sample_rate)[0]
            logger.info(f"Computed BPM: {original_bpm:.2f}")

            # Cache the BPM analysis for future use
            bpm_analysis_data = {
                "bpm": float(original_bpm),
                "sample_rate": sample_rate,
                "duration": len(audio_data) / sample_rate,
                "analysis_timestamp": time.time(),
            }
            cache.cache_bpm_analysis(audio_file_hash, bpm_analysis_data)
            logger.debug(f"Cached BPM analysis for future use")

        # Generate smart preset suggestions and warnings based on audio characteristics
        duration = len(audio_data) / sample_rate
        smart_suggestions = get_smart_preset_suggestions(original_bpm, duration)
        processing_warnings = get_processing_warnings(
            tempo_factor, pitch_shift_semitones, duration, preset_config
        )

        if processing_warnings:
            logger.warning(f"Processing warnings: {processing_warnings}")

        # Generate cache key for processed audio
        processing_params = {
            "tempo_factor": tempo_factor,
            "pitch_shift_semitones": pitch_shift_semitones,
            "preserve_pitch": preserve_pitch,
            "preset": preset,
            "add_reverb": add_reverb,
            "stem_type": "full_mix" if not use_stems else "stems",
        }
        audio_cache_key = cache.generate_audio_cache_key(
            audio_file_hash, processing_params
        )

        # Try to get cached processed audio
        cached_audio_data = cache.get_cached_processed_audio(audio_cache_key)
        if cached_audio_data:
            processed_audio = cached_audio_data["audio_data"]
            sample_rate = cached_audio_data["sample_rate"]
            cache_hit = True
            logger.info(f"Using cached processed audio")
        else:
            # Apply tempo processing with preset configuration
            current_task.update_state(
                state="PROGRESS",
                meta={
                    "progress": 50,
                    "status": "Processing audio (not cached)",
                    "task_id": task_id,
                },
            )
            processed_audio = apply_tempo_processing(
                audio_data,
                sample_rate,
                tempo_factor,
                pitch_shift_semitones,
                preserve_pitch,
                add_reverb,
                preset_config,
            )

            # Cache the processed audio for future use
            cache.cache_processed_audio(
                audio_cache_key, processed_audio, sample_rate, processing_params
            )
            logger.debug(f"Cached processed audio for future use")

        # Calculate final BPM
        if tempo_factor != 1.0 and not preserve_pitch:
            final_bpm = original_bpm * tempo_factor
        else:
            final_bpm = original_bpm

        current_task.update_state(
            state="PROGRESS",
            meta={
                "progress": 70,
                "status": "Saving processed audio",
                "task_id": task_id,
            },
        )

        # Save processed audio to temporary file
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_file:
            temp_output_path = temp_file.name

        sf.write(temp_output_path, processed_audio, sample_rate)
        logger.info(f"Saved processed audio to {temp_output_path}")

        current_task.update_state(
            state="PROGRESS",
            meta={
                "progress": 85,
                "status": "Uploading processed audio to storage",
                "task_id": task_id,
            },
        )

        # Extract original filename and user info for improved naming
        original_filename = Path(storage_path).name
        user_id = None
        if metadata and "user_id" in metadata:
            user_id = str(metadata["user_id"])

        # Generate descriptive filename using improved naming convention
        output_filename = generate_tempo_filename(
            original_filename=original_filename,
            preset=preset,
            tempo_factor=tempo_factor,
            pitch_shift_semitones=pitch_shift_semitones,
        )

        # Build consistent file path following Laravel conventions
        if user_id:
            from datetime import datetime

            upload_date = datetime.now()
            output_path = build_tempo_file_path(user_id, upload_date, output_filename)
        else:
            # Fallback for cases without user_id
            base_dir = (
                Path(storage_path).parent.parent.parent
                / "processed"
                / Path(storage_path).parent.name
            )
            output_path = str(base_dir / output_filename)

        # Upload processed audio to storage
        if not storage.upload_file(temp_output_path, output_path):
            raise StorageError(
                f"Failed to upload processed audio to storage: {output_path}"
            )

        processing_time = time.time() - start_time

        # Generate public URL if available
        public_url = storage.get_public_url(output_path)

        # Calculate quality score for the processing
        quality_score = calculate_processing_quality_score(
            processing_warnings, processing_time, duration, cache_hit
        )

        # Create comprehensive processing summary with all required fields
        tempo_processing = {
            "preset": preset,
            "tempo_factor": tempo_factor,
            "pitch_shift_semitones": pitch_shift_semitones,
            "preserve_pitch": preserve_pitch,
            "processing_method": "stems_separate" if use_stems else "direct",
            "effects_applied": [],
            "final_bpm": final_bpm,
            "quality_score": quality_score,
            "processing_warnings": processing_warnings,
        }

        # Populate effects_applied based on actual processing
        if tempo_factor != 1.0:
            tempo_processing["effects_applied"].append("tempo_change")
        if pitch_shift_semitones != 0.0:
            tempo_processing["effects_applied"].append("pitch_shift")
        if add_reverb:
            tempo_processing["effects_applied"].append("reverb")
        if preset_config and "brightness_boost" in preset_config.get("effects", []):
            tempo_processing["effects_applied"].append("brightness_boost")
        if preset_config and "compression" in preset_config.get("effects", []):
            tempo_processing["effects_applied"].append("compression")

        # Enhanced original analysis with more details
        original_analysis = {
            "bpm": float(original_bpm),
            "duration": float(duration),
            "sample_rate": int(sample_rate),
            "audio_hash": audio_file_hash[:16],  # Include hash for debugging
        }

        # Include key detection if available from cache or quick analysis
        try:
            chroma_stft = librosa.feature.chroma_stft(y=audio_data, sr=sample_rate)
            key_profile = np.mean(chroma_stft, axis=1)
            key_names = [
                "C",
                "C#",
                "D",
                "D#",
                "E",
                "F",
                "F#",
                "G",
                "G#",
                "A",
                "A#",
                "B",
            ]
            estimated_key = key_names[np.argmax(key_profile)]
            original_analysis["key"] = estimated_key
        except Exception:
            original_analysis["key"] = "Unknown"

        result = {
            "task_id": task_id,
            "status": "completed",
            "original_analysis": original_analysis,
            "tempo_processing": tempo_processing,
            "smart_suggestions": smart_suggestions,
            "processing_warnings": processing_warnings,
            "output_files": {"processed_audio": output_path},
            "public_urls": {"processed_audio": public_url} if public_url else {},
            "processing_time": processing_time,
            "storage_type": storage_type.value,
            "metadata": metadata or {},
        }

        current_task.update_state(
            state="PROGRESS",
            meta={"progress": 100, "status": "Completed", "task_id": task_id},
        )

        # Send enhanced callback with complete metadata
        if callback_url:
            try:
                callback_data = TempoCallbackData(
                    task_id=task_id,
                    status="completed",
                    processing_type="tempo",
                    original_analysis=result["original_analysis"],
                    tempo_processing=result["tempo_processing"],
                    storage_paths={
                        "processed_audio": output_path,
                        "original": storage_path,
                    },
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
                    f"Enhanced callback sent for tempo task {task_id}: {response.status_code}"
                )

            except Exception as callback_error:
                logger.error(
                    f"Failed to send callback for tempo task {task_id}: {callback_error}"
                )

        return result

    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = str(e)

        # Enhanced error handling with detailed context
        error_info = handle_processing_error(
            e,
            f"tempo processing task {task_id}",
            audio_data if "audio_data" in locals() else None,
        )

        logger.error(f"Error in tempo processing task {task_id}: {error_msg}")

        current_task.update_state(
            state="FAILURE",
            meta={
                "error": error_msg,
                "error_details": error_info,
                "status": "failed",
                "task_id": task_id,
                "storage_path": storage_path,
                "processing_time": processing_time,
                "storage_type": get_storage_type().value,
            },
        )

        # Send failure callback with enhanced error information
        if callback_url:
            try:
                callback_data = TempoCallbackData(
                    task_id=task_id,
                    status="failed",
                    processing_type="tempo",
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
                    f"Failed to send failure callback for tempo task {task_id}: {callback_error}"
                )

        raise

    finally:
        # Cleanup temporary files
        for temp_path in [temp_input_path, temp_output_path]:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.unlink(temp_path)
                except Exception as cleanup_error:
                    logger.warning(
                        f"Failed to cleanup temp file {temp_path}: {cleanup_error}"
                    )
