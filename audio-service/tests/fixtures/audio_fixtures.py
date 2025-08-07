"""
Audio test fixtures and utilities
"""

import numpy as np
import tempfile
import os
from pathlib import Path
from typing import Tuple, Optional
import soundfile as sf


class AudioFixtures:
    """Provides test audio data and utilities"""
    
    @staticmethod
    def generate_test_audio(
        duration: float = 1.0, 
        sample_rate: int = 22050, 
        frequency: float = 440.0,
        channels: int = 1,
        amplitude: float = 0.5
    ) -> np.ndarray:
        """
        Generate test audio signal
        
        Args:
            duration: Duration in seconds
            sample_rate: Sample rate
            frequency: Frequency in Hz
            channels: Number of channels (1=mono, 2=stereo)
            amplitude: Amplitude (0-1)
        
        Returns:
            Audio array
        """
        samples = int(duration * sample_rate)
        t = np.linspace(0, duration, samples)
        
        # Generate sine wave
        audio = amplitude * np.sin(2 * np.pi * frequency * t)
        
        if channels == 2:
            # Create stereo with slight phase difference
            left = audio
            right = amplitude * np.sin(2 * np.pi * frequency * t + np.pi/4)
            audio = np.stack([left, right])
        elif channels > 2:
            # Multi-channel audio
            audio_multi = []
            for i in range(channels):
                phase = i * np.pi / channels
                channel_audio = amplitude * np.sin(2 * np.pi * frequency * t + phase)
                audio_multi.append(channel_audio)
            audio = np.stack(audio_multi)
            
        return audio
    
    @staticmethod
    def create_temp_audio_file(
        audio_data: np.ndarray, 
        sample_rate: int = 22050,
        suffix: str = '.wav'
    ) -> str:
        """
        Create temporary audio file
        
        Args:
            audio_data: Audio array
            sample_rate: Sample rate
            suffix: File extension
        
        Returns:
            Path to temporary file
        """
        temp_file = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
        temp_file.close()
        
        # Handle mono/stereo format for soundfile
        if len(audio_data.shape) == 1:
            # Mono
            sf.write(temp_file.name, audio_data, sample_rate)
        else:
            # Multi-channel - transpose for soundfile format (samples x channels)
            sf.write(temp_file.name, audio_data.T, sample_rate)
        
        return temp_file.name
    
    @staticmethod
    def get_test_audio_path() -> str:
        """Get path to the main test audio file"""
        fixtures_dir = Path(__file__).parent
        test_audio_path = fixtures_dir / "test_audio.wav"
        return str(test_audio_path)
    
    @staticmethod
    def audio_to_bytes(audio_data: np.ndarray, sample_rate: int = 22050) -> bytes:
        """
        Convert audio array to bytes
        
        Args:
            audio_data: Audio array
            sample_rate: Sample rate
        
        Returns:
            Audio as bytes
        """
        temp_file = AudioFixtures.create_temp_audio_file(audio_data, sample_rate)
        
        try:
            with open(temp_file, 'rb') as f:
                audio_bytes = f.read()
            return audio_bytes
        finally:
            os.unlink(temp_file)
    
    @staticmethod
    def cleanup_temp_files(file_paths: list):
        """Clean up temporary files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception:
                pass  # Ignore cleanup errors


# Common test audio samples
TEST_AUDIO_MONO_1S = AudioFixtures.generate_test_audio(duration=1.0, channels=1)
TEST_AUDIO_STEREO_1S = AudioFixtures.generate_test_audio(duration=1.0, channels=2)
TEST_AUDIO_MONO_5S = AudioFixtures.generate_test_audio(duration=5.0, channels=1)
TEST_AUDIO_STEREO_5S = AudioFixtures.generate_test_audio(duration=5.0, channels=2)

# Different frequency test samples
TEST_AUDIO_LOW_FREQ = AudioFixtures.generate_test_audio(frequency=220.0)  # A3
TEST_AUDIO_HIGH_FREQ = AudioFixtures.generate_test_audio(frequency=880.0)  # A5

# Multi-channel test
TEST_AUDIO_MULTICHANNEL = AudioFixtures.generate_test_audio(channels=5)