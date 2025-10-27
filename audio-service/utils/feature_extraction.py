from typing import Any, Dict, List

import librosa
import numpy as np

from config import settings


def extract_mfcc(y: np.ndarray, sr: int, n_mfcc: int = None) -> List[List[float]]:
    """Extract MFCC features"""
    if n_mfcc is None:
        n_mfcc = settings.N_MFCC

    mfcc = librosa.feature.mfcc(
        y=y, sr=sr, n_mfcc=n_mfcc, hop_length=settings.HOP_LENGTH
    )
    return mfcc.tolist()


def extract_chroma(y: np.ndarray, sr: int) -> List[List[float]]:
    """Extract chroma features"""
    chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=settings.HOP_LENGTH)
    return chroma.tolist()


def extract_spectral_centroid(y: np.ndarray, sr: int) -> List[float]:
    """Extract spectral centroid"""
    spectral_centroid = librosa.feature.spectral_centroid(
        y=y, sr=sr, hop_length=settings.HOP_LENGTH
    )[0]
    return spectral_centroid.tolist()


def extract_spectral_rolloff(y: np.ndarray, sr: int) -> List[float]:
    """Extract spectral rollof"""
    spectral_rolloff = librosa.feature.spectral_rolloff(
        y=y, sr=sr, hop_length=settings.HOP_LENGTH
    )[0]
    return spectral_rolloff.tolist()


def extract_zero_crossing_rate(y: np.ndarray) -> List[float]:
    """Extract zero crossing rate"""
    zcr = librosa.feature.zero_crossing_rate(y=y, hop_length=settings.HOP_LENGTH)[0]
    return zcr.tolist()


def extract_tempo(y: np.ndarray, sr: int) -> float:
    """Extract tempo (BPM)"""
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    return float(tempo)


def extract_onset_frames(y: np.ndarray, sr: int) -> List[int]:
    """Extract onset detection frames"""
    onset_frames = librosa.onset.onset_detect(
        y=y, sr=sr, hop_length=settings.HOP_LENGTH, units="frames"
    )
    return onset_frames.tolist()


def extract_melspectrogram(
    y: np.ndarray, sr: int, n_mels: int = None
) -> List[List[float]]:
    """Extract mel-spectrogram"""
    if n_mels is None:
        n_mels = settings.N_MELS

    mel_spec = librosa.feature.melspectrogram(
        y=y, sr=sr, n_mels=n_mels, hop_length=settings.HOP_LENGTH
    )
    # Convert to dB scale
    mel_spec_db = librosa.power_to_db(mel_spec, ref=np.max)
    return mel_spec_db.tolist()


def extract_spectral_bandwidth(y: np.ndarray, sr: int) -> List[float]:
    """Extract spectral bandwidth"""
    spectral_bandwidth = librosa.feature.spectral_bandwidth(
        y=y, sr=sr, hop_length=settings.HOP_LENGTH
    )[0]
    return spectral_bandwidth.tolist()


def extract_spectral_contrast(y: np.ndarray, sr: int) -> List[List[float]]:
    """Extract spectral contrast"""
    spectral_contrast = librosa.feature.spectral_contrast(
        y=y, sr=sr, hop_length=settings.HOP_LENGTH
    )
    return spectral_contrast.tolist()


def extract_tonnetz(y: np.ndarray, sr: int) -> List[List[float]]:
    """Extract tonnetz (tonal centroid features)"""
    # First extract chroma
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=settings.HOP_LENGTH)
    # Then compute tonnetz
    tonnetz = librosa.feature.tonnetz(chroma=chroma)
    return tonnetz.tolist()


def extract_rms_energy(y: np.ndarray) -> List[float]:
    """Extract RMS energy"""
    rms = librosa.feature.rms(y=y, hop_length=settings.HOP_LENGTH)[0]
    return rms.tolist()


def extract_pitch_features(y: np.ndarray, sr: int) -> Dict[str, Any]:
    """Extract pitch-related features"""
    # Fundamental frequency estimation
    pitches, magnitudes = librosa.piptrack(
        y=y, sr=sr, hop_length=settings.HOP_LENGTH, threshold=0.1
    )

    # Extract the most prominent pitch at each frame
    pitch_track = []
    for t in range(pitches.shape[1]):
        index = magnitudes[:, t].argmax()
        pitch = pitches[index, t]
        pitch_track.append(float(pitch) if pitch > 0 else 0.0)

    # Calculate statistics
    non_zero_pitches = [p for p in pitch_track if p > 0]

    pitch_features = {
        "pitch_track": pitch_track,
        "mean_pitch": float(np.mean(non_zero_pitches)) if non_zero_pitches else 0.0,
        "std_pitch": float(np.std(non_zero_pitches)) if non_zero_pitches else 0.0,
        "min_pitch": float(np.min(non_zero_pitches)) if non_zero_pitches else 0.0,
        "max_pitch": float(np.max(non_zero_pitches)) if non_zero_pitches else 0.0,
    }

    return pitch_features


def extract_rhythm_features(y: np.ndarray, sr: int) -> Dict[str, Any]:
    """Extract rhythm-related features"""
    # Tempo and beats
    tempo, beats = librosa.beat.beat_track(y=y, sr=sr, hop_length=settings.HOP_LENGTH)

    # Beat times
    beat_times = librosa.frames_to_time(beats, sr=sr, hop_length=settings.HOP_LENGTH)

    # Inter-beat intervals
    if len(beat_times) > 1:
        ibi = np.diff(beat_times)
        ibi_mean = float(np.mean(ibi))
        ibi_std = float(np.std(ibi))
    else:
        ibi_mean = 0.0
        ibi_std = 0.0

    rhythm_features = {
        "tempo": float(tempo),
        "beat_frames": beats.tolist(),
        "beat_times": beat_times.tolist(),
        "inter_beat_interval_mean": ibi_mean,
        "inter_beat_interval_std": ibi_std,
        "rhythmic_regularity": 1.0 / (1.0 + ibi_std) if ibi_std > 0 else 1.0,
    }

    return rhythm_features


