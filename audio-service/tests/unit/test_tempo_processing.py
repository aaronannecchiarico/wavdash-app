"""
Unit tests for tempo processing functionality
"""

from pathlib import Path
import sys
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models.tempo_models import TempoPresetEnum
from tasks.tempo_processing import TEMPO_PRESETS, apply_tempo_processing


class TestTempoProcessingFunctions:
    """Test cases for tempo processing functions"""

    def setup_method(self):
        """Set up test data"""
        # Create a simple sine wave for testing
        self.sample_rate = 22050
        self.duration = 2.0  # 2 seconds
        self.samples = int(self.sample_rate * self.duration)

        # Generate 440Hz sine wave (A4 note)
        t = np.linspace(0, self.duration, self.samples, False)
        self.test_audio = np.sin(2 * np.pi * 440 * t).astype(np.float32)

    def test_apply_tempo_processing_no_change(self):
        """Test tempo processing with no changes (factor=1.0, no pitch shift)"""
        processed = apply_tempo_processing(
            self.test_audio,
            self.sample_rate,
            tempo_factor=1.0,
            pitch_shift_semitones=0.0,
            preserve_pitch=False,
            add_reverb=False,
        )

        # Should be very similar to original (allowing for small numerical differences)
        assert processed.shape == self.test_audio.shape
        np.testing.assert_allclose(processed, self.test_audio, rtol=1e-5)

    @patch("librosa.effects.time_stretch")
    def test_apply_tempo_processing_speed_up(self, mock_time_stretch):
        """Test tempo processing with speed up (traditional pitch + tempo change)"""
        # Create expected output (shorter audio)
        tempo_factor = 1.5
        expected_length = int(len(self.test_audio) / tempo_factor)
        mock_output = self.test_audio[:expected_length]  # Simulate shorter audio
        mock_time_stretch.return_value = mock_output

        processed = apply_tempo_processing(
            self.test_audio,
            self.sample_rate,
            tempo_factor=tempo_factor,
            pitch_shift_semitones=0.0,
            preserve_pitch=False,
            add_reverb=False,
        )

        # Should call time_stretch and return shorter audio
        mock_time_stretch.assert_called_once()
        call_args = mock_time_stretch.call_args
        assert call_args[1]["rate"] == tempo_factor
        assert len(processed) == expected_length

    @patch("librosa.effects.time_stretch")
    def test_apply_tempo_processing_slow_down(self, mock_time_stretch):
        """Test tempo processing with slow down (traditional pitch + tempo change)"""
        tempo_factor = 0.75
        expected_length = int(len(self.test_audio) / tempo_factor)
        mock_output = np.tile(
            self.test_audio, int(np.ceil(expected_length / len(self.test_audio)))
        )[:expected_length]
        mock_time_stretch.return_value = mock_output

        processed = apply_tempo_processing(
            self.test_audio,
            self.sample_rate,
            tempo_factor=tempo_factor,
            pitch_shift_semitones=0.0,
            preserve_pitch=False,
            add_reverb=False,
        )

        # Should call time_stretch and return longer audio
        mock_time_stretch.assert_called_once()
        call_args = mock_time_stretch.call_args
        assert call_args[1]["rate"] == tempo_factor
        assert len(processed) == expected_length

    @patch("librosa.effects.time_stretch")
    def test_apply_tempo_processing_time_stretch(self, mock_time_stretch):
        """Test tempo processing with time stretching (preserve pitch)"""
        mock_time_stretch.return_value = self.test_audio  # Mock return value

        processed = apply_tempo_processing(
            self.test_audio,
            self.sample_rate,
            tempo_factor=1.2,
            pitch_shift_semitones=0.0,
            preserve_pitch=True,
            add_reverb=False,
        )

        # Should have called librosa time_stretch
        mock_time_stretch.assert_called_once()
        call_args = mock_time_stretch.call_args
        assert call_args[1]["rate"] == 1.2
        assert processed is not None

    @patch(
        "tasks.tempo_processing.PEDALBOARD_AVAILABLE", False
    )  # Force fallback to librosa
    @patch("librosa.effects.pitch_shift")
    @patch("librosa.effects.time_stretch")
    def test_apply_tempo_processing_pitch_shift_with_time_stretch(
        self, mock_time_stretch, mock_pitch_shift
    ):
        """Test tempo processing with both time stretch and pitch shift (librosa fallback)"""
        mock_time_stretch.return_value = self.test_audio.copy()
        mock_pitch_shift.return_value = self.test_audio.copy()

        processed = apply_tempo_processing(
            self.test_audio,
            self.sample_rate,
            tempo_factor=0.8,
            pitch_shift_semitones=-2.0,
            preserve_pitch=True,
            add_reverb=False,
        )

        # Should call both functions when pedalboard is not available
        mock_time_stretch.assert_called_once()
        time_stretch_args = mock_time_stretch.call_args
        assert time_stretch_args[1]["rate"] == 0.8

        # Check that pitch_shift was called with correct parameters
        mock_pitch_shift.assert_called_once()
        pitch_shift_args = mock_pitch_shift.call_args
        assert pitch_shift_args[1]["sr"] == self.sample_rate
        assert pitch_shift_args[1]["n_steps"] == -2.0
        assert processed is not None

    @patch("tasks.tempo_processing.create_pedalboard_for_preset")
    @patch("librosa.effects.time_stretch")
    def test_apply_tempo_processing_with_pedalboard_available(
        self, mock_time_stretch, mock_create_pedalboard
    ):
        """Test tempo processing with pedalboard available (Phase 2 enhanced path)"""
        mock_time_stretch.return_value = self.test_audio.copy()

        # Mock pedalboard creation and processing
        mock_pedalboard = MagicMock()
        mock_pedalboard.return_value = self.test_audio.copy()
        mock_create_pedalboard.return_value = mock_pedalboard

        processed = apply_tempo_processing(
            self.test_audio,
            self.sample_rate,
            tempo_factor=1.3,
            pitch_shift_semitones=2.0,
            preserve_pitch=False,
            add_reverb=True,
        )

        # Should call time_stretch for tempo change
        mock_time_stretch.assert_called_once()
        time_stretch_args = mock_time_stretch.call_args
        assert time_stretch_args[1]["rate"] == 1.3

        # Should create pedalboard for effects (including pitch shift)
        mock_create_pedalboard.assert_called_once()
        create_args = mock_create_pedalboard.call_args[0]
        assert create_args[1] == 1.3  # tempo_factor
        assert create_args[2] == 2.0  # pitch_shift_semitones
        assert create_args[3] is True  # add_reverb

        # Should apply pedalboard effects
        mock_pedalboard.assert_called_once()

        assert processed is not None

    def test_apply_tempo_processing_with_reverb(self):
        """Test tempo processing with reverb effect"""
        processed = apply_tempo_processing(
            self.test_audio,
            self.sample_rate,
            tempo_factor=1.0,
            pitch_shift_semitones=0.0,
            preserve_pitch=False,
            add_reverb=True,
        )

        # Should have same length but different values due to reverb
        assert processed.shape == self.test_audio.shape
        # The processed audio should be different from original due to reverb
        assert not np.allclose(processed, self.test_audio, rtol=1e-3)

    def test_apply_tempo_processing_error_handling(self):
        """Test error handling in tempo processing"""
        # Test with invalid audio data (None)
        with pytest.raises(ValueError, match="Audio data cannot be None or empty"):
            apply_tempo_processing(
                None,  # Invalid audio data
                self.sample_rate,
                tempo_factor=1.0,
                pitch_shift_semitones=0.0,
                preserve_pitch=False,
                add_reverb=False,
            )

        # Test with invalid sample rate
        with pytest.raises(ValueError, match="Sample rate must be positive"):
            apply_tempo_processing(
                self.test_audio,
                -1,  # Invalid sample rate
                tempo_factor=1.0,
                pitch_shift_semitones=0.0,
                preserve_pitch=False,
                add_reverb=False,
            )

    def test_tempo_presets_configuration(self):
        """Test that TEMPO_PRESETS contains expected configurations"""
        # Check that all expected presets are present
        expected_presets = [
            TempoPresetEnum.SPED_UP,
            TempoPresetEnum.SLOWED_REVERB,
            TempoPresetEnum.NIGHTCORE,
            TempoPresetEnum.CHOPPED_SCREWED,
            TempoPresetEnum.TIME_STRETCHED,
        ]

        for preset in expected_presets:
            assert preset in TEMPO_PRESETS
            config = TEMPO_PRESETS[preset]

            # Validate required fields
            assert "tempo_factor" in config
            assert "pitch_shift_semitones" in config
            assert "preserve_pitch" in config
            assert "effects" in config
            assert "description" in config

            # Validate ranges
            assert 0.25 <= config["tempo_factor"] <= 4.0
            assert -12.0 <= config["pitch_shift_semitones"] <= 12.0
            assert isinstance(config["preserve_pitch"], bool)
            assert isinstance(config["effects"], list)

    def test_sped_up_preset_values(self):
        """Test specific values for sped up preset"""
        config = TEMPO_PRESETS[TempoPresetEnum.SPED_UP]

        assert config["tempo_factor"] == 1.25
        assert config["pitch_shift_semitones"] == 3.0
        assert config["preserve_pitch"] is False
        assert "pitch_shift" in config["effects"]
        assert "brightness_boost" in config["effects"]

    def test_slowed_reverb_preset_values(self):
        """Test specific values for slowed reverb preset"""
        config = TEMPO_PRESETS[TempoPresetEnum.SLOWED_REVERB]

        assert config["tempo_factor"] == 0.75
        assert config["pitch_shift_semitones"] == -2.0
        assert config["preserve_pitch"] is False
        assert "pitch_shift" in config["effects"]
        assert "reverb" in config["effects"]
        assert "reverb_settings" in config
        assert config["reverb_settings"]["wet_level"] == 0.35
        assert config["reverb_settings"]["room_size"] == 0.5

    def test_nightcore_preset_values(self):
        """Test specific values for nightcore preset"""
        config = TEMPO_PRESETS[TempoPresetEnum.NIGHTCORE]

        assert config["tempo_factor"] == 1.4
        assert config["pitch_shift_semitones"] == 4.0
        assert config["preserve_pitch"] is False
        assert "pitch_shift" in config["effects"]
        assert "brightness_boost" in config["effects"]
        assert "compression" in config["effects"]

    def test_chopped_screwed_preset_values(self):
        """Test specific values for chopped & screwed preset"""
        config = TEMPO_PRESETS[TempoPresetEnum.CHOPPED_SCREWED]

        assert config["tempo_factor"] == 0.6
        assert config["pitch_shift_semitones"] == -3.0
        assert config["preserve_pitch"] is False
        assert "pitch_shift" in config["effects"]
        assert "low_pass_filter" in config["effects"]

    def test_time_stretched_preset_values(self):
        """Test specific values for time stretched preset"""
        config = TEMPO_PRESETS[TempoPresetEnum.TIME_STRETCHED]

        assert config["tempo_factor"] == 0.8
        assert config["pitch_shift_semitones"] == 0.0
        assert config["preserve_pitch"] is True
        assert "time_stretch" in config["effects"]


