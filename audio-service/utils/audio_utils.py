import os
import tempfile
import librosa
import numpy as np
from typing import Tuple, Optional
import soundfile as sf
import io
from config import settings


def load_audio_from_bytes(
    audio_data: bytes, sr: Optional[int] = None, mono: bool = True
) -> Tuple[np.ndarray, int]:
    """
    Load audio from byte data

    Args:
        audio_data: Audio file as bytes
        sr: Target sample rate
        mono: Whether to convert to mono (default True for compatibility)

    Returns:
        Tuple of (audio_array, sample_rate)
    """
    try:
        # Create a temporary file to load the audio
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            tmp_file.write(audio_data)
            tmp_file.flush()

            # Load audio using librosa with mono option
            y, sr_orig = librosa.load(tmp_file.name, sr=sr, mono=mono)

            # Clean up temporary file
            os.unlink(tmp_file.name)

            return y, sr_orig if sr is None else sr

    except Exception as e:
        raise ValueError(f"Could not load audio from bytes: {str(e)}")


def save_audio_file(audio_array: np.ndarray, sample_rate: int, output_path: str) -> str:
    """
    Save audio array to file

    Args:
        audio_array: Audio data as numpy array
        sample_rate: Sample rate
        output_path: Output file path

    Returns:
        Path to saved file
    """
    try:
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save using soundfile
        sf.write(output_path, audio_array, sample_rate)

        return output_path

    except Exception as e:
        raise ValueError(f"Could not save audio file: {str(e)}")


def validate_audio_format(filename: str) -> bool:
    """
    Validate if audio format is supported

    Args:
        filename: Name of the audio file

    Returns:
        True if format is supported
    """
    file_ext = filename.lower().split(".")[-1]
    return file_ext in settings.SUPPORTED_FORMATS


def get_audio_duration(audio_data: bytes) -> float:
    """
    Get duration of audio in seconds

    Args:
        audio_data: Audio file as bytes

    Returns:
        Duration in seconds
    """
    try:
        y, sr = load_audio_from_bytes(audio_data)
        return len(y) / sr

    except Exception as e:
        raise ValueError(f"Could not get audio duration: {str(e)}")


def normalize_audio(audio_array: np.ndarray, target_db: float = -20.0) -> np.ndarray:
    """
    Normalize audio to target dB level

    Args:
        audio_array: Input audio array
        target_db: Target dB level

    Returns:
        Normalized audio array
    """
    try:
        # Calculate RMS
        rms = np.sqrt(np.mean(audio_array**2))

        if rms == 0:
            return audio_array

        # Convert target dB to linear scale
        target_linear = 10 ** (target_db / 20.0)

        # Calculate scaling factor
        scale_factor = target_linear / rms

        # Apply scaling
        normalized_audio = audio_array * scale_factor

        # Prevent clipping
        max_val = np.max(np.abs(normalized_audio))
        if max_val > 1.0:
            normalized_audio = normalized_audio / max_val

        return normalized_audio

    except Exception as e:
        raise ValueError(f"Could not normalize audio: {str(e)}")


def resample_audio(audio_array: np.ndarray, orig_sr: int, target_sr: int) -> np.ndarray:
    """
    Resample audio to target sample rate

    Args:
        audio_array: Input audio array
        orig_sr: Original sample rate
        target_sr: Target sample rate

    Returns:
        Resampled audio array
    """
    try:
        if orig_sr == target_sr:
            return audio_array

        resampled = librosa.resample(audio_array, orig_sr=orig_sr, target_sr=target_sr)
        return resampled

    except Exception as e:
        raise ValueError(f"Could not resample audio: {str(e)}")


def convert_stereo_to_mono(audio_array: np.ndarray) -> np.ndarray:
    """
    Convert stereo audio to mono

    Args:
        audio_array: Input audio array

    Returns:
        Mono audio array
    """
    try:
        if len(audio_array.shape) == 1:
            return audio_array

        return librosa.to_mono(audio_array)

    except Exception as e:
        raise ValueError(f"Could not convert to mono: {str(e)}")


def apply_fade(
    audio_array: np.ndarray, sample_rate: int, fade_duration: float = 0.1
) -> np.ndarray:
    """
    Apply fade in/out to audio

    Args:
        audio_array: Input audio array
        sample_rate: Sample rate
        fade_duration: Fade duration in seconds

    Returns:
        Audio with fade applied
    """
    try:
        fade_samples = int(fade_duration * sample_rate)

        if fade_samples >= len(audio_array) // 2:
            fade_samples = len(audio_array) // 4

        # Create fade curves
        fade_in = np.linspace(0, 1, fade_samples)
        fade_out = np.linspace(1, 0, fade_samples)

        # Apply fades
        audio_faded = audio_array.copy()
        audio_faded[:fade_samples] *= fade_in
        audio_faded[-fade_samples:] *= fade_out

        return audio_faded

    except Exception as e:
        raise ValueError(f"Could not apply fade: {str(e)}")


def detect_silence(
    audio_array: np.ndarray,
    sample_rate: int,
    silence_threshold: float = 0.01,
    min_silence_duration: float = 0.5,
) -> list:
    """
    Detect silence segments in audio

    Args:
        audio_array: Input audio array
        sample_rate: Sample rate
        silence_threshold: RMS threshold for silence detection
        min_silence_duration: Minimum duration for silence segment

    Returns:
        List of (start_time, end_time) tuples for silence segments
    """
    try:
        # Calculate frame-wise RMS
        frame_length = int(0.025 * sample_rate)  # 25ms frames
        hop_length = int(0.010 * sample_rate)  # 10ms hop

        rms = librosa.feature.rms(
            y=audio_array, frame_length=frame_length, hop_length=hop_length
        )[0]

        # Convert to time axis
        times = librosa.frames_to_time(
            np.arange(len(rms)), sr=sample_rate, hop_length=hop_length
        )

        # Find silence frames
        silence_frames = rms < silence_threshold

        # Find contiguous silence regions
        silence_segments = []
        in_silence = False
        silence_start = None

        for i, is_silent in enumerate(silence_frames):
            if is_silent and not in_silence:
                silence_start = times[i]
                in_silence = True
            elif not is_silent and in_silence:
                silence_duration = times[i] - silence_start
                if silence_duration >= min_silence_duration:
                    silence_segments.append((silence_start, times[i]))
                in_silence = False

        # Handle case where audio ends in silence
        if in_silence and silence_start is not None:
            silence_duration = times[-1] - silence_start
            if silence_duration >= min_silence_duration:
                silence_segments.append((silence_start, times[-1]))

        return silence_segments

    except Exception as e:
        raise ValueError(f"Could not detect silence: {str(e)}")


def trim_silence(
    audio_array: np.ndarray, sample_rate: int, threshold: float = 0.01
) -> Tuple[np.ndarray, Tuple[int, int]]:
    """
    Trim silence from beginning and end of audio

    Args:
        audio_array: Input audio array
        sample_rate: Sample rate
        threshold: RMS threshold for silence detection

    Returns:
        Tuple of (trimmed_audio, (start_sample, end_sample))
    """
    try:
        # Use librosa's trim function
        trimmed_audio, trim_indices = librosa.effects.trim(
            audio_array,
            top_db=20 * np.log10(1 / threshold),
            frame_length=2048,
            hop_length=512,
        )

        return trimmed_audio, trim_indices

    except Exception as e:
        raise ValueError(f"Could not trim silence: {str(e)}")