def extract_harmony_features(y: np.ndarray, sr: int) -> Dict[str, Any]:
    """Extract harmony-related features"""
    # Chroma features
    chroma = librosa.feature.chroma_stft(y=y, sr=sr, hop_length=settings.HOP_LENGTH)

    # Tonnetz features
    tonnetz = librosa.feature.tonnetz(chroma=chroma)

    # Key estimation (simplified)
    chroma_mean = np.mean(chroma, axis=1)
    key_profile_major = np.array(
        [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
    )
    key_profile_minor = np.array(
        [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
    )

    # Correlate with key profiles
    major_correlations = [
        np.corrcoef(chroma_mean, np.roll(key_profile_major, k))[0, 1] for k in range(12)
    ]
    minor_correlations = [
        np.corrcoef(chroma_mean, np.roll(key_profile_minor, k))[0, 1] for k in range(12)
    ]

    max_major_idx = np.argmax(major_correlations)
    max_minor_idx = np.argmax(minor_correlations)

    if major_correlations[max_major_idx] > minor_correlations[max_minor_idx]:
        estimated_key = f"{['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][max_major_idx]} major"
        key_confidence = float(major_correlations[max_major_idx])
    else:
        estimated_key = f"{['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B'][max_minor_idx]} minor"
        key_confidence = float(minor_correlations[max_minor_idx])

    harmony_features = {
        "chroma_mean": chroma_mean.tolist(),
        "chroma_std": np.std(chroma, axis=1).tolist(),
        "tonnetz_mean": np.mean(tonnetz, axis=1).tolist(),
        "tonnetz_std": np.std(tonnetz, axis=1).tolist(),
        "estimated_key": estimated_key,
        "key_confidence": key_confidence,
    }

    return harmony_features


def extract_all_features(y: np.ndarray, sr: int) -> Dict[str, Any]:
    """Extract all audio features"""
    features = {}

    # Basic spectral features
    features["mfcc"] = extract_mfcc(y, sr)
    features["chroma"] = extract_chroma(y, sr)
    features["spectral_centroid"] = extract_spectral_centroid(y, sr)
    features["spectral_rolloff"] = extract_spectral_rolloff(y, sr)
    features["spectral_bandwidth"] = extract_spectral_bandwidth(y, sr)
    features["spectral_contrast"] = extract_spectral_contrast(y, sr)
    features["zero_crossing_rate"] = extract_zero_crossing_rate(y)
    features["rms_energy"] = extract_rms_energy(y)

    # Mel-spectrogram
    features["melspectrogram"] = extract_melspectrogram(y, sr)

    # Tonal features
    features["tonnetz"] = extract_tonnetz(y, sr)

    # Temporal features
    features["tempo"] = extract_tempo(y, sr)
    features["onset_frames"] = extract_onset_frames(y, sr)

    # Advanced features
    try:
        features["pitch_features"] = extract_pitch_features(y, sr)
    except Exception as e:
        features["pitch_features"] = {"error": str(e)}

    try:
        features["rhythm_features"] = extract_rhythm_features(y, sr)
    except Exception as e:
        features["rhythm_features"] = {"error": str(e)}

    try:
        features["harmony_features"] = extract_harmony_features(y, sr)
    except Exception as e:
        features["harmony_features"] = {"error": str(e)}

    # Audio statistics
    features["audio_stats"] = {
        "duration": float(len(y) / sr),
        "sample_rate": int(sr),
        "length_samples": int(len(y)),
        "max_amplitude": float(np.max(np.abs(y))),
        "rms_amplitude": float(np.sqrt(np.mean(y**2))),
        "zero_crossings": int(np.sum(np.abs(np.diff(np.sign(y)))) / 2),
    }

    return features


def extract_features_subset(
    y: np.ndarray, sr: int, feature_list: List[str]
) -> Dict[str, Any]:
    """Extract only specified features"""
    available_features = {
        "mfcc": lambda: extract_mfcc(y, sr),
        "chroma": lambda: extract_chroma(y, sr),
        "spectral_centroid": lambda: extract_spectral_centroid(y, sr),
        "spectral_rolloff": lambda: extract_spectral_rolloff(y, sr),
        "spectral_bandwidth": lambda: extract_spectral_bandwidth(y, sr),
        "spectral_contrast": lambda: extract_spectral_contrast(y, sr),
        "zero_crossing_rate": lambda: extract_zero_crossing_rate(y),
        "rms_energy": lambda: extract_rms_energy(y),
        "melspectrogram": lambda: extract_melspectrogram(y, sr),
        "tonnetz": lambda: extract_tonnetz(y, sr),
        "tempo": lambda: extract_tempo(y, sr),
        "onset_frames": lambda: extract_onset_frames(y, sr),
        "pitch_features": lambda: extract_pitch_features(y, sr),
        "rhythm_features": lambda: extract_rhythm_features(y, sr),
        "harmony_features": lambda: extract_harmony_features(y, sr),
    }

    features = {}
    for feature_name in feature_list:
        if feature_name in available_features:
            try:
                features[feature_name] = available_features[feature_name]()
            except Exception as e:
                features[feature_name] = {"error": str(e)}
        else:
            features[feature_name] = {
                "error": f'Feature "{feature_name}" not available'
            }

    return features