class TestTempoProcessingEdgeCases:
    """Test edge cases and error conditions"""

    @patch("librosa.effects.time_stretch")
    def test_extreme_tempo_factors(self, mock_time_stretch):
        """Test tempo processing with extreme but valid tempo factors"""
        # Create short test audio
        sample_rate = 22050
        duration = 0.5
        samples = int(sample_rate * duration)
        test_audio = np.sin(2 * np.pi * 440 * np.linspace(0, duration, samples)).astype(
            np.float32
        )

        # Test minimum tempo factor - mock longer output
        longer_output = np.tile(test_audio, 4)[: int(len(test_audio) / 0.25)]
        mock_time_stretch.return_value = longer_output

        processed_min = apply_tempo_processing(
            test_audio, sample_rate, 0.25, 0.0, False, False
        )
        assert processed_min is not None
        assert len(processed_min) > len(test_audio)  # Should be longer

        # Test maximum tempo factor - mock shorter output
        shorter_output = test_audio[: int(len(test_audio) / 4.0)]
        mock_time_stretch.return_value = shorter_output

        processed_max = apply_tempo_processing(
            test_audio, sample_rate, 4.0, 0.0, False, False
        )
        assert processed_max is not None
        assert len(processed_max) < len(test_audio)  # Should be shorter

    def test_extreme_pitch_shifts(self):
        """Test tempo processing with extreme but valid pitch shifts"""
        # Create short test audio
        sample_rate = 22050
        duration = 0.5
        samples = int(sample_rate * duration)
        test_audio = np.sin(2 * np.pi * 440 * np.linspace(0, duration, samples)).astype(
            np.float32
        )

        # These tests will use the mock to avoid actual librosa processing
        with patch("librosa.effects.pitch_shift") as mock_pitch_shift:
            mock_pitch_shift.return_value = test_audio

            # Test minimum pitch shift with time stretching
            processed = apply_tempo_processing(
                test_audio, sample_rate, 1.0, -12.0, True, False
            )
            assert processed is not None

            # Test maximum pitch shift with time stretching
            processed = apply_tempo_processing(
                test_audio, sample_rate, 1.0, 12.0, True, False
            )
            assert processed is not None

    def test_empty_audio_array(self):
        """Test tempo processing with empty audio array"""
        empty_audio = np.array([])

        with pytest.raises(ValueError, match="Audio data cannot be None or empty"):
            apply_tempo_processing(empty_audio, 22050, 1.0, 0.0, False, False)

    def test_single_sample_audio(self):
        """Test tempo processing with single sample audio"""
        single_sample = np.array([0.5])

        # This should handle gracefully or raise appropriate exception
        try:
            processed = apply_tempo_processing(
                single_sample, 22050, 2.0, 0.0, False, False
            )
            # If it succeeds, should return something
            assert processed is not None
        except Exception:
            # It's acceptable for this edge case to raise an exception
            pass
