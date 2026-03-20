import numpy as np
import pytest
from unittest.mock import patch, MagicMock

from audio_engine import AudioEngine, MixerState


class TestMixerState:
    def test_initial_state(self):
        state = MixerState()
        assert len(state.fader_values) == 6
        assert all(v == 1.0 for v in state.fader_values)
        assert all(not m for m in state.mute_states)
        assert all(not s for s in state.solo_states)
        assert state.master_volume == 1.0
        assert state.playing is False

    def test_set_fader(self):
        state = MixerState()
        state.set_fader(0, 0.5)
        assert state.fader_values[0] == 0.5

    def test_toggle_mute(self):
        state = MixerState()
        state.toggle_mute(2)
        assert state.mute_states[2] is True
        state.toggle_mute(2)
        assert state.mute_states[2] is False

    def test_toggle_solo(self):
        state = MixerState()
        state.toggle_solo(1)
        assert state.solo_states[1] is True
        # Solo is exclusive — toggling another clears the first
        state.toggle_solo(3)
        assert state.solo_states[1] is False
        assert state.solo_states[3] is True
        # Toggle same to unsolo
        state.toggle_solo(3)
        assert state.solo_states[3] is False

    def test_fader_clamps(self):
        state = MixerState()
        state.set_fader(0, -0.5)
        assert state.fader_values[0] == 0.0
        state.set_fader(0, 1.5)
        assert state.fader_values[0] == 1.0


class TestAudioEngine:
    def make_test_stems(self, num_frames=44100, num_channels=2):
        """Create 6 constant-value stereo stems for predictable mixing."""
        stems = {}
        types = ["vocals", "drums", "bass", "guitar", "piano", "other"]
        for i, stem_type in enumerate(types):
            # Each stem is a constant value: 0.1, 0.2, 0.3, 0.4, 0.5, 0.6
            val = (i + 1) * 0.1
            stems[stem_type] = np.full((num_frames, num_channels), val, dtype=np.float32)
        return stems

    def test_mix_all_faders_up(self):
        engine = AudioEngine()
        stems = self.make_test_stems(num_frames=1024)
        engine.load_stems(stems)
        engine.state.playing = True

        # All faders at 1.0, no mute/solo — output = sum of all stems
        output = engine.mix_frames(512)
        expected = sum((i + 1) * 0.1 for i in range(6))  # 2.1
        np.testing.assert_allclose(output[0, 0], expected, atol=1e-5)

    def test_mix_with_mute(self):
        engine = AudioEngine()
        stems = self.make_test_stems(num_frames=1024)
        engine.load_stems(stems)
        engine.state.playing = True
        engine.state.toggle_mute(0)  # Mute vocals (0.1)

        output = engine.mix_frames(512)
        expected = sum((i + 1) * 0.1 for i in range(6)) - 0.1  # 2.0
        np.testing.assert_allclose(output[0, 0], expected, atol=1e-5)

    def test_mix_with_solo(self):
        engine = AudioEngine()
        stems = self.make_test_stems(num_frames=1024)
        engine.load_stems(stems)
        engine.state.playing = True
        engine.state.toggle_solo(1)  # Solo drums (0.2)

        output = engine.mix_frames(512)
        expected = 0.2
        np.testing.assert_allclose(output[0, 0], expected, atol=1e-5)

    def test_mix_with_master_volume(self):
        engine = AudioEngine()
        stems = self.make_test_stems(num_frames=1024)
        engine.load_stems(stems)
        engine.state.playing = True
        engine.state.master_volume = 0.5

        output = engine.mix_frames(512)
        expected = 2.1 * 0.5  # 1.05
        np.testing.assert_allclose(output[0, 0], expected, atol=1e-5)

    def test_mix_with_fader_scaled(self):
        engine = AudioEngine()
        stems = self.make_test_stems(num_frames=1024)
        engine.load_stems(stems)
        engine.state.playing = True
        engine.state.set_fader(0, 0.5)  # Vocals at half

        output = engine.mix_frames(512)
        expected = 0.1 * 0.5 + sum((i + 1) * 0.1 for i in range(1, 6))  # 0.05 + 2.0
        np.testing.assert_allclose(output[0, 0], expected, atol=1e-5)

    def test_not_playing_outputs_silence(self):
        engine = AudioEngine()
        stems = self.make_test_stems(num_frames=1024)
        engine.load_stems(stems)
        # state.playing is False by default

        output = engine.mix_frames(512)
        np.testing.assert_allclose(output, 0.0)

    def test_playback_position_advances(self):
        engine = AudioEngine()
        stems = self.make_test_stems(num_frames=1024)
        engine.load_stems(stems)
        engine.state.playing = True

        engine.mix_frames(512)
        assert engine.position == 512
        engine.mix_frames(512)
        assert engine.position == 1024

    def test_playback_stops_at_end(self):
        engine = AudioEngine()
        stems = self.make_test_stems(num_frames=100)
        engine.load_stems(stems)
        engine.state.playing = True

        output = engine.mix_frames(200)
        # Should be zero-padded after frame 100
        assert output.shape[0] == 200
        assert engine.state.playing is False
