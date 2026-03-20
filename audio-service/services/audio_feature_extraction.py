"""
Advanced Audio Feature Extraction Service using Librosa

Provides comprehensive audio analysis with efficient processing and structured output
optimized for API consumption without large dataset transfers.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from enum import Enum
from io import BytesIO
import logging
from pathlib import Path
import signal
import time
from typing import Any, Dict, List, Optional, Tuple, Union

import librosa
import numpy as np
import soundfile as sf

from config import settings

logger = logging.getLogger(__name__)


class AudioFormat(Enum):
    """Supported audio formats"""

    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    M4A = "m4a"
    OGG = "ogg"
    AIFF = "aiff"
    WMA = "wma"


@dataclass
class AudioMetadata:
    """Audio file metadata"""

    filename: str
    duration: float
    sample_rate: int
    channels: int
    format: str
    bitrate: Optional[int] = None
    file_size: Optional[int] = None


@dataclass
class FeatureExtractionConfig:
    """Configuration for feature extraction"""

    chunk_duration: float = 30.0  # Process in 30-second chunks
    hop_length: int = 512
    n_fft: int = 2048  # FFT window size - will be dynamically adjusted
    n_mfcc: int = 13
    n_mels: int = 128
    n_chroma: int = 12
    max_processing_time: int = 300  # 5 minutes timeout
    target_sr: Optional[int] = 22050
    extract_detailed_features: bool = False  # For API optimization


class AudioProcessingError(Exception):
    """Base exception for audio processing errors"""

    pass


class UnsupportedFormatError(AudioProcessingError):
    """Raised when audio format is not supported"""

    pass


class CorruptedFileError(AudioProcessingError):
    """Raised when audio file is corrupted or unreadable"""

    pass


class ProcessingTimeoutError(AudioProcessingError):
    """Raised when processing exceeds time limit"""

    pass


class MemoryLimitError(AudioProcessingError):
    """Raised when processing would exceed memory limits"""

    pass


@contextmanager
def timeout_context(seconds: int):
    """Context manager for processing timeout"""

    def timeout_handler(signum, frame):
        raise ProcessingTimeoutError(f"Processing timeout after {seconds} seconds")

    # Set the signal handler
    old_handler = signal.signal(signal.SIGALRM, timeout_handler)
    signal.alarm(seconds)

    try:
        yield
    finally:
        # Restore the old handler
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)


class AudioFeatureExtractor:
    """
    Advanced audio feature extraction service optimized for API consumption
    """

    def __init__(self, config: Optional[FeatureExtractionConfig] = None):
        self.config = config or FeatureExtractionConfig()
        self.supported_formats = {fmt.value for fmt in AudioFormat}

    def _get_optimal_n_fft(self, y: np.ndarray) -> int:
        """Calculate optimal FFT size based on audio length"""
        # Ensure n_fft is not larger than audio length and is a power of 2
        max_n_fft = len(y)
        n_fft = min(self.config.n_fft, max_n_fft)

        # Find the largest power of 2 that's <= n_fft and >= hop_length * 4
        min_n_fft = self.config.hop_length * 4  # Minimum for good frequency resolution

        if n_fft < min_n_fft:
            # For very short signals, use the largest power of 2 possible
            n_fft = 2 ** int(np.log2(max_n_fft)) if max_n_fft >= 32 else 32
        else:
            # Find largest power of 2 <= n_fft
            n_fft = 2 ** int(np.log2(n_fft))

        return max(32, min(n_fft, max_n_fft))  # Ensure reasonable bounds

    def load_audio(
        self, source: Union[str, Path, BytesIO], sr: Optional[int] = None
    ) -> Tuple[np.ndarray, int, AudioMetadata]:
        """
        Load audio from file path or BytesIO object

        Args:
            source: File path, Path object, or BytesIO object
            sr: Target sample rate (None for original)

        Returns:
            Tuple of (audio_data, sample_rate, metadata)
        """
        try:
            if isinstance(source, (str, Path)):
                return self._load_from_path(source, sr)
            elif isinstance(source, BytesIO):
                return self._load_from_bytes(source, sr)
            else:
                raise AudioProcessingError(f"Unsupported source type: {type(source)}")

        except Exception as e:
            if isinstance(e, AudioProcessingError):
                raise
            raise CorruptedFileError(f"Failed to load audio: {str(e)}")

    def _load_from_path(
        self, file_path: Union[str, Path], sr: Optional[int]
    ) -> Tuple[np.ndarray, int, AudioMetadata]:
        """Load audio from file path"""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {file_path}")

        # Check format
        file_format = file_path.suffix.lower().lstrip(".")
        if file_format not in self.supported_formats:
            raise UnsupportedFormatError(f"Unsupported format: {file_format}")

        # Check file size (prevent memory issues)
        file_size = file_path.stat().st_size
        max_size = settings.MAX_FILE_SIZE
        if file_size > max_size:
            raise MemoryLimitError(
                f"File too large: {file_size} bytes > {max_size} bytes"
            )

        # Load audio
        target_sr = sr or self.config.target_sr
        y, sample_rate = librosa.load(str(file_path), sr=target_sr, mono=True)

        # Get metadata
        sf.info(str(file_path))
        metadata = AudioMetadata(
            filename=file_path.name,
            duration=len(y) / sample_rate,
            sample_rate=sample_rate,
            channels=1,  # Converted to mono
            format=file_format,
            file_size=file_size,
        )

        return y, sample_rate, metadata

    def _load_from_bytes(
        self, audio_bytes: BytesIO, sr: Optional[int]
    ) -> Tuple[np.ndarray, int, AudioMetadata]:
        """Load audio from BytesIO object"""
        audio_bytes.seek(0)

        # Check size
        audio_bytes.seek(0, 2)  # Seek to end
        size = audio_bytes.tell()
        audio_bytes.seek(0)  # Reset

        max_size = settings.MAX_FILE_SIZE
        if size > max_size:
            raise MemoryLimitError(
                f"Audio data too large: {size} bytes > {max_size} bytes"
            )

        try:
            target_sr = sr or self.config.target_sr
            y, sample_rate = librosa.load(audio_bytes, sr=target_sr, mono=True)

            metadata = AudioMetadata(
                filename="uploaded_audio",
                duration=len(y) / sample_rate,
                sample_rate=sample_rate,
                channels=1,
                format="unknown",
                file_size=size,
            )

            return y, sample_rate, metadata

        except Exception as e:
            raise CorruptedFileError(f"Failed to decode audio data: {str(e)}")

    def extract_musical_key(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract musical key using chroma features"""
        try:
            # Use optimal n_fft size to prevent warnings
            n_fft = self._get_optimal_n_fft(y)

            # Extract chroma features - using chroma_stft instead of chroma_cqt for n_fft compatibility
            chroma = librosa.feature.chroma_stft(
                y=y, sr=sr, hop_length=self.config.hop_length, n_fft=n_fft
            )

            # Calculate chroma mean for key detection
            chroma_mean = np.mean(chroma, axis=1)

            # Key profiles (Krumhansl-Schmuckler)
            major_profile = np.array(
                [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
            )
            minor_profile = np.array(
                [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
            )

            # Normalize profiles
            major_profile = major_profile / np.sum(major_profile)
            minor_profile = minor_profile / np.sum(minor_profile)

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

            # Calculate correlations
            major_correlations = []
            minor_correlations = []

            for i in range(12):
                major_corr = np.corrcoef(chroma_mean, np.roll(major_profile, i))[0, 1]
                minor_corr = np.corrcoef(chroma_mean, np.roll(minor_profile, i))[0, 1]
                major_correlations.append(major_corr)
                minor_correlations.append(minor_corr)

            # Find best matches
            best_major_idx = np.argmax(major_correlations)
            best_minor_idx = np.argmax(minor_correlations)

            best_major_corr = major_correlations[best_major_idx]
            best_minor_corr = minor_correlations[best_minor_idx]

            # Determine key
            if best_major_corr > best_minor_corr:
                key = f"{key_names[best_major_idx]} major"
                confidence = float(best_major_corr)
            else:
                key = f"{key_names[best_minor_idx]} minor"
                confidence = float(best_minor_corr)

            return {
                "key": key,
                "confidence": confidence,
                "major_correlations": [float(c) for c in major_correlations],
                "minor_correlations": [float(c) for c in minor_correlations],
            }

        except Exception as e:
            logger.warning(f"Key extraction failed: {e}")
            return {"key": "unknown", "confidence": 0.0, "error": str(e)}

    def extract_bpm(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Calculate BPM using beat tracking with enhanced fallback"""
        try:
            # First try standard method
            tempo, beats = librosa.beat.beat_track(
                y=y, sr=sr, hop_length=self.config.hop_length
            )

            # Calculate beat intervals
            beat_times = librosa.frames_to_time(
                beats, sr=sr, hop_length=self.config.hop_length
            )

            if len(beat_times) > 1:
                intervals = np.diff(beat_times)
                avg_interval = np.mean(intervals)
                interval_std = np.std(intervals)

                # Calculate confidence based on regularity
                confidence = (
                    max(0.0, 1.0 - (interval_std / avg_interval))
                    if avg_interval > 0
                    else 0.0
                )
            else:
                intervals = []
                avg_interval = 0.0
                interval_std = 0.0
                confidence = 0.0

            # If confidence is low or tempo seems wrong, use enhanced method
            if confidence < 0.6 or tempo < 30 or tempo > 300:
                logger.debug(
                    f"Low confidence BPM ({confidence:.2f}) or suspicious tempo ({tempo:.1f}), using enhanced method"
                )
                enhanced_result = self.extract_bpm_enhanced(y, sr)
                if (
                    "error" not in enhanced_result
                    and enhanced_result.get("confidence", 0) > confidence
                ):
                    # Use enhanced result but maintain backward compatibility
                    return {
                        "bpm": enhanced_result["bpm"],
                        "beat_count": enhanced_result["beat_count"],
                        "avg_beat_interval": enhanced_result["avg_beat_interval"],
                        "beat_regularity": enhanced_result["beat_regularity"],
                        "beat_times": enhanced_result["beat_times"],
                    }

            return {
                "bpm": (
                    float(tempo)
                    if np.isscalar(tempo)
                    else float(tempo[0]) if len(tempo) > 0 else 0.0
                ),
                "beat_count": len(beats),
                "avg_beat_interval": float(avg_interval),
                "beat_regularity": float(confidence),
                "beat_times": [
                    float(t) for t in beat_times[:20]
                ],  # Limit to first 20 beats
            }

        except Exception as e:
            logger.warning(f"BPM extraction failed, trying enhanced method: {e}")
            # Fallback to enhanced method
            try:
                enhanced_result = self.extract_bpm_enhanced(y, sr)
                if "error" not in enhanced_result:
                    return {
                        "bpm": enhanced_result["bpm"],
                        "beat_count": enhanced_result["beat_count"],
                        "avg_beat_interval": enhanced_result.get(
                            "avg_beat_interval", 0.0
                        ),
                        "beat_regularity": enhanced_result.get("beat_regularity", 0.0),
                        "beat_times": enhanced_result.get("beat_times", []),
                    }
            except Exception as e2:
                logger.warning(f"Enhanced BPM extraction also failed: {e2}")

            return {"bpm": 0.0, "beat_count": 0, "error": str(e)}

    def _detect_tempo_doubling_halving(self, tempos: List[float]) -> List[float]:
        """Detect and correct tempo doubling/halving issues"""
        if not tempos:
            return []

        corrected_tempos = []

        for tempo in tempos:
            if tempo <= 0:
                continue

            # Generate candidates for tempo doubling/halving correction
            candidates = [tempo, tempo * 2, tempo / 2]

            # For very fast or slow tempos, add more extreme corrections
            if tempo < 60:
                candidates.extend([tempo * 4])
            elif tempo > 240:
                candidates.extend([tempo / 4])

            # Keep only reasonable BPM values (30-300)
            valid_candidates = [t for t in candidates if 30 <= t <= 300]

            if valid_candidates:
                # Prefer tempos in the common range (60-200)
                preferred = [t for t in valid_candidates if 60 <= t <= 200]
                if preferred:
                    # Add just the original tempo, not all preferred variants
                    corrected_tempos.append(tempo)
                else:
                    corrected_tempos.append(valid_candidates[0])
            else:
                if 30 <= tempo <= 300:  # Keep reasonable tempos as-is
                    corrected_tempos.append(tempo)

        return corrected_tempos

    def _ensemble_tempo_selection(
        self, tempos: List[float], weights: List[float] = None
    ) -> float:
        """Select final tempo from multiple estimates using ensemble method"""
        if not tempos or all(t == 0 for t in tempos):
            return 0.0

        # Filter out zero/invalid tempos
        valid_tempos = [t for t in tempos if t > 0]
        if not valid_tempos:
            return 0.0

        if weights is None:
            weights = [1.0] * len(valid_tempos)
        else:
            # Only use weights for valid tempos
            weights = [w for t, w in zip(tempos, weights) if t > 0]

        # Apply tempo doubling/halving correction
        corrected_tempos = self._detect_tempo_doubling_halving(valid_tempos)

        # Weighted average with outlier rejection
        if len(corrected_tempos) >= 3:
            # Remove outliers (values > 2 standard deviations from mean)
            mean_tempo = np.mean(corrected_tempos)
            std_tempo = np.std(corrected_tempos)

            if std_tempo > 0:
                filtered_tempos = [
                    t for t in corrected_tempos if abs(t - mean_tempo) <= 2 * std_tempo
                ]
                if filtered_tempos:
                    corrected_tempos = filtered_tempos

        # Weighted average
        total_weight = sum(weights[: len(corrected_tempos)])
        if total_weight > 0:
            weighted_tempo = sum(
                t * w
                for t, w in zip(corrected_tempos, weights[: len(corrected_tempos)])
            )
            return weighted_tempo / total_weight
        else:
            return np.mean(corrected_tempos)

    def _calculate_tempo_confidence(
        self, tempos: List[float], final_tempo: float
    ) -> float:
        """Calculate confidence score for tempo estimation"""
        if not tempos or final_tempo == 0:
            return 0.0

        valid_tempos = [t for t in tempos if t > 0]
        if not valid_tempos:
            return 0.0

        # Calculate how well the algorithms agree
        # Apply tempo doubling/halving correction for comparison
        corrected_tempos = self._detect_tempo_doubling_halving(valid_tempos)

        # Check agreement within ±5% tolerance
        tolerance = final_tempo * 0.05
        agreeing_tempos = [
            t for t in corrected_tempos if abs(t - final_tempo) <= tolerance
        ]

        agreement_ratio = len(agreeing_tempos) / len(corrected_tempos)

        # Boost confidence for tempos in common ranges
        range_boost = 1.0
        if 80 <= final_tempo <= 160:  # Common pop/rock range
            range_boost = 1.1
        elif 60 <= final_tempo <= 200:  # Extended common range
            range_boost = 1.05

        confidence = min(1.0, agreement_ratio * range_boost)
        return float(confidence)

    def extract_bpm_enhanced(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Enhanced BPM detection using multiple algorithms"""
        try:
            tempos = []
            confidences = []
            beats_list = []

            # Method 1: Standard beat tracking
            try:
                tempo1, beats1 = librosa.beat.beat_track(
                    y=y, sr=sr, hop_length=self.config.hop_length
                )
                # Handle both scalar and array returns from librosa
                tempo1 = (
                    float(tempo1)
                    if np.isscalar(tempo1)
                    else float(tempo1[0]) if len(tempo1) > 0 else 0.0
                )
                tempos.append(tempo1)
                beats_list.append(beats1)
                confidences.append(0.8)  # Base confidence for standard method
            except Exception as e:
                logger.debug(f"Standard beat tracking failed: {e}")
                tempos.append(0.0)
                confidences.append(0.0)

            # Method 2: Harmonic-percussive separation + percussive BPM
            try:
                y_harmonic, y_percussive = librosa.effects.hpss(y)
                tempo2, beats2 = librosa.beat.beat_track(
                    y=y_percussive, sr=sr, hop_length=self.config.hop_length
                )
                # Handle both scalar and array returns from librosa
                tempo2 = (
                    float(tempo2)
                    if np.isscalar(tempo2)
                    else float(tempo2[0]) if len(tempo2) > 0 else 0.0
                )
                tempos.append(tempo2)
                beats_list.append(beats2)
                confidences.append(0.9)  # Higher confidence for percussive-only
            except Exception as e:
                logger.debug(f"Harmonic-percussive separation BPM failed: {e}")
                tempos.append(0.0)
                confidences.append(0.0)

            # Method 3: Onset-based tempo estimation
            try:
                onset_envelope = librosa.onset.onset_strength(y=y, sr=sr)
                # Use newer librosa API
                try:
                    tempo3_result = librosa.feature.rhythm.tempo(
                        onset_envelope=onset_envelope
                    )
                except AttributeError:
                    # Fallback to older API
                    tempo3_result = librosa.beat.tempo(onset_envelope=onset_envelope)
                tempo3 = float(tempo3_result[0]) if len(tempo3_result) > 0 else 0.0
                tempos.append(tempo3)
                confidences.append(0.7)  # Moderate confidence
            except Exception as e:
                logger.debug(f"Onset-based tempo estimation failed: {e}")
                tempos.append(0.0)
                confidences.append(0.0)

            # Method 4: Tempogram-based analysis
            try:
                tempogram = librosa.feature.tempogram(
                    y=y, sr=sr, hop_length=self.config.hop_length
                )
                try:
                    tempo4_result = librosa.feature.rhythm.tempo(tempogram=tempogram)
                except AttributeError:
                    # Fallback to older API
                    tempo4_result = librosa.beat.tempo(tempogram=tempogram)
                tempo4 = float(tempo4_result[0]) if len(tempo4_result) > 0 else 0.0
                tempos.append(tempo4)
                confidences.append(0.6)  # Lower confidence, more experimental
            except Exception as e:
                logger.debug(f"Tempogram-based tempo estimation failed: {e}")
                tempos.append(0.0)
                confidences.append(0.0)

            # Ensemble decision
            final_bpm = self._ensemble_tempo_selection(tempos, confidences)
            overall_confidence = self._calculate_tempo_confidence(tempos, final_bpm)

            # Use the best beat tracking result for additional metrics
            best_beats = None
            if beats_list:
                # Find beats from method with tempo closest to final BPM
                best_method_idx = 0
                min_diff = float("inf")
                for i, tempo in enumerate(tempos[: len(beats_list)]):
                    if tempo > 0:
                        diff = abs(tempo - final_bpm)
                        if diff < min_diff:
                            min_diff = diff
                            best_method_idx = i

                if best_method_idx < len(beats_list):
                    best_beats = beats_list[best_method_idx]

            # Calculate additional metrics
            if best_beats is not None and len(best_beats) > 1:
                beat_times = librosa.frames_to_time(
                    best_beats, sr=sr, hop_length=self.config.hop_length
                )
                intervals = np.diff(beat_times)
                avg_interval = np.mean(intervals)
                interval_std = np.std(intervals)
                beat_regularity = (
                    max(0.0, 1.0 - (interval_std / avg_interval))
                    if avg_interval > 0
                    else 0.0
                )
                beat_count = len(best_beats)
                beat_times_list = [float(t) for t in beat_times[:20]]
            else:
                avg_interval = 60.0 / final_bpm if final_bpm > 0 else 0.0
                interval_std = 0.0
                beat_regularity = overall_confidence
                beat_count = 0
                beat_times_list = []

            # Find alternative tempos
            alternative_tempos = []
            for tempo in tempos:
                if (
                    tempo > 0 and abs(tempo - final_bpm) > final_bpm * 0.1
                ):  # More than 10% different
                    alternative_tempos.append(tempo)

            # Remove duplicates and limit
            alternative_tempos = list(set([round(t, 1) for t in alternative_tempos]))[
                :3
            ]

            return {
                "bpm": float(final_bpm),
                "confidence": float(overall_confidence),
                "beat_count": int(beat_count),
                "avg_beat_interval": float(avg_interval),
                "beat_regularity": float(beat_regularity),
                "beat_times": beat_times_list,
                "method_results": {
                    "standard": tempos[0] if len(tempos) > 0 else 0.0,
                    "percussive": tempos[1] if len(tempos) > 1 else 0.0,
                    "onset_based": tempos[2] if len(tempos) > 2 else 0.0,
                    "tempogram": tempos[3] if len(tempos) > 3 else 0.0,
                },
                "alternative_tempos": alternative_tempos,
            }

        except Exception as e:
            logger.warning(f"Enhanced BPM extraction failed: {e}")
            return {"bpm": 0.0, "beat_count": 0, "confidence": 0.0, "error": str(e)}

    def extract_spectral_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract spectral features (centroid, rolloff, bandwidth)"""
        try:
            # Use optimal n_fft size to prevent warnings
            n_fft = self._get_optimal_n_fft(y)

            # Spectral centroid
            spectral_centroid = librosa.feature.spectral_centroid(
                y=y, sr=sr, hop_length=self.config.hop_length, n_fft=n_fft
            )[0]

            # Spectral rolloff
            spectral_rolloff = librosa.feature.spectral_rolloff(
                y=y,
                sr=sr,
                hop_length=self.config.hop_length,
                n_fft=n_fft,
                roll_percent=0.85,
            )[0]

            # Spectral bandwidth
            spectral_bandwidth = librosa.feature.spectral_bandwidth(
                y=y, sr=sr, hop_length=self.config.hop_length, n_fft=n_fft
            )[0]

            return {
                "spectral_centroid": {
                    "mean": float(np.mean(spectral_centroid)),
                    "std": float(np.std(spectral_centroid)),
                    "min": float(np.min(spectral_centroid)),
                    "max": float(np.max(spectral_centroid)),
                },
                "spectral_rolloff": {
                    "mean": float(np.mean(spectral_rolloff)),
                    "std": float(np.std(spectral_rolloff)),
                    "min": float(np.min(spectral_rolloff)),
                    "max": float(np.max(spectral_rolloff)),
                },
                "spectral_bandwidth": {
                    "mean": float(np.mean(spectral_bandwidth)),
                    "std": float(np.std(spectral_bandwidth)),
                    "min": float(np.min(spectral_bandwidth)),
                    "max": float(np.max(spectral_bandwidth)),
                },
            }

        except Exception as e:
            logger.warning(f"Spectral features extraction failed: {e}")
            return {"error": str(e)}

    def extract_mfcc(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract MFCC features"""
        try:
            # Use optimal n_fft size to prevent warnings
            n_fft = self._get_optimal_n_fft(y)

            mfcc = librosa.feature.mfcc(
                y=y,
                sr=sr,
                n_mfcc=self.config.n_mfcc,
                hop_length=self.config.hop_length,
                n_mels=self.config.n_mels,
                n_fft=n_fft,
            )

            # Calculate statistics for each coefficient
            mfcc_stats = []
            for i in range(mfcc.shape[0]):
                coeff = mfcc[i]
                mfcc_stats.append(
                    {
                        "mean": float(np.mean(coeff)),
                        "std": float(np.std(coeff)),
                        "min": float(np.min(coeff)),
                        "max": float(np.max(coeff)),
                    }
                )

            return {
                "n_coefficients": mfcc.shape[0],
                "coefficients": mfcc_stats,
                "overall_mean": float(np.mean(mfcc)),
                "overall_std": float(np.std(mfcc)),
            }

        except Exception as e:
            logger.warning(f"MFCC extraction failed: {e}")
            return {"error": str(e)}

    def extract_zero_crossing_rate(self, y: np.ndarray) -> Dict[str, Any]:
        """Extract zero crossing rate"""
        try:
            zcr = librosa.feature.zero_crossing_rate(
                y=y, hop_length=self.config.hop_length
            )[0]

            return {
                "mean": float(np.mean(zcr)),
                "std": float(np.std(zcr)),
                "min": float(np.min(zcr)),
                "max": float(np.max(zcr)),
            }

        except Exception as e:
            logger.warning(f"ZCR extraction failed: {e}")
            return {"error": str(e)}

    def extract_energy_features(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Calculate loudness and RMS energy"""
        try:
            # Use optimal n_fft size to prevent warnings
            n_fft = self._get_optimal_n_fft(y)

            # RMS Energy
            rms = librosa.feature.rms(
                y=y, hop_length=self.config.hop_length, frame_length=n_fft
            )[0]

            # Loudness (using RMS in dB)
            rms_db = librosa.amplitude_to_db(rms, ref=np.max)

            # Overall loudness metrics
            overall_rms = np.sqrt(np.mean(y**2))
            overall_loudness_db = float(
                librosa.amplitude_to_db([overall_rms], ref=1.0)[0]
            )

            # Dynamic range
            dynamic_range = float(np.max(rms_db) - np.min(rms_db))

            return {
                "rms_energy": {
                    "mean": float(np.mean(rms)),
                    "std": float(np.std(rms)),
                    "min": float(np.min(rms)),
                    "max": float(np.max(rms)),
                },
                "loudness_db": {
                    "mean": float(np.mean(rms_db)),
                    "std": float(np.std(rms_db)),
                    "min": float(np.min(rms_db)),
                    "max": float(np.max(rms_db)),
                },
                "overall_loudness_db": overall_loudness_db,
                "overall_rms": float(overall_rms),
                "dynamic_range_db": dynamic_range,
            }

        except Exception as e:
            logger.warning(f"Energy features extraction failed: {e}")
            return {"error": str(e)}

    def process_in_chunks(
        self, y: np.ndarray, sr: int, metadata: AudioMetadata
    ) -> List[Dict[str, Any]]:
        """Process large audio files in chunks"""
        chunk_samples = int(self.config.chunk_duration * sr)
        chunks = []

        num_chunks = len(y) // chunk_samples + (1 if len(y) % chunk_samples else 0)

        for i in range(num_chunks):
            start_idx = i * chunk_samples
            end_idx = min((i + 1) * chunk_samples, len(y))
            chunk = y[start_idx:end_idx]

            start_time = start_idx / sr
            end_time = end_idx / sr

            # Extract features for this chunk
            chunk_features = self.extract_features_from_audio(chunk, sr)
            chunk_features["chunk_info"] = {
                "chunk_index": i,
                "start_time": start_time,
                "end_time": end_time,
                "duration": end_time - start_time,
            }

            chunks.append(chunk_features)

        return chunks

    def extract_features_from_audio(self, y: np.ndarray, sr: int) -> Dict[str, Any]:
        """Extract all features from loaded audio data"""
        features = {}

        try:
            # Musical analysis
            features["key"] = self.extract_musical_key(y, sr)
            features["tempo"] = self.extract_bpm(y, sr)

            # Spectral features
            features["spectral"] = self.extract_spectral_features(y, sr)

            # MFCC features
            features["mfcc"] = self.extract_mfcc(y, sr)

            # Zero crossing rate
            features["zero_crossing_rate"] = self.extract_zero_crossing_rate(y)

            # Energy features
            features["energy"] = self.extract_energy_features(y, sr)

            # Additional summary statistics
            features["audio_statistics"] = {
                "length_samples": int(len(y)),
                "max_amplitude": float(np.max(np.abs(y))),
                "mean_amplitude": float(np.mean(np.abs(y))),
                "std_amplitude": float(np.std(y)),
                "zero_crossings_total": int(np.sum(np.abs(np.diff(np.sign(y)))) / 2),
            }

        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            features["extraction_error"] = str(e)

        return features

    def extract_features(
        self,
        source: Union[str, Path, BytesIO],
        sr: Optional[int] = None,
        process_chunks: bool = None,
    ) -> Dict[str, Any]:
        """
        Main feature extraction method with comprehensive error handling

        Args:
            source: Audio file path or BytesIO object
            sr: Target sample rate
            process_chunks: Whether to process in chunks (auto-detect if None)

        Returns:
            Dictionary with extracted features and metadata
        """
        start_time = time.time()

        try:
            with timeout_context(self.config.max_processing_time):
                # Load audio
                y, sample_rate, metadata = self.load_audio(source, sr)

                # Auto-decide chunking based on duration
                if process_chunks is None:
                    process_chunks = metadata.duration > self.config.chunk_duration * 2

                logger.info(
                    f"Processing audio: {metadata.filename}, "
                    f"duration: {metadata.duration:.2f}s, "
                    f"chunks: {process_chunks}"
                )

                # Build result
                result = {
                    "metadata": {
                        "filename": metadata.filename,
                        "duration": metadata.duration,
                        "sample_rate": sample_rate,
                        "format": metadata.format,
                        "file_size": metadata.file_size,
                        "processed_in_chunks": process_chunks,
                        "processing_time": None,  # Will be set at the end
                    }
                }

                if process_chunks:
                    # Process in chunks
                    chunk_features = self.process_in_chunks(y, sample_rate, metadata)
                    result["chunks"] = chunk_features
                    result["chunk_count"] = len(chunk_features)

                    # Aggregate features from chunks (optional)
                    if chunk_features:
                        result["aggregated_features"] = self._aggregate_chunk_features(
                            chunk_features
                        )
                else:
                    # Process entire file
                    result["features"] = self.extract_features_from_audio(
                        y, sample_rate
                    )

                # Set processing time
                processing_time = time.time() - start_time
                result["metadata"]["processing_time"] = processing_time

                logger.info(f"Feature extraction completed in {processing_time:.2f}s")
                return result

        except Exception as e:
            processing_time = time.time() - start_time

            error_result = {
                "error": {
                    "type": type(e).__name__,
                    "message": str(e),
                    "processing_time": processing_time,
                },
                "metadata": {
                    "filename": getattr(e, "filename", "unknown"),
                    "processing_time": processing_time,
                },
            }

            logger.error(f"Feature extraction failed: {e}")
            return error_result

    def _aggregate_chunk_features(
        self, chunk_features: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Aggregate features from multiple chunks"""
        if not chunk_features:
            return {}

        aggregated = {}

        # Aggregate tempo/BPM
        bpms = [
            chunk["tempo"]["bpm"]
            for chunk in chunk_features
            if "tempo" in chunk and "bpm" in chunk["tempo"]
        ]
        if bpms:
            aggregated["tempo"] = {
                "mean_bpm": float(np.mean(bpms)),
                "std_bpm": float(np.std(bpms)),
                "bpm_range": [float(np.min(bpms)), float(np.max(bpms))],
            }

        # Aggregate keys (most common)
        keys = [
            chunk["key"]["key"]
            for chunk in chunk_features
            if "key" in chunk and "key" in chunk["key"]
        ]
        if keys:
            from collections import Counter

            key_counts = Counter(keys)
            most_common_key = key_counts.most_common(1)[0]
            aggregated["key"] = {
                "most_likely_key": most_common_key[0],
                "confidence": most_common_key[1] / len(keys),
                "key_changes": len(set(keys)),
            }

        # Aggregate energy features
        overall_loudness = [
            chunk["energy"]["overall_loudness_db"]
            for chunk in chunk_features
            if "energy" in chunk and "overall_loudness_db" in chunk["energy"]
        ]
        if overall_loudness:
            aggregated["energy"] = {
                "mean_loudness_db": float(np.mean(overall_loudness)),
                "std_loudness_db": float(np.std(overall_loudness)),
                "loudness_range_db": [
                    float(np.min(overall_loudness)),
                    float(np.max(overall_loudness)),
                ],
            }

        # Aggregate spectral features (brightness)
        brightness_values = [
            chunk["spectral"]["spectral_centroid"]["mean"]
            for chunk in chunk_features
            if "spectral" in chunk
            and "spectral_centroid" in chunk["spectral"]
            and "mean" in chunk["spectral"]["spectral_centroid"]
        ]
        if brightness_values:
            aggregated["spectral"] = {
                "mean_brightness": float(np.mean(brightness_values)),
                "std_brightness": float(np.std(brightness_values)),
                "brightness_range": [
                    float(np.min(brightness_values)),
                    float(np.max(brightness_values)),
                ],
            }

        return aggregated


# Factory function for easy usage
def create_feature_extractor(
    extract_detailed: bool = False, chunk_duration: float = 30.0, timeout: int = 300
) -> AudioFeatureExtractor:
    """
    Create a feature extractor with specified configuration

    Args:
        extract_detailed: Whether to extract detailed features (impacts performance)
        chunk_duration: Duration of chunks for large files
        timeout: Processing timeout in seconds
    """
    config = FeatureExtractionConfig(
        extract_detailed_features=extract_detailed,
        chunk_duration=chunk_duration,
        max_processing_time=timeout,
    )
    return AudioFeatureExtractor(config)
