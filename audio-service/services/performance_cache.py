"""
Performance Optimization and Caching Service
Phase 3: Optimization & Polish - Performance improvements and caching strategies
"""

import os
import time
import hashlib
import pickle
import logging
from typing import Dict, Any, Optional, Callable, Union
from pathlib import Path
import tempfile
import numpy as np
from functools import wraps
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class PerformanceCache:
    """
    Intelligent caching system for tempo processing operations
    Caches processed audio, BPM analysis, and preset configurations
    """

    def __init__(self, cache_dir: Optional[str] = None, max_cache_size_mb: int = 500):
        self.cache_dir = (
            Path(cache_dir)
            if cache_dir
            else Path(tempfile.gettempdir()) / "beatforge_cache"
        )
        self.max_cache_size_mb = max_cache_size_mb
        self.cache_dir.mkdir(exist_ok=True)

        # Create subdirectories for different cache types
        self.audio_cache_dir = self.cache_dir / "audio"
        self.bpm_cache_dir = self.cache_dir / "bpm"
        self.preset_cache_dir = self.cache_dir / "presets"

        for cache_subdir in [
            self.audio_cache_dir,
            self.bpm_cache_dir,
            self.preset_cache_dir,
        ]:
            cache_subdir.mkdir(exist_ok=True)

        # Cache performance tracking
        self.cache_hits = {"audio": 0, "bpm": 0, "preset": 0}
        self.cache_misses = {"audio": 0, "bpm": 0, "preset": 0}

        logger.info(f"Performance cache initialized at {self.cache_dir}")

    def _generate_cache_key(
        self, data: Union[str, bytes, Dict], prefix: str = ""
    ) -> str:
        """Generate a unique cache key from input data"""
        if isinstance(data, dict):
            # Sort dict keys for consistent hashing
            data_str = str(sorted(data.items()))
        elif isinstance(data, bytes):
            data_str = hashlib.md5(data).hexdigest()
        else:
            data_str = str(data)

        cache_key = hashlib.sha256(data_str.encode()).hexdigest()[:16]
        return f"{prefix}_{cache_key}" if prefix else cache_key

    def _get_cache_file_path(self, cache_key: str, cache_type: str) -> Path:
        """Get the full path for a cache file"""
        cache_dirs = {
            "audio": self.audio_cache_dir,
            "bpm": self.bpm_cache_dir,
            "preset": self.preset_cache_dir,
        }
        return cache_dirs[cache_type] / f"{cache_key}.cache"

    def _is_cache_valid(self, cache_file: Path, max_age_hours: int = 24) -> bool:
        """Check if cache file exists and is not expired"""
        if not cache_file.exists():
            return False

        file_age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
        return file_age < timedelta(hours=max_age_hours)

    def _cleanup_cache(self):
        """Remove old cache files if cache size exceeds limit"""
        try:
            total_size = sum(f.stat().st_size for f in self.cache_dir.rglob("*.cache"))
            total_size_mb = total_size / (1024 * 1024)

            if total_size_mb > self.max_cache_size_mb:
                logger.info(
                    f"Cache size {total_size_mb:.1f}MB exceeds limit {self.max_cache_size_mb}MB, cleaning up..."
                )

                # Get all cache files sorted by modification time (oldest first)
                cache_files = list(self.cache_dir.rglob("*.cache"))
                cache_files.sort(key=lambda f: f.stat().st_mtime)

                # Remove oldest files until we're under the limit
                removed_count = 0
                for cache_file in cache_files:
                    cache_file.unlink()
                    removed_count += 1

                    # Recalculate size
                    remaining_size = sum(
                        f.stat().st_size for f in self.cache_dir.rglob("*.cache")
                    )
                    if (
                        remaining_size / (1024 * 1024) <= self.max_cache_size_mb * 0.8
                    ):  # 80% of limit
                        break

                logger.info(f"Removed {removed_count} old cache files")

        except Exception as e:
            logger.warning(f"Cache cleanup failed: {e}")

    def cache_bpm_analysis(
        self, audio_hash: str, bpm_data: Dict[str, Any], max_age_hours: int = 168
    ):
        """Cache BPM analysis results (1 week default TTL)"""
        try:
            cache_key = self._generate_cache_key(audio_hash, "bpm")
            cache_file = self._get_cache_file_path(cache_key, "bpm")

            cache_data = {
                "timestamp": time.time(),
                "bpm_data": bpm_data,
                "audio_hash": audio_hash,
            }

            with open(cache_file, "wb") as f:
                pickle.dump(cache_data, f)

            logger.debug(f"Cached BPM analysis: {cache_key}")
            self._cleanup_cache()

        except Exception as e:
            logger.warning(f"Failed to cache BPM analysis: {e}")

    def get_cached_bpm_analysis(
        self, audio_hash: str, max_age_hours: int = 168
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached BPM analysis if available and valid"""
        try:
            cache_key = self._generate_cache_key(audio_hash, "bpm")
            cache_file = self._get_cache_file_path(cache_key, "bpm")

            if not self._is_cache_valid(cache_file, max_age_hours):
                self.cache_misses["bpm"] += 1
                return None

            with open(cache_file, "rb") as f:
                cache_data = pickle.load(f)

            # Verify the cached data matches the audio hash
            if cache_data.get("audio_hash") == audio_hash:
                self.cache_hits["bpm"] += 1
                logger.debug(f"BPM cache hit: {cache_key}")
                return cache_data["bpm_data"]
            else:
                self.cache_misses["bpm"] += 1
                return None

        except Exception as e:
            self.cache_misses["bpm"] += 1
            logger.debug(f"BPM cache miss: {e}")

        return None

    def cache_processed_audio(
        self,
        cache_key: str,
        audio_data: np.ndarray,
        sample_rate: int,
        processing_params: Dict,
        max_age_hours: int = 48,
    ):
        """Cache processed audio results (2 days default TTL)"""
        try:
            cache_file = self._get_cache_file_path(cache_key, "audio")

            cache_data = {
                "timestamp": time.time(),
                "audio_data": audio_data,
                "sample_rate": sample_rate,
                "processing_params": processing_params,
            }

            with open(cache_file, "wb") as f:
                pickle.dump(cache_data, f)

            logger.debug(f"Cached processed audio: {cache_key}")
            self._cleanup_cache()

        except Exception as e:
            logger.warning(f"Failed to cache processed audio: {e}")

    def get_cached_processed_audio(
        self, cache_key: str, max_age_hours: int = 48
    ) -> Optional[Dict[str, Any]]:
        """Retrieve cached processed audio if available and valid"""
        try:
            cache_file = self._get_cache_file_path(cache_key, "audio")

            if not self._is_cache_valid(cache_file, max_age_hours):
                self.cache_misses["audio"] += 1
                return None

            with open(cache_file, "rb") as f:
                cache_data = pickle.load(f)

            self.cache_hits["audio"] += 1
            logger.debug(f"Audio cache hit: {cache_key}")
            return cache_data

        except Exception as e:
            self.cache_misses["audio"] += 1
            logger.debug(f"Audio cache miss: {e}")

        return None

    def generate_audio_cache_key(self, audio_hash: str, processing_params: Dict) -> str:
        """Generate cache key for processed audio based on input audio and processing parameters"""
        # Create a deterministic key from audio hash and processing parameters
        key_data = {
            "audio_hash": audio_hash,
            "tempo_factor": processing_params.get("tempo_factor", 1.0),
            "pitch_shift_semitones": processing_params.get(
                "pitch_shift_semitones", 0.0
            ),
            "preserve_pitch": processing_params.get("preserve_pitch", False),
            "preset": processing_params.get("preset", "custom"),
            "add_reverb": processing_params.get("add_reverb", False),
            "stem_type": processing_params.get("stem_type", "full_mix"),
        }
        return self._generate_cache_key(key_data, "audio")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics for monitoring"""
        try:
            audio_files = list(self.audio_cache_dir.glob("*.cache"))
            bpm_files = list(self.bpm_cache_dir.glob("*.cache"))
            preset_files = list(self.preset_cache_dir.glob("*.cache"))

            total_size = sum(f.stat().st_size for f in self.cache_dir.rglob("*.cache"))

            # Calculate hit rates
            def calculate_hit_rate(cache_type: str) -> float:
                hits = self.cache_hits[cache_type]
                misses = self.cache_misses[cache_type]
                total = hits + misses
                return (hits / total * 100) if total > 0 else 0.0

            return {
                "total_files": len(audio_files) + len(bpm_files) + len(preset_files),
                "audio_cache_files": len(audio_files),
                "bpm_cache_files": len(bpm_files),
                "preset_cache_files": len(preset_files),
                "total_size_mb": total_size / (1024 * 1024),
                "cache_directory": str(self.cache_dir),
                "performance": {
                    "overall_hit_rate": (
                        calculate_hit_rate("audio")
                        if self.cache_hits["audio"] + self.cache_misses["audio"] > 0
                        else calculate_hit_rate("bpm")
                    ),
                    "audio_hit_rate": calculate_hit_rate("audio"),
                    "bpm_hit_rate": calculate_hit_rate("bpm"),
                    "preset_hit_rate": calculate_hit_rate("preset"),
                    "total_requests": {
                        "audio": self.cache_hits["audio"] + self.cache_misses["audio"],
                        "bpm": self.cache_hits["bpm"] + self.cache_misses["bpm"],
                        "preset": self.cache_hits["preset"]
                        + self.cache_misses["preset"],
                    },
                    "cache_hits": self.cache_hits.copy(),
                    "cache_misses": self.cache_misses.copy(),
                },
            }
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {"error": str(e)}


# Global cache instance
_performance_cache = None


def get_performance_cache() -> PerformanceCache:
    """Get or create the global performance cache instance"""
    global _performance_cache
    if _performance_cache is None:
        _performance_cache = PerformanceCache()
    return _performance_cache


def audio_hash(audio_data: Union[np.ndarray, bytes]) -> str:
    """Generate a hash for audio data to use as cache key"""
    if isinstance(audio_data, np.ndarray):
        # Use first and last few samples plus shape for hash (more efficient than full array)
        if len(audio_data) > 1000:
            sample_data = np.concatenate([audio_data[:500], audio_data[-500:]])
        else:
            sample_data = audio_data

        hash_input = f"{sample_data.tobytes()}_{audio_data.shape}_{audio_data.dtype}"
    else:
        # For bytes input
        hash_input = audio_data

    return hashlib.md5(
        hash_input if isinstance(hash_input, bytes) else hash_input.encode()
    ).hexdigest()


def cached_tempo_processing(cache_ttl_hours: int = 48):
    """
    Decorator to cache tempo processing results

    Args:
        cache_ttl_hours: Cache time-to-live in hours
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache = get_performance_cache()

            # Extract audio data and processing parameters
            audio_data = args[0] if args else kwargs.get("audio_data")
            if audio_data is None:
                # No audio data to cache, call function normally
                return func(*args, **kwargs)

            # Generate cache key
            audio_hash_key = audio_hash(audio_data)
            processing_params = {
                "tempo_factor": kwargs.get(
                    "tempo_factor", args[2] if len(args) > 2 else 1.0
                ),
                "pitch_shift_semitones": kwargs.get(
                    "pitch_shift_semitones", args[3] if len(args) > 3 else 0.0
                ),
                "preserve_pitch": kwargs.get(
                    "preserve_pitch", args[4] if len(args) > 4 else False
                ),
                "add_reverb": kwargs.get(
                    "add_reverb", args[5] if len(args) > 5 else False
                ),
                "preset": kwargs.get("preset", "custom"),
                "stem_type": kwargs.get("stem_type", "full_mix"),
            }

            cache_key = cache.generate_audio_cache_key(
                audio_hash_key, processing_params
            )

            # Check cache first
            cached_result = cache.get_cached_processed_audio(cache_key, cache_ttl_hours)
            if cached_result:
                logger.info(f"Cache hit for tempo processing: {cache_key[:8]}...")
                return cached_result["audio_data"]

            # Cache miss - compute result
            logger.debug(f"Cache miss for tempo processing: {cache_key[:8]}...")
            start_time = time.time()
            result = func(*args, **kwargs)
            processing_time = time.time() - start_time

            # Cache the result if processing took significant time
            if processing_time > 1.0 and isinstance(result, np.ndarray):
                sample_rate = (
                    args[1] if len(args) > 1 else kwargs.get("sample_rate", 44100)
                )
                cache.cache_processed_audio(
                    cache_key, result, sample_rate, processing_params, cache_ttl_hours
                )
                logger.info(
                    f"Cached tempo processing result (took {processing_time:.1f}s): {cache_key[:8]}..."
                )

            return result

        return wrapper

    return decorator


class PerformanceMonitor:
    """Monitor and track performance metrics for tempo processing"""

    def __init__(self):
        self.metrics = {
            "processing_times": [],
            "cache_hits": 0,
            "cache_misses": 0,
            "total_requests": 0,
            "error_count": 0,
            "preset_usage": {},
            "average_file_size_mb": 0,
        }
        self.start_time = time.time()

    def record_processing_time(
        self,
        processing_time: float,
        preset: str = "custom",
        file_size_mb: float = 0,
        cache_hit: bool = False,
    ):
        """Record processing time and related metrics"""
        self.metrics["processing_times"].append(processing_time)
        self.metrics["total_requests"] += 1

        if cache_hit:
            self.metrics["cache_hits"] += 1
        else:
            self.metrics["cache_misses"] += 1

        # Track preset usage
        self.metrics["preset_usage"][preset] = (
            self.metrics["preset_usage"].get(preset, 0) + 1
        )

        # Update average file size
        if file_size_mb > 0:
            current_avg = self.metrics["average_file_size_mb"]
            total_requests = self.metrics["total_requests"]
            self.metrics["average_file_size_mb"] = (
                (current_avg * (total_requests - 1)) + file_size_mb
            ) / total_requests

    def record_error(self):
        """Record an error occurrence"""
        self.metrics["error_count"] += 1

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        processing_times = self.metrics["processing_times"]
        total_requests = self.metrics["total_requests"]

        if not processing_times:
            return {"message": "No processing data available"}

        cache_hit_rate = (
            (self.metrics["cache_hits"] / total_requests * 100)
            if total_requests > 0
            else 0
        )
        error_rate = (
            (self.metrics["error_count"] / total_requests * 100)
            if total_requests > 0
            else 0
        )

        return {
            "uptime_seconds": time.time() - self.start_time,
            "total_requests": total_requests,
            "cache_hit_rate_percent": round(cache_hit_rate, 2),
            "error_rate_percent": round(error_rate, 2),
            "processing_times": {
                "average_seconds": round(np.mean(processing_times), 2),
                "median_seconds": round(np.median(processing_times), 2),
                "min_seconds": round(min(processing_times), 2),
                "max_seconds": round(max(processing_times), 2),
                "p95_seconds": round(np.percentile(processing_times, 95), 2),
            },
            "preset_usage": self.metrics["preset_usage"],
            "average_file_size_mb": round(self.metrics["average_file_size_mb"], 2),
        }


# Global performance monitor
_performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance"""
    return _performance_monitor
