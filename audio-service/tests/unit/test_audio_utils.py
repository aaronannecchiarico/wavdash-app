"""
Unit tests for utils.audio_utils module
"""

import pytest
import numpy as np
import tempfile
import os
from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from utils.audio_utils import (
    load_audio_from_bytes,
    save_audio_file,
    validate_audio_format,
    get_audio_duration,
    normalize_audio,
    resample_audio,
    convert_stereo_to_mono,
    apply_fade,
    detect_silence,
    trim_silence
)
from tests.fixtures.audio_fixtures import AudioFixtures, TEST_AUDIO_MONO_1S, TEST_AUDIO_STEREO_1S


class TestAudioUtils:
    """Test cases for audio utility functions"""
    
    def test_load_audio_from_bytes_mono(self):
        """Test loading mono audio from bytes"""
        audio_bytes = AudioFixtures.audio_to_bytes(TEST_AUDIO_MONO_1S, 22050)
        
        y, sr = load_audio_from_bytes(audio_bytes, sr=22050, mono=True)
        
        assert isinstance(y, np.ndarray)
        assert len(y.shape) == 1  # Mono
        assert sr == 22050
        assert len(y) > 0
    
    def test_load_audio_from_bytes_stereo(self):
        """Test loading stereo audio from bytes"""
        audio_bytes = AudioFixtures.audio_to_bytes(TEST_AUDIO_STEREO_1S, 22050)
        
        y, sr = load_audio_from_bytes(audio_bytes, sr=22050, mono=False)
        
        assert isinstance(y, np.ndarray)
        assert len(y.shape) == 2  # Stereo
        assert y.shape[0] == 2  # 2 channels
        assert sr == 22050
        assert y.shape[1] > 0
    
    def test_load_audio_invalid_data(self):
        """Test loading audio with invalid data"""
        invalid_bytes = b"not audio data"
        
        with pytest.raises(ValueError, match="Could not load audio from bytes"):
            load_audio_from_bytes(invalid_bytes)
    
    def test_save_audio_file(self):
        """Test saving audio to file"""
        temp_dir = tempfile.mkdtemp()
        output_path = os.path.join(temp_dir, "test_output.wav")
        
        try:
            result_path = save_audio_file(TEST_AUDIO_MONO_1S, 22050, output_path)
            
            assert result_path == output_path
            assert os.path.exists(output_path)
            
            # Verify file can be loaded back
            y, sr = load_audio_from_bytes(open(output_path, 'rb').read())
            assert len(y) > 0
            
        finally:
            AudioFixtures.cleanup_temp_files([output_path])
            os.rmdir(temp_dir)
    
    def test_validate_audio_format(self):
        """Test audio format validation"""
        # Valid formats
        assert validate_audio_format("test.wav")
        assert validate_audio_format("test.mp3")
        assert validate_audio_format("test.flac")
        assert validate_audio_format("TEST.WAV")  # Case insensitive
        
        # Invalid formats
        assert not validate_audio_format("test.txt")
        assert not validate_audio_format("test.pdf")
        assert not validate_audio_format("test")  # No extension
    
    def test_get_audio_duration(self):
        """Test getting audio duration"""
        # 1 second audio at 22050 Hz should be close to 1.0 seconds
        audio_bytes = AudioFixtures.audio_to_bytes(TEST_AUDIO_MONO_1S, 22050)
        
        duration = get_audio_duration(audio_bytes)
        
        # Allow some tolerance for floating point precision
        assert 0.9 <= duration <= 1.1
    
    def test_normalize_audio(self):
        """Test audio normalization"""
        # Create audio with known amplitude
        loud_audio = TEST_AUDIO_MONO_1S * 2.0  # Double amplitude
        
        normalized = normalize_audio(loud_audio, target_db=-6.0)
        
        assert isinstance(normalized, np.ndarray)
        assert normalized.shape == loud_audio.shape
        assert np.max(np.abs(normalized)) <= 1.0  # No clipping
        
        # Check RMS is closer to target
        rms_normalized = np.sqrt(np.mean(normalized**2))
        target_linear = 10**(-6.0/20.0)
        assert abs(rms_normalized - target_linear) < 0.1
    
    def test_normalize_audio_zero_signal(self):
        """Test normalizing zero signal"""
        zero_audio = np.zeros(1000)
        
        normalized = normalize_audio(zero_audio)
        
        assert np.array_equal(normalized, zero_audio)
    
    def test_resample_audio(self):
        """Test audio resampling"""
        original_sr = 44100
        target_sr = 22050
        
        # Generate audio at higher sample rate
        audio_44k = AudioFixtures.generate_test_audio(sample_rate=original_sr)
        
        resampled = resample_audio(audio_44k, original_sr, target_sr)
        
        assert isinstance(resampled, np.ndarray)
        # Should be roughly half the length
        expected_length = len(audio_44k) * target_sr // original_sr
        assert abs(len(resampled) - expected_length) < 10  # Allow some tolerance
    
    def test_resample_audio_same_rate(self):
        """Test resampling with same rate (should return unchanged)"""
        sr = 22050
        resampled = resample_audio(TEST_AUDIO_MONO_1S, sr, sr)
        
        np.testing.assert_array_equal(resampled, TEST_AUDIO_MONO_1S)
    
    def test_convert_stereo_to_mono(self):
        """Test stereo to mono conversion"""
        mono_result = convert_stereo_to_mono(TEST_AUDIO_STEREO_1S)
        
        assert isinstance(mono_result, np.ndarray)
        assert len(mono_result.shape) == 1  # Should be mono
        assert len(mono_result) == TEST_AUDIO_STEREO_1S.shape[1]
    
    def test_convert_mono_to_mono(self):
        """Test mono input to mono conversion (should be unchanged)"""
        mono_result = convert_stereo_to_mono(TEST_AUDIO_MONO_1S)
        
        np.testing.assert_array_equal(mono_result, TEST_AUDIO_MONO_1S)
    
    def test_apply_fade(self):
        """Test applying fade in/out"""
        sample_rate = 22050
        fade_duration = 0.1  # 100ms
        
        faded = apply_fade(TEST_AUDIO_MONO_1S, sample_rate, fade_duration)
        
        assert isinstance(faded, np.ndarray)
        assert faded.shape == TEST_AUDIO_MONO_1S.shape
        
        # Check fade in - first samples should be quieter (skip the first zero)
        fade_samples = int(fade_duration * sample_rate)
        assert abs(faded[fade_samples//2]) < abs(TEST_AUDIO_MONO_1S[fade_samples//2])
        
        # Check fade out - last samples should be quieter (skip the last zero)
        assert abs(faded[-fade_samples//2]) < abs(TEST_AUDIO_MONO_1S[-fade_samples//2])
    
    def test_detect_silence(self):
        """Test silence detection"""
        sample_rate = 22050
        
        # Create audio with silence in the middle
        audio_with_silence = np.concatenate([
            TEST_AUDIO_MONO_1S[:5000],      # Audio
            np.zeros(5000),                  # Silence
            TEST_AUDIO_MONO_1S[:5000]       # Audio
        ])
        
        silence_segments = detect_silence(
            audio_with_silence, 
            sample_rate, 
            silence_threshold=0.01,
            min_silence_duration=0.1
        )
        
        assert isinstance(silence_segments, list)
        # Should detect at least one silence segment
        assert len(silence_segments) >= 1
        
        # Each segment should be a tuple of (start, end) times
        for start, end in silence_segments:
            assert isinstance(start, (int, float))
            assert isinstance(end, (int, float))
            assert end > start
    
    def test_trim_silence(self):
        """Test trimming silence from audio"""
        sample_rate = 22050
        
        # Create audio with silence padding
        padded_audio = np.concatenate([
            np.zeros(2000),           # Silence at start
            TEST_AUDIO_MONO_1S,       # Actual audio
            np.zeros(2000)            # Silence at end
        ])
        
        trimmed, indices = trim_silence(padded_audio, sample_rate, threshold=0.01)
        
        assert isinstance(trimmed, np.ndarray)
        # librosa.effects.trim returns numpy arrays, not tuples
        assert isinstance(indices, np.ndarray)
        assert len(indices) == 2
        
        # Trimmed audio should be shorter
        assert len(trimmed) < len(padded_audio)
        assert len(trimmed) > 0
        
        # Indices should be valid
        start_idx, end_idx = indices[0], indices[1]
        assert 0 <= start_idx < end_idx <= len(padded_audio)


if __name__ == "__main__":
    pytest.main([__file__])