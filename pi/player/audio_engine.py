import numpy as np

STEM_TYPES = ["vocals", "drums", "bass", "guitar", "piano", "other"]
NUM_STEMS = 6


class MixerState:
    """Shared state for the mixer.

    Thread safety relies on CPython's GIL for simple attribute reads/writes.
    No lock is used because mix_frames runs in a real-time audio callback
    where locking risks priority inversion. The worst case is a single buffer
    (~23ms) seeing a partially updated state, which is inaudible.
    """

    def __init__(self):
        self.fader_values: list[float] = [1.0] * NUM_STEMS
        self.mute_states: list[bool] = [False] * NUM_STEMS
        self.solo_states: list[bool] = [False] * NUM_STEMS
        self.master_volume: float = 1.0
        self.playing: bool = False

    def set_fader(self, index: int, value: float):
        self.fader_values[index] = max(0.0, min(1.0, value))

    def toggle_mute(self, index: int):
        self.mute_states[index] = not self.mute_states[index]

    def toggle_solo(self, index: int):
        if self.solo_states[index]:
            self.solo_states[index] = False
        else:
            # Exclusive solo — clear others
            for i in range(NUM_STEMS):
                self.solo_states[i] = False
            self.solo_states[index] = True


class AudioEngine:
    """Mixes 6 stems based on MixerState. Used by sounddevice callback."""

    def __init__(self):
        self.state = MixerState()
        self.stems: list[np.ndarray] = []  # 6 numpy arrays, each (frames, 2)
        self.num_frames: int = 0
        self.position: int = 0
        self._pending_seek: int | None = None  # Set by seek(), consumed by mix_frames()
        self.sample_rate: int = 44100

    def load_stems(self, stems_dict: dict[str, np.ndarray]):
        """Load stems from a dict keyed by stem type. All must be same length."""
        self.stems = []
        for stem_type in STEM_TYPES:
            if stem_type in stems_dict:
                self.stems.append(stems_dict[stem_type])
            else:
                # Missing stem -> silence
                ref = next(iter(stems_dict.values()))
                self.stems.append(np.zeros_like(ref))

        self.num_frames = self.stems[0].shape[0]
        self.position = 0

    def seek(self, frame: int):
        """Request a seek — applied atomically by the next mix_frames call."""
        self._pending_seek = max(0, min(frame, self.num_frames - 1))

    def mix_frames(self, count: int) -> np.ndarray:
        """Mix `count` frames from current position. Returns (count, 2) array.

        This method owns the playback position entirely — it reads, advances,
        and applies pending seeks atomically within the audio callback thread.
        """
        # Apply pending seek atomically
        pending = self._pending_seek
        if pending is not None:
            self.position = pending
            self._pending_seek = None

        start = self.position

        if not self.state.playing or not self.stems:
            self.position = start + count
            return np.zeros((count, 2), dtype=np.float32)

        channels = 2
        output = np.zeros((count, channels), dtype=np.float32)

        # How many real frames we can read
        available = min(count, self.num_frames - start)
        if available <= 0:
            self.state.playing = False
            self.position = start + count
            return output

        any_soloed = any(self.state.solo_states)

        for i in range(NUM_STEMS):
            if any_soloed:
                if not self.state.solo_states[i]:
                    continue
            else:
                if self.state.mute_states[i]:
                    continue

            fader = self.state.fader_values[i]
            output[:available] += self.stems[i][start:start + available] * fader

        output *= self.state.master_volume

        if available < count:
            self.state.playing = False

        self.position = start + count
        return output

    @property
    def duration_seconds(self) -> float:
        if self.num_frames == 0:
            return 0.0
        return self.num_frames / self.sample_rate

    @property
    def position_seconds(self) -> float:
        return self.position / self.sample_rate
