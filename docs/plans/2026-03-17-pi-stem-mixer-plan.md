# Pi Stem Mixer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a hardware stem mixer on Raspberry Pi 5 that receives stems from WavDash over Tailscale and provides real-time mixing with physical faders.

**Architecture:** WavDash (MacBook/Docker) auto-pushes OGG stems to Pi via HTTP. Pi runs two services: a FastAPI receiver (port 9000) and a Python player app with threaded audio/hardware/UI. Laravel dispatches a PushStemsToDevice job after all stem conversions complete.

**Tech Stack:** Laravel 12 (PHP), FastAPI (Python), sounddevice/numpy (audio), Adafruit Blinka/seesaw (hardware I/O), Pillow (TFT rendering)

**Design Doc:** `docs/plans/2026-03-17-pi-stem-mixer-design.md`

---

## Task 1: Hardware Assembly & Validation ✅ DONE

**Status:** Complete (2026-03-18). Hardware assembled and all controls validated.

**Hardware verified working:**
- Custom PCB with seesaw at `0x49`: 6 faders (pins 0,1,2,3,6,7), 6 buttons (pins 19,18,14,13,12,9), 12 NeoPixels (pin 20)
- ANO Rotary Encoder at `0x4A`: rotary position + 5 buttons (select/up/left/down/right on pins 1-5)
- TFT Bonnet (ST7789 240x240): display + joystick (GPIO D17/D22/D27/D23/D4) + buttons A/B (GPIO D5/D6)
- Behringer UM2 USB audio output
- Audio playback tested with pydub

**Test scripts (validated):**
- `pi/main.py` — Full hardware test: PCB faders/buttons/LEDs + ANO encoder + audio playback
- `pi/rotary_encoder_example.py` — ANO encoder standalone test
- `pi/bonnet_example.py` — TFT bonnet display + joystick/button test

> **Note:** The original plan assumed two KB2040 boards with custom I2C peripheral firmware. The actual hardware uses a single seesaw (ATTiny8x7) on the custom PCB, which is simpler — no separate firmware is needed. The seesaw is controlled directly from the Pi using `adafruit-circuitpython-seesaw`.

---

## Dev Workflow: Code Sync to Pi

All Pi code lives locally in `pi/` and is synced to the Raspberry Pi for execution and testing. The Pi already has a working Python venv with hardware dependencies installed.

**Connection:**
- Host: `aannecchiarico@raspberrypi.local`
- Target dir: `/home/aannecchiarico/wavdash/`
- Venv: `/home/aannecchiarico/venv/`

**Makefile targets (from repo root):**

| Command | Description |
|---------|-------------|
| `make pi-sync` | rsync `pi/` → Pi's `~/wavdash/` (excludes `__pycache__`, `.pytest_cache`) |
| `make pi-ssh` | Open an SSH shell on the Pi |
| `make pi-test` | Sync + run `pytest -v` on Pi |
| `make pi-run` | Sync + run `main.py` on Pi |
| `make pi-receiver` | Sync + start the FastAPI receiver on Pi (port 9000) |

**Workflow for each task:**
1. Write/edit code locally in `pi/`
2. Run `make pi-sync` to push changes to Pi
3. Run `make pi-test` to execute tests on Pi (or `make pi-ssh` for interactive debugging)
4. Iterate until tests pass, then commit locally

**SSH key setup (recommended) ✅ COMPLETED:** To avoid typing the password on every sync/test:
```bash
ssh-copy-id aannecchiarico@raspberrypi.local
# Enter password once, then all future connections are passwordless
```

> **For Claude agents:** When implementing tasks that need Pi execution, use `make pi-sync` after writing code and `make pi-test` to validate. For interactive hardware testing, describe what the user should verify manually via `make pi-ssh`.

---

## Task 2: Pi Receiver Service

FastAPI service on Pi that accepts stem uploads from WavDash.

**Files:**
- Create: `pi/receiver/main.py`
- Create: `pi/receiver/requirements.txt`
- Create: `pi/receiver/test_receiver.py`

**Step 1: Write the failing tests**

```python
# pi/receiver/test_receiver.py
import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


@pytest.fixture
def stems_dir(tmp_path):
    """Use a temp directory for stem storage during tests."""
    os.environ["WAVDASH_STEMS_DIR"] = str(tmp_path)
    yield tmp_path


@pytest.fixture
def client(stems_dir):
    # Import after setting env var
    from main import app
    return TestClient(app)


def make_ogg_bytes():
    """Return minimal bytes to simulate an OGG file."""
    return b"fake-ogg-data-for-testing"


class TestCreateSong:
    def test_create_song(self, client):
        response = client.post("/api/songs", json={
            "title": "Test Song",
            "artist": "Test Artist",
            "bpm": 120.0,
            "duration": 210.5,
        })
        assert response.status_code == 201
        data = response.json()
        assert "song_id" in data
        assert data["title"] == "Test Song"

    def test_create_song_missing_title(self, client):
        response = client.post("/api/songs", json={
            "artist": "Test Artist",
        })
        assert response.status_code == 422


class TestUploadStem:
    def test_upload_stem(self, client, stems_dir):
        # Create song first
        resp = client.post("/api/songs", json={
            "title": "Test Song",
            "artist": "Test",
            "bpm": 120.0,
            "duration": 200.0,
        })
        song_id = resp.json()["song_id"]

        # Upload a stem
        response = client.post(
            f"/api/songs/{song_id}/stems",
            data={"stem_type": "vocals"},
            files={"file": ("vocals.ogg", make_ogg_bytes(), "audio/ogg")},
        )
        assert response.status_code == 201
        assert response.json()["stem_type"] == "vocals"

        # Verify file exists on disk
        stem_path = stems_dir / "songs" / song_id / "vocals.ogg"
        assert stem_path.exists()

    def test_upload_stem_invalid_type(self, client):
        resp = client.post("/api/songs", json={
            "title": "Test",
            "artist": "Test",
            "bpm": 120.0,
            "duration": 200.0,
        })
        song_id = resp.json()["song_id"]

        response = client.post(
            f"/api/songs/{song_id}/stems",
            data={"stem_type": "invalid"},
            files={"file": ("bad.ogg", make_ogg_bytes(), "audio/ogg")},
        )
        assert response.status_code == 422

    def test_upload_stem_song_not_found(self, client):
        response = client.post(
            "/api/songs/nonexistent/stems",
            data={"stem_type": "vocals"},
            files={"file": ("vocals.ogg", make_ogg_bytes(), "audio/ogg")},
        )
        assert response.status_code == 404


class TestListSongs:
    def test_list_songs_empty(self, client):
        response = client.get("/api/songs")
        assert response.status_code == 200
        assert response.json() == []

    def test_list_songs_with_entries(self, client):
        client.post("/api/songs", json={
            "title": "Song A",
            "artist": "Artist",
            "bpm": 128.0,
            "duration": 180.0,
        })
        client.post("/api/songs", json={
            "title": "Song B",
            "artist": "Artist",
            "bpm": 140.0,
            "duration": 200.0,
        })
        response = client.get("/api/songs")
        assert response.status_code == 200
        assert len(response.json()) == 2


class TestDeleteSong:
    def test_delete_song(self, client, stems_dir):
        resp = client.post("/api/songs", json={
            "title": "To Delete",
            "artist": "Test",
            "bpm": 120.0,
            "duration": 200.0,
        })
        song_id = resp.json()["song_id"]

        # Upload a stem so there are files to delete
        client.post(
            f"/api/songs/{song_id}/stems",
            data={"stem_type": "drums"},
            files={"file": ("drums.ogg", make_ogg_bytes(), "audio/ogg")},
        )

        response = client.delete(f"/api/songs/{song_id}")
        assert response.status_code == 200

        # Verify files removed
        assert not (stems_dir / "songs" / song_id).exists()

        # Verify not in listing
        listing = client.get("/api/songs").json()
        assert len(listing) == 0

    def test_delete_nonexistent(self, client):
        response = client.delete("/api/songs/nonexistent")
        assert response.status_code == 404
```

**Step 2: Run tests to verify they fail**

Run locally: `cd pi/receiver && pip install fastapi uvicorn python-multipart pytest httpx && pytest test_receiver.py -v`
Or on Pi: `make pi-sync && make pi-test`
Expected: FAIL (main.py doesn't exist yet)

**Step 3: Write the receiver implementation**

```python
# pi/receiver/main.py
import json
import os
import shutil
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

app = FastAPI(title="WavDash Stem Receiver")

VALID_STEM_TYPES = {"vocals", "drums", "bass", "guitar", "piano", "other"}


def get_stems_dir() -> Path:
    d = Path(os.environ.get("WAVDASH_STEMS_DIR", os.path.expanduser("~/wavdash-stems")))
    d.mkdir(parents=True, exist_ok=True)
    return d


def get_songs_index_path() -> Path:
    return get_stems_dir() / "songs.json"


def load_songs_index() -> list[dict]:
    path = get_songs_index_path()
    if not path.exists():
        return []
    with open(path) as f:
        return json.load(f)


def save_songs_index(songs: list[dict]):
    with open(get_songs_index_path(), "w") as f:
        json.dump(songs, f, indent=2)


class CreateSongRequest(BaseModel):
    title: str
    artist: Optional[str] = None
    bpm: Optional[float] = None
    duration: Optional[float] = None


class CreateSongResponse(BaseModel):
    song_id: str
    title: str
    artist: Optional[str] = None
    bpm: Optional[float] = None
    duration: Optional[float] = None


class StemUploadResponse(BaseModel):
    song_id: str
    stem_type: str
    message: str


@app.post("/api/songs", status_code=201, response_model=CreateSongResponse)
def create_song(req: CreateSongRequest):
    song_id = uuid.uuid4().hex[:12]
    song_dir = get_stems_dir() / "songs" / song_id
    song_dir.mkdir(parents=True, exist_ok=True)

    meta = {
        "song_id": song_id,
        "title": req.title,
        "artist": req.artist,
        "bpm": req.bpm,
        "duration": req.duration,
        "stems": [],
    }
    with open(song_dir / "meta.json", "w") as f:
        json.dump(meta, f, indent=2)

    songs = load_songs_index()
    songs.append({"song_id": song_id, "title": req.title, "artist": req.artist, "bpm": req.bpm, "duration": req.duration})
    save_songs_index(songs)

    return CreateSongResponse(song_id=song_id, **req.model_dump())


@app.post("/api/songs/{song_id}/stems", status_code=201, response_model=StemUploadResponse)
async def upload_stem(
    song_id: str,
    stem_type: str = Form(...),
    file: UploadFile = File(...),
):
    if stem_type not in VALID_STEM_TYPES:
        raise HTTPException(status_code=422, detail=f"Invalid stem_type: {stem_type}. Must be one of {VALID_STEM_TYPES}")

    song_dir = get_stems_dir() / "songs" / song_id
    if not song_dir.exists():
        raise HTTPException(status_code=404, detail=f"Song {song_id} not found")

    stem_path = song_dir / f"{stem_type}.ogg"
    with open(stem_path, "wb") as f:
        content = await file.read()
        f.write(content)

    # Update meta.json stems list
    meta_path = song_dir / "meta.json"
    with open(meta_path) as f:
        meta = json.load(f)
    if stem_type not in meta["stems"]:
        meta["stems"].append(stem_type)
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)

    return StemUploadResponse(song_id=song_id, stem_type=stem_type, message="Stem uploaded")


@app.get("/api/songs")
def list_songs():
    return load_songs_index()


@app.delete("/api/songs/{song_id}")
def delete_song(song_id: str):
    song_dir = get_stems_dir() / "songs" / song_id
    if not song_dir.exists():
        raise HTTPException(status_code=404, detail=f"Song {song_id} not found")

    shutil.rmtree(song_dir)

    songs = load_songs_index()
    songs = [s for s in songs if s["song_id"] != song_id]
    save_songs_index(songs)

    return {"message": f"Song {song_id} deleted"}
```

```
# pi/receiver/requirements.txt
fastapi==0.115.*
uvicorn[standard]==0.34.*
python-multipart==0.0.*
pytest==8.*
httpx==0.28.*
```

**Step 4: Run tests to verify they pass**

Run locally: `cd pi/receiver && pytest test_receiver.py -v`
Or on Pi: `make pi-test`
Expected: All 7 tests PASS

**Step 5: Commit**

```bash
git add -f pi/receiver/
git commit -m "feat(pi): add FastAPI stem receiver service with tests"
```

---

## Task 3: Pi Player — Audio Engine

The core audio mixing engine. Testable without hardware using mock data.

**Files:**
- Create: `pi/player/audio_engine.py`
- Create: `pi/player/test_audio_engine.py`
- Create: `pi/player/requirements.txt`

**Step 1: Write the failing tests**

```python
# pi/player/test_audio_engine.py
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
        output = engine.mix_frames(0, 512)
        expected = sum((i + 1) * 0.1 for i in range(6))  # 2.1
        np.testing.assert_allclose(output[0, 0], expected, atol=1e-5)

    def test_mix_with_mute(self):
        engine = AudioEngine()
        stems = self.make_test_stems(num_frames=1024)
        engine.load_stems(stems)
        engine.state.playing = True
        engine.state.toggle_mute(0)  # Mute vocals (0.1)

        output = engine.mix_frames(0, 512)
        expected = sum((i + 1) * 0.1 for i in range(6)) - 0.1  # 2.0
        np.testing.assert_allclose(output[0, 0], expected, atol=1e-5)

    def test_mix_with_solo(self):
        engine = AudioEngine()
        stems = self.make_test_stems(num_frames=1024)
        engine.load_stems(stems)
        engine.state.playing = True
        engine.state.toggle_solo(1)  # Solo drums (0.2)

        output = engine.mix_frames(0, 512)
        expected = 0.2
        np.testing.assert_allclose(output[0, 0], expected, atol=1e-5)

    def test_mix_with_master_volume(self):
        engine = AudioEngine()
        stems = self.make_test_stems(num_frames=1024)
        engine.load_stems(stems)
        engine.state.playing = True
        engine.state.master_volume = 0.5

        output = engine.mix_frames(0, 512)
        expected = 2.1 * 0.5  # 1.05
        np.testing.assert_allclose(output[0, 0], expected, atol=1e-5)

    def test_mix_with_fader_scaled(self):
        engine = AudioEngine()
        stems = self.make_test_stems(num_frames=1024)
        engine.load_stems(stems)
        engine.state.playing = True
        engine.state.set_fader(0, 0.5)  # Vocals at half

        output = engine.mix_frames(0, 512)
        expected = 0.1 * 0.5 + sum((i + 1) * 0.1 for i in range(1, 6))  # 0.05 + 2.0
        np.testing.assert_allclose(output[0, 0], expected, atol=1e-5)

    def test_not_playing_outputs_silence(self):
        engine = AudioEngine()
        stems = self.make_test_stems(num_frames=1024)
        engine.load_stems(stems)
        # state.playing is False by default

        output = engine.mix_frames(0, 512)
        np.testing.assert_allclose(output, 0.0)

    def test_playback_position_advances(self):
        engine = AudioEngine()
        stems = self.make_test_stems(num_frames=1024)
        engine.load_stems(stems)
        engine.state.playing = True

        engine.mix_frames(0, 512)
        assert engine.position == 512
        engine.mix_frames(512, 512)
        assert engine.position == 1024

    def test_playback_stops_at_end(self):
        engine = AudioEngine()
        stems = self.make_test_stems(num_frames=100)
        engine.load_stems(stems)
        engine.state.playing = True

        output = engine.mix_frames(0, 200)
        # Should be zero-padded after frame 100
        assert output.shape[0] == 200
        assert engine.state.playing is False
```

**Step 2: Run tests to verify they fail**

Run: `cd pi/player && pip install numpy pytest && pytest test_audio_engine.py -v`
Expected: FAIL (audio_engine.py doesn't exist)

**Step 3: Write the audio engine**

```python
# pi/player/audio_engine.py
import threading
from dataclasses import dataclass, field

import numpy as np

STEM_TYPES = ["vocals", "drums", "bass", "guitar", "piano", "other"]
NUM_STEMS = 6


class MixerState:
    """Thread-safe shared state for the mixer."""

    def __init__(self):
        self._lock = threading.Lock()
        self.fader_values: list[float] = [1.0] * NUM_STEMS
        self.mute_states: list[bool] = [False] * NUM_STEMS
        self.solo_states: list[bool] = [False] * NUM_STEMS
        self.master_volume: float = 1.0
        self.playing: bool = False

    def set_fader(self, index: int, value: float):
        with self._lock:
            self.fader_values[index] = max(0.0, min(1.0, value))

    def toggle_mute(self, index: int):
        with self._lock:
            self.mute_states[index] = not self.mute_states[index]

    def toggle_solo(self, index: int):
        with self._lock:
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

    def mix_frames(self, start: int, count: int) -> np.ndarray:
        """Mix `count` frames from position `start`. Returns (count, 2) array."""
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
```

```
# pi/player/requirements.txt
numpy==2.*
sounddevice==0.5.*
soundfile==0.13.*
adafruit-blinka==8.*
adafruit-circuitpython-seesaw==1.*
adafruit-circuitpython-rgb-display==4.*
Pillow==11.*
pytest==8.*
```

**Step 4: Run tests to verify they pass**

Run: `cd pi/player && pytest test_audio_engine.py -v`
Expected: All 9 tests PASS

**Step 5: Commit**

```bash
git add -f pi/player/audio_engine.py pi/player/test_audio_engine.py pi/player/requirements.txt
git commit -m "feat(pi): add audio mixing engine with tests"
```

---

## Task 4: Pi Player — Hardware I/O

Reads PCB seesaw (faders, buttons, LEDs) and ANO encoder over I2C. Detects button short/long press.

**Files:**
- Create: `pi/player/hardware.py`
- Create: `pi/player/test_hardware.py`

**Step 1: Write the failing tests**

```python
# pi/player/test_hardware.py
import time
from unittest.mock import MagicMock, patch

import pytest

from hardware import ButtonHandler


class TestButtonHandler:
    def test_short_press_detected(self):
        on_short = MagicMock()
        on_long = MagicMock()
        handler = ButtonHandler(on_short_press=on_short, on_long_press=on_long, long_press_ms=500)

        handler.update(pressed=True, now=0.0)
        handler.update(pressed=False, now=0.2)  # Released after 200ms -> short press

        on_short.assert_called_once()
        on_long.assert_not_called()

    def test_long_press_detected(self):
        on_short = MagicMock()
        on_long = MagicMock()
        handler = ButtonHandler(on_short_press=on_short, on_long_press=on_long, long_press_ms=500)

        handler.update(pressed=True, now=0.0)
        handler.update(pressed=True, now=0.3)
        handler.update(pressed=True, now=0.6)  # Still held at 600ms -> long press fires
        handler.update(pressed=False, now=0.7)  # Release after long press — no short press

        on_long.assert_called_once()
        on_short.assert_not_called()

    def test_no_press_no_callbacks(self):
        on_short = MagicMock()
        on_long = MagicMock()
        handler = ButtonHandler(on_short_press=on_short, on_long_press=on_long)

        handler.update(pressed=False, now=0.0)
        handler.update(pressed=False, now=0.5)

        on_short.assert_not_called()
        on_long.assert_not_called()
```

**Step 2: Run tests to verify they fail**

Run: `cd pi/player && pytest test_hardware.py -v`
Expected: FAIL (hardware.py doesn't exist)

**Step 3: Write the hardware controller**

```python
# pi/player/hardware.py
"""Hardware I/O for the Pi Stem Mixer.

Uses Adafruit seesaw library to communicate with:
- Custom PCB seesaw (0x49): 6 faders, 6 buttons, 12 NeoPixels
- ANO Rotary Encoder seesaw (0x4A): rotary encoder + 5 buttons

Uses GPIO (via digitalio) for TFT bonnet joystick/buttons.
"""
import time
from typing import Callable, Optional

try:
    import board
    from adafruit_seesaw.seesaw import Seesaw
    from adafruit_seesaw.analoginput import AnalogInput
    from adafruit_seesaw.digitalio import DigitalIO
    from adafruit_seesaw.neopixel import NeoPixel
    from adafruit_seesaw.rotaryio import IncrementalEncoder
    import digitalio
    HAS_HARDWARE = True
except ImportError:
    HAS_HARDWARE = False

# I2C addresses
PCB_SEESAW_ADDR = 0x49  # Default seesaw address for custom PCB
ANO_ENCODER_ADDR = 0x4A  # ANO rotary encoder

# PCB seesaw pin assignments
SLIDER_PINS = [0, 1, 2, 3, 6, 7]  # Analog pins for 6 faders
BUTTON_PINS = [19, 18, 14, 13, 12, 9]  # Digital pins for 6 buttons
NEOPIXEL_PIN = 20  # NeoPixel data pin
NEOPIXEL_COUNT = 12  # 2 LEDs per fader

# ANO encoder seesaw pin assignments
ANO_SELECT_PIN = 1
ANO_UP_PIN = 2
ANO_LEFT_PIN = 3
ANO_DOWN_PIN = 4
ANO_RIGHT_PIN = 5

NUM_STEMS = 6


class ButtonHandler:
    """Detects short press vs long press on a single button."""

    def __init__(
        self,
        on_short_press: Callable = lambda: None,
        on_long_press: Callable = lambda: None,
        long_press_ms: int = 500,
    ):
        self.on_short_press = on_short_press
        self.on_long_press = on_long_press
        self.long_press_s = long_press_ms / 1000.0
        self._pressed = False
        self._press_start: float = 0.0
        self._long_fired = False

    def update(self, pressed: bool, now: float):
        if pressed and not self._pressed:
            # Just pressed
            self._press_start = now
            self._long_fired = False
        elif pressed and self._pressed:
            # Held down — check for long press
            if not self._long_fired and (now - self._press_start) >= self.long_press_s:
                self.on_long_press()
                self._long_fired = True
        elif not pressed and self._pressed:
            # Just released
            if not self._long_fired:
                self.on_short_press()

        self._pressed = pressed


class HardwareController:
    """Reads faders, buttons, rotary encoder via I2C seesaw. Writes LED colors."""

    def __init__(self):
        if not HAS_HARDWARE:
            raise RuntimeError("Hardware libraries not available — are you on a Raspberry Pi?")

        i2c = board.I2C()

        # PCB seesaw — faders, buttons, LEDs
        self.pcb = Seesaw(i2c)  # default addr 0x49

        # Set up analog inputs for faders
        self.sliders = []
        for pin in SLIDER_PINS:
            self.sliders.append(AnalogInput(self.pcb, pin))

        # Set up digital inputs for buttons (pull-up, active low)
        self.buttons = []
        for pin in BUTTON_PINS:
            btn = DigitalIO(self.pcb, pin)
            btn.direction = digitalio.Direction.INPUT
            btn.pull = digitalio.Pull.UP
            self.buttons.append(btn)

        # Set up NeoPixels
        self.pixels = NeoPixel(self.pcb, NEOPIXEL_PIN, NEOPIXEL_COUNT)
        self.pixels.brightness = 0.3

        # ANO rotary encoder seesaw
        self.ano = Seesaw(i2c, addr=ANO_ENCODER_ADDR)

        # Set up ANO buttons (pull-up, active low)
        for pin in [ANO_SELECT_PIN, ANO_UP_PIN, ANO_LEFT_PIN, ANO_DOWN_PIN, ANO_RIGHT_PIN]:
            self.ano.pin_mode(pin, self.ano.INPUT_PULLUP)

        self.ano_select = DigitalIO(self.ano, ANO_SELECT_PIN)
        self.ano_up = DigitalIO(self.ano, ANO_UP_PIN)
        self.ano_left = DigitalIO(self.ano, ANO_LEFT_PIN)
        self.ano_down = DigitalIO(self.ano, ANO_DOWN_PIN)
        self.ano_right = DigitalIO(self.ano, ANO_RIGHT_PIN)

        # Set up rotary encoder
        self.encoder = IncrementalEncoder(self.ano)
        self._last_encoder_pos = self.encoder.position

    def read_faders(self) -> list[float]:
        """Read 6 fader values (0.0–1.0) from PCB seesaw analog inputs."""
        faders = []
        for slider in self.sliders:
            # AnalogInput returns 0–1023
            raw = slider.value
            faders.append(raw / 1023.0)
        return faders

    def read_buttons(self) -> list[bool]:
        """Read 6 button states from PCB seesaw. True = pressed (active low)."""
        return [not btn.value for btn in self.buttons]

    def read_encoder_delta(self) -> int:
        """Read rotary encoder position change since last call."""
        pos = self.encoder.position
        delta = pos - self._last_encoder_pos
        self._last_encoder_pos = pos
        return delta

    def read_encoder_select(self) -> bool:
        """Read ANO center/select button. True = pressed."""
        return not self.ano_select.value

    def read_ano_buttons(self) -> dict[str, bool]:
        """Read ANO directional buttons. Returns dict with True = pressed."""
        return {
            "select": not self.ano_select.value,
            "up": not self.ano_up.value,
            "left": not self.ano_left.value,
            "down": not self.ano_down.value,
            "right": not self.ano_right.value,
        }

    def update_leds(self, mixer_state):
        """Update all 12 NeoPixels based on mixer state.

        LED mapping: 2 LEDs per fader (pixel 0,1 = fader 0; pixel 2,3 = fader 1; etc.)
        """
        for stem_idx in range(NUM_STEMS):
            if mixer_state.solo_states[stem_idx]:
                color = (0, 0, 255)  # Blue
            elif mixer_state.mute_states[stem_idx]:
                color = (255, 0, 0)  # Red
            elif mixer_state.playing:
                brightness = int(mixer_state.fader_values[stem_idx] * 255)
                color = (0, brightness, 0)  # Green, brightness follows fader
            else:
                color = (30, 30, 30)  # Dim white

            # Each fader has 2 LEDs
            self.pixels[stem_idx * 2] = color
            self.pixels[stem_idx * 2 + 1] = color
```

**Step 4: Run tests to verify they pass**

Run: `cd pi/player && pytest test_hardware.py -v`
Expected: All 3 tests PASS (ButtonHandler tests — HardwareController requires real hardware)

**Step 5: Commit**

```bash
git add -f pi/player/hardware.py pi/player/test_hardware.py
git commit -m "feat(pi): add seesaw-based hardware controller with button handler"
```

---

## Task 5: Pi Player — Song Library

Reads the `~/wavdash-stems/` directory and loads OGG files into the audio engine.

**Files:**
- Create: `pi/player/song_library.py`
- Create: `pi/player/test_song_library.py`

**Step 1: Write the failing tests**

```python
# pi/player/test_song_library.py
import json
import os
from pathlib import Path

import pytest

from song_library import SongLibrary, Song


@pytest.fixture
def stems_dir(tmp_path):
    """Create a temp stems directory with test songs."""
    songs_dir = tmp_path / "songs"
    songs_dir.mkdir()

    # Create two test songs
    for song_id, title in [("abc123", "Test Song A"), ("def456", "Test Song B")]:
        song_path = songs_dir / song_id
        song_path.mkdir()
        meta = {
            "song_id": song_id,
            "title": title,
            "artist": "Test Artist",
            "bpm": 120.0,
            "duration": 180.0,
            "stems": ["vocals", "drums", "bass", "guitar", "piano", "other"],
        }
        with open(song_path / "meta.json", "w") as f:
            json.dump(meta, f)
        # Create dummy stem files
        for stem in meta["stems"]:
            (song_path / f"{stem}.ogg").write_bytes(b"fake-ogg")

    # Write index
    index = [
        {"song_id": "abc123", "title": "Test Song A", "artist": "Test Artist", "bpm": 120.0, "duration": 180.0},
        {"song_id": "def456", "title": "Test Song B", "artist": "Test Artist", "bpm": 120.0, "duration": 180.0},
    ]
    with open(tmp_path / "songs.json", "w") as f:
        json.dump(index, f)

    return tmp_path


class TestSongLibrary:
    def test_scan_songs(self, stems_dir):
        lib = SongLibrary(stems_dir)
        songs = lib.scan()
        assert len(songs) == 2
        assert songs[0].title == "Test Song A"
        assert songs[1].title == "Test Song B"

    def test_song_has_stem_paths(self, stems_dir):
        lib = SongLibrary(stems_dir)
        songs = lib.scan()
        song = songs[0]
        assert "vocals" in song.stem_paths
        assert song.stem_paths["vocals"].exists()

    def test_empty_directory(self, tmp_path):
        lib = SongLibrary(tmp_path)
        songs = lib.scan()
        assert len(songs) == 0

    def test_rescan_detects_new_songs(self, stems_dir):
        lib = SongLibrary(stems_dir)
        songs = lib.scan()
        assert len(songs) == 2

        # Add a new song
        new_dir = stems_dir / "songs" / "ghi789"
        new_dir.mkdir()
        meta = {"song_id": "ghi789", "title": "New Song", "artist": "New", "bpm": 140.0, "duration": 200.0, "stems": ["vocals"]}
        with open(new_dir / "meta.json", "w") as f:
            json.dump(meta, f)
        (new_dir / "vocals.ogg").write_bytes(b"fake")

        songs = lib.scan()
        assert len(songs) == 3
```

**Step 2: Run tests to verify they fail**

Run: `cd pi/player && pytest test_song_library.py -v`
Expected: FAIL (song_library.py doesn't exist)

**Step 3: Write the song library**

```python
# pi/player/song_library.py
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Song:
    song_id: str
    title: str
    artist: Optional[str] = None
    bpm: Optional[float] = None
    duration: Optional[float] = None
    stem_paths: dict[str, Path] = field(default_factory=dict)


class SongLibrary:
    """Scans the stems directory for available songs."""

    def __init__(self, stems_dir: Path):
        self.stems_dir = Path(stems_dir)
        self.songs: list[Song] = []

    def scan(self) -> list[Song]:
        """Scan the stems directory and return list of available songs."""
        songs_dir = self.stems_dir / "songs"
        if not songs_dir.exists():
            self.songs = []
            return self.songs

        self.songs = []
        for song_path in sorted(songs_dir.iterdir()):
            if not song_path.is_dir():
                continue
            meta_path = song_path / "meta.json"
            if not meta_path.exists():
                continue

            with open(meta_path) as f:
                meta = json.load(f)

            stem_paths = {}
            for stem_type in meta.get("stems", []):
                ogg_path = song_path / f"{stem_type}.ogg"
                if ogg_path.exists():
                    stem_paths[stem_type] = ogg_path

            self.songs.append(Song(
                song_id=meta["song_id"],
                title=meta["title"],
                artist=meta.get("artist"),
                bpm=meta.get("bpm"),
                duration=meta.get("duration"),
                stem_paths=stem_paths,
            ))

        return self.songs
```

**Step 4: Run tests to verify they pass**

Run: `cd pi/player && pytest test_song_library.py -v`
Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add -f pi/player/song_library.py pi/player/test_song_library.py
git commit -m "feat(pi): add song library scanner"
```

---

## Task 6: Pi Player — TFT Display

TFT Bonnet display driver and joystick/button input.

**Files:**
- Create: `pi/player/display.py`

**Step 1: Write the display module**

```python
# pi/player/display.py
"""TFT Bonnet display driver using Pillow + ST7789.

Based on validated bonnet_example.py — uses the same GPIO pin assignments.
"""
from typing import Optional

try:
    import board
    from digitalio import DigitalInOut, Direction
    from adafruit_rgb_display import st7789
    from PIL import Image, ImageDraw, ImageFont
    HAS_DISPLAY = True
except ImportError:
    HAS_DISPLAY = False

from audio_engine import MixerState, STEM_TYPES

# TFT Bonnet GPIO pins (from bonnet_example.py — validated working)
BUTTON_A_PIN = board.D5 if HAS_DISPLAY else None
BUTTON_B_PIN = board.D6 if HAS_DISPLAY else None
JOYSTICK_UP_PIN = board.D17 if HAS_DISPLAY else None
JOYSTICK_DOWN_PIN = board.D22 if HAS_DISPLAY else None
JOYSTICK_LEFT_PIN = board.D27 if HAS_DISPLAY else None
JOYSTICK_RIGHT_PIN = board.D23 if HAS_DISPLAY else None
JOYSTICK_PRESS_PIN = board.D4 if HAS_DISPLAY else None
BACKLIGHT_PIN = board.D26 if HAS_DISPLAY else None

WIDTH = 240
HEIGHT = 240
STEM_LABELS = ["VOC", "DRM", "BAS", "GTR", "PNO", "OTH"]


class Display:
    """Drives the TFT Bonnet display and reads its joystick/buttons."""

    def __init__(self):
        if not HAS_DISPLAY:
            raise RuntimeError("Display libraries not available")

        cs_pin = DigitalInOut(board.CE0)
        dc_pin = DigitalInOut(board.D25)
        reset_pin = DigitalInOut(board.D24)
        spi = board.SPI()

        self.display = st7789.ST7789(
            spi, height=HEIGHT, y_offset=80, rotation=180,
            cs=cs_pin, dc=dc_pin, rst=reset_pin,
            baudrate=24000000,
        )

        # Turn on backlight
        self.backlight = DigitalInOut(BACKLIGHT_PIN)
        self.backlight.switch_to_output()
        self.backlight.value = True

        self._setup_buttons()
        self.image = Image.new("RGB", (WIDTH, HEIGHT), (0, 0, 0))
        self.draw = ImageDraw.Draw(self.image)

        try:
            self.font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 14)
            self.font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf", 18)
        except OSError:
            self.font = ImageFont.load_default()
            self.font_large = self.font

    def _setup_buttons(self):
        self.buttons = {}
        for name, pin in [
            ("a", BUTTON_A_PIN), ("b", BUTTON_B_PIN),
            ("up", JOYSTICK_UP_PIN), ("down", JOYSTICK_DOWN_PIN),
            ("left", JOYSTICK_LEFT_PIN), ("right", JOYSTICK_RIGHT_PIN),
            ("press", JOYSTICK_PRESS_PIN),
        ]:
            dio = DigitalInOut(pin)
            dio.direction = Direction.INPUT
            self.buttons[name] = dio

    def read_buttons(self) -> dict[str, bool]:
        """Read joystick + button states. Returns dict with True = pressed (active low)."""
        return {name: not pin.value for name, pin in self.buttons.items()}

    def render_library(self, songs: list, selected_index: int):
        """Render the song library screen."""
        self.draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(0, 0, 0))

        # Header
        self.draw.text((10, 5), "WavDash Stems", fill=(0, 200, 255), font=self.font_large)
        self.draw.line((0, 28, WIDTH, 28), fill=(60, 60, 60))

        # Song list
        visible_start = max(0, selected_index - 3)
        y = 35
        for i in range(visible_start, min(len(songs), visible_start + 7)):
            song = songs[i]
            prefix = "> " if i == selected_index else "  "
            color = (255, 255, 255) if i == selected_index else (140, 140, 140)
            bpm_str = f" {song.bpm:.0f}bpm" if song.bpm else ""
            text = f"{prefix}{song.title}{bpm_str}"
            self.draw.text((10, y), text[:28], fill=color, font=self.font)
            y += 28

        # Footer
        self.draw.line((0, HEIGHT - 25, WIDTH, HEIGHT - 25), fill=(60, 60, 60))
        self.draw.text((10, HEIGHT - 20), f"{len(songs)} songs", fill=(100, 100, 100), font=self.font)

        self.display.image(self.image)

    def render_now_playing(self, song, mixer_state: MixerState, position_s: float, duration_s: float):
        """Render the now-playing screen with fader levels."""
        self.draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(0, 0, 0))

        # Header
        play_icon = "||" if mixer_state.playing else ">"
        self.draw.text((10, 5), f"{play_icon} {song.title[:18]}", fill=(0, 255, 100), font=self.font_large)
        bpm_str = f"{song.bpm:.0f} BPM" if song.bpm else ""
        self.draw.text((10, 28), bpm_str, fill=(180, 180, 180), font=self.font)
        self.draw.line((0, 48, WIDTH, 48), fill=(60, 60, 60))

        # Stem meters
        y = 55
        bar_width = 120
        any_soloed = any(mixer_state.solo_states)
        for i in range(6):
            label = STEM_LABELS[i]
            fader = mixer_state.fader_values[i]

            if mixer_state.solo_states[i]:
                color = (0, 100, 255)
                status = "SOLO"
            elif mixer_state.mute_states[i]:
                color = (255, 50, 50)
                status = "MUTE"
            elif any_soloed:
                color = (80, 80, 80)
                status = f"{int(fader * 100)}%"
            else:
                color = (0, 200, 80)
                status = f"{int(fader * 100)}%"

            self.draw.text((10, y), label, fill=color, font=self.font)

            # Bar background
            bar_x = 50
            self.draw.rectangle((bar_x, y + 2, bar_x + bar_width, y + 14), fill=(40, 40, 40))
            # Bar fill
            fill_width = int(bar_width * fader)
            if fill_width > 0:
                self.draw.rectangle((bar_x, y + 2, bar_x + fill_width, y + 14), fill=color)

            self.draw.text((bar_x + bar_width + 8, y), status, fill=color, font=self.font)
            y += 26

        # Playback position
        self.draw.line((0, HEIGHT - 30, WIDTH, HEIGHT - 30), fill=(60, 60, 60))
        pos_str = f"{int(position_s // 60):02d}:{int(position_s % 60):02d}"
        dur_str = f"{int(duration_s // 60):02d}:{int(duration_s % 60):02d}"
        self.draw.text((10, HEIGHT - 22), f"{pos_str} / {dur_str}", fill=(180, 180, 180), font=self.font)

        # Progress bar
        if duration_s > 0:
            progress = min(position_s / duration_s, 1.0)
            prog_width = int((WIDTH - 20) * progress)
            self.draw.rectangle((10, HEIGHT - 5, WIDTH - 10, HEIGHT - 2), fill=(40, 40, 40))
            if prog_width > 0:
                self.draw.rectangle((10, HEIGHT - 5, 10 + prog_width, HEIGHT - 2), fill=(0, 200, 255))

        self.display.image(self.image)


class MockDisplay:
    """Stub display for development/testing without hardware."""

    def read_buttons(self) -> dict[str, bool]:
        return {k: False for k in ["a", "b", "up", "down", "left", "right", "press"]}

    def render_library(self, songs, selected_index):
        pass

    def render_now_playing(self, song, mixer_state, position_s, duration_s):
        pass
```

**Step 2: Commit**

```bash
git add -f pi/player/display.py
git commit -m "feat(pi): add TFT bonnet display driver"
```

---

## Task 7: Pi Player — Main Application

Ties together audio engine, hardware I/O, song library, and TFT display into the main threaded application.

**Files:**
- Create: `pi/player/main.py`

**Step 1: Write the main application**

```python
# pi/player/main.py
"""WavDash Stem Mixer — Main application for Raspberry Pi 5."""
import os
import sys
import threading
import time
from pathlib import Path

import numpy as np

try:
    import sounddevice as sd
    import soundfile as sf
except ImportError:
    sd = None
    sf = None

from audio_engine import AudioEngine, STEM_TYPES
from song_library import SongLibrary, Song

# Try hardware imports — fall back for development
try:
    from hardware import HardwareController, ButtonHandler
    HAS_HARDWARE = True
except (ImportError, RuntimeError):
    HAS_HARDWARE = False

try:
    from display import Display
    HAS_DISPLAY = True
except (ImportError, RuntimeError):
    from display import MockDisplay
    HAS_DISPLAY = False

STEMS_DIR = Path(os.environ.get("WAVDASH_STEMS_DIR", os.path.expanduser("~/wavdash-stems")))
POLL_HZ = 60
DISPLAY_FPS = 15
LIBRARY_RESCAN_INTERVAL = 5.0


class StemMixerApp:
    """Main application coordinating audio, hardware, and display."""

    def __init__(self):
        self.engine = AudioEngine()
        self.library = SongLibrary(STEMS_DIR)
        self.songs: list[Song] = []
        self.selected_index = 0
        self.current_song: Song | None = None
        self.screen = "library"  # "library" or "playing"
        self.running = False

        # Hardware
        self.hw: HardwareController | None = None
        if HAS_HARDWARE:
            try:
                self.hw = HardwareController()
            except Exception as e:
                print(f"Hardware init failed: {e}. Running without hardware.")

        # Display
        if HAS_DISPLAY:
            try:
                self.display = Display()
            except Exception as e:
                print(f"Display init failed: {e}. Running without display.")
                self.display = MockDisplay()
        else:
            self.display = MockDisplay()

        # Button handlers for mute/solo (PCB buttons)
        self.button_handlers: list[ButtonHandler] = []
        if HAS_HARDWARE:
            from hardware import ButtonHandler
            for i in range(6):
                handler = ButtonHandler(
                    on_short_press=lambda idx=i: self.engine.state.toggle_mute(idx),
                    on_long_press=lambda idx=i: self.engine.state.toggle_solo(idx),
                )
                self.button_handlers.append(handler)

        # ANO encoder select button handler (play/pause)
        self._ano_select_held = False

    def load_song(self, song: Song):
        """Load a song's stems into the audio engine."""
        if sf is None:
            print("soundfile not available — cannot load audio")
            return

        self.engine.state.playing = False
        stems = {}
        for stem_type in STEM_TYPES:
            if stem_type in song.stem_paths:
                data, sr = sf.read(str(song.stem_paths[stem_type]), dtype="float32")
                if data.ndim == 1:
                    data = np.column_stack([data, data])  # Mono -> stereo
                stems[stem_type] = data
                self.engine.sample_rate = sr

        if stems:
            self.engine.load_stems(stems)
            self.current_song = song
            self.screen = "playing"
            self.engine.state.playing = True
            print(f"Loaded: {song.title}")

    def _audio_callback(self, outdata, frames, time_info, status):
        """sounddevice output callback — called from audio thread."""
        output = self.engine.mix_frames(self.engine.position, frames)
        outdata[:] = output

    def _hardware_loop(self):
        """Hardware I/O polling thread."""
        poll_interval = 1.0 / POLL_HZ
        while self.running:
            now = time.monotonic()

            if self.hw:
                # Read faders from PCB seesaw
                try:
                    faders = self.hw.read_faders()
                    for i, val in enumerate(faders):
                        self.engine.state.set_fader(i, val)
                except Exception:
                    pass

                # Read buttons from PCB seesaw
                try:
                    buttons = self.hw.read_buttons()
                    for i, pressed in enumerate(buttons):
                        self.button_handlers[i].update(pressed, now)
                except Exception:
                    pass

                # Update LEDs on PCB seesaw
                try:
                    self.hw.update_leds(self.engine.state)
                except Exception:
                    pass

                # Read rotary encoder (master volume)
                try:
                    delta = self.hw.read_encoder_delta()
                    if delta != 0:
                        new_vol = self.engine.state.master_volume + delta * 0.02
                        self.engine.state.master_volume = max(0.0, min(1.0, new_vol))
                except Exception:
                    pass

                # ANO select button = play/pause (with debounce)
                try:
                    select_pressed = self.hw.read_encoder_select()
                    if select_pressed and not self._ano_select_held:
                        self.engine.state.playing = not self.engine.state.playing
                    self._ano_select_held = select_pressed
                except Exception:
                    pass

            time.sleep(poll_interval)

    def _display_loop(self):
        """Main thread display + input loop."""
        display_interval = 1.0 / DISPLAY_FPS
        last_rescan = 0.0

        while self.running:
            now = time.monotonic()

            # Periodically rescan library for new songs
            if now - last_rescan > LIBRARY_RESCAN_INTERVAL:
                self.songs = self.library.scan()
                last_rescan = now

            # Read TFT bonnet inputs
            btn = self.display.read_buttons()

            # Also read ANO up/down for library navigation
            ano_btn = {}
            if self.hw:
                try:
                    ano_btn = self.hw.read_ano_buttons()
                except Exception:
                    pass

            if self.screen == "library":
                if (btn.get("down") or ano_btn.get("down")) and self.selected_index < len(self.songs) - 1:
                    self.selected_index += 1
                    time.sleep(0.15)  # Debounce
                elif (btn.get("up") or ano_btn.get("up")) and self.selected_index > 0:
                    self.selected_index -= 1
                    time.sleep(0.15)
                elif btn.get("press") and self.songs:
                    self.load_song(self.songs[self.selected_index])

                self.display.render_library(self.songs, self.selected_index)

            elif self.screen == "playing":
                if btn.get("left") or btn.get("a"):
                    self.engine.state.playing = False
                    self.screen = "library"

                if self.current_song:
                    self.display.render_now_playing(
                        self.current_song,
                        self.engine.state,
                        self.engine.position_seconds,
                        self.engine.duration_seconds,
                    )

                # Auto-return to library when song ends
                if not self.engine.state.playing and self.engine.position >= self.engine.num_frames:
                    self.screen = "library"

            time.sleep(display_interval)

    def run(self):
        """Start the stem mixer application."""
        if sd is None:
            print("sounddevice not available — cannot start audio")
            sys.exit(1)

        self.running = True
        self.songs = self.library.scan()
        print(f"WavDash Stem Mixer — {len(self.songs)} songs found")

        # Find the UM2 or use default audio device
        device = None
        devices = sd.query_devices()
        for i, d in enumerate(devices):
            if "um2" in d["name"].lower() or "uphoria" in d["name"].lower():
                device = i
                print(f"Using audio device: {d['name']}")
                break
        if device is None:
            print("UM2 not found — using default output device")

        # Start audio stream
        stream = sd.OutputStream(
            samplerate=44100,
            channels=2,
            callback=self._audio_callback,
            blocksize=1024,
            device=device,
            dtype="float32",
        )

        # Start hardware thread
        hw_thread = threading.Thread(target=self._hardware_loop, daemon=True)

        try:
            with stream:
                hw_thread.start()
                print("Stem mixer running. Press Ctrl+C to exit.")
                self._display_loop()  # Runs on main thread
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.running = False


if __name__ == "__main__":
    app = StemMixerApp()
    app.run()
```

**Step 2: Commit**

```bash
git add -f pi/player/main.py
git commit -m "feat(pi): add main stem mixer application"
```

---

## Task 8: Laravel PushStemsToDevice Job

Adds the auto-push from WavDash to the Pi after all stems are converted.

**Files:**
- Create: `app/app/Jobs/PushStemsToDevice.php`
- Modify: `app/app/Jobs/ConvertAndPublishAudio.php` — add dispatch after all stems converted
- Modify: `app/.env.example` — add `STEM_DEVICE_URL`
- Create: `app/tests/Feature/Jobs/PushStemsToDeviceTest.php`

**Step 1: Write the failing test**

```php
// app/tests/Feature/Jobs/PushStemsToDeviceTest.php
<?php

namespace Tests\Feature\Jobs;

use App\Jobs\PushStemsToDevice;
use App\Models\Upload;
use App\Models\UploadStem;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Illuminate\Support\Facades\Http;
use Tests\TestCase;

class PushStemsToDeviceTest extends TestCase
{
    use RefreshDatabase;

    public function test_push_stems_sends_metadata_and_files(): void
    {
        config(['services.stem_device.url' => 'http://100.0.0.1:9000']);

        $user = User::factory()->create();
        $upload = Upload::factory()->for($user)->create([
            'title' => 'Test Song',
            'duration_seconds' => 180,
        ]);

        // Create stems
        foreach (['vocals', 'drums', 'bass', 'guitar', 'piano', 'other'] as $type) {
            UploadStem::factory()->create([
                'upload_id' => $upload->id,
                'stem_type' => $type,
                'public_path' => "uploads/stream/{$user->id}/stems/{$upload->id}/{$type}.ogg",
                'converted_to_ogg' => true,
            ]);
        }

        Http::fake([
            '100.0.0.1:9000/api/songs' => Http::response(['song_id' => 'abc123', 'title' => 'Test Song'], 201),
            '100.0.0.1:9000/api/songs/abc123/stems' => Http::response(['stem_type' => 'vocals', 'message' => 'ok'], 201),
        ]);

        PushStemsToDevice::dispatch($upload);

        // Verify metadata POST was sent
        Http::assertSent(function ($request) {
            return str_contains($request->url(), '/api/songs')
                && $request['title'] === 'Test Song';
        });
    }

    public function test_push_stems_skipped_when_no_device_url(): void
    {
        config(['services.stem_device.url' => null]);

        $user = User::factory()->create();
        $upload = Upload::factory()->for($user)->create();

        Http::fake();

        PushStemsToDevice::dispatch($upload);

        Http::assertNothingSent();
    }
}
```

**Step 2: Run test to verify it fails**

Run: `cd app && php artisan test --filter=PushStemsToDeviceTest`
Expected: FAIL (class not found)

**Step 3: Write the PushStemsToDevice job**

```php
// app/app/Jobs/PushStemsToDevice.php
<?php

namespace App\Jobs;

use App\Models\Upload;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Facades\Storage;

class PushStemsToDevice implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public int $tries = 3;
    public int $timeout = 120;

    public function __construct(
        public Upload $upload,
    ) {}

    public function handle(): void
    {
        $deviceUrl = config('services.stem_device.url');
        if (empty($deviceUrl)) {
            return;
        }

        $upload = $this->upload->load(['stems', 'analysis']);
        $bpm = $upload->analysis?->bpm;

        // Step 1: Create song on device
        $response = Http::timeout(30)->post("{$deviceUrl}/api/songs", [
            'title' => $upload->title ?? $upload->original_filename ?? 'Untitled',
            'artist' => $upload->artist ?? null,
            'bpm' => $bpm,
            'duration' => $upload->duration_seconds,
        ]);

        if (!$response->successful()) {
            Log::error('PushStemsToDevice: Failed to create song on device', [
                'upload_id' => $upload->id,
                'status' => $response->status(),
                'body' => $response->body(),
            ]);
            $this->fail(new \RuntimeException("Device returned {$response->status()}"));
            return;
        }

        $songId = $response->json('song_id');

        // Step 2: Upload each stem file
        foreach ($upload->stems as $stem) {
            if (!$stem->converted_to_ogg || empty($stem->public_path)) {
                continue;
            }

            try {
                $filePath = $stem->public_path;

                // Get file contents from storage
                if ($upload->usesR2Storage()) {
                    $fileContents = Storage::disk('r2')->get($filePath);
                } else {
                    $fileContents = Storage::disk('public')->get($filePath);
                }

                if ($fileContents === null) {
                    Log::warning("PushStemsToDevice: Stem file not found", [
                        'stem_type' => $stem->stem_type,
                        'path' => $filePath,
                    ]);
                    continue;
                }

                $stemResponse = Http::timeout(60)
                    ->attach('file', $fileContents, "{$stem->stem_type}.ogg")
                    ->post("{$deviceUrl}/api/songs/{$songId}/stems", [
                        'stem_type' => $stem->stem_type,
                    ]);

                if (!$stemResponse->successful()) {
                    Log::warning("PushStemsToDevice: Failed to push stem", [
                        'stem_type' => $stem->stem_type,
                        'status' => $stemResponse->status(),
                    ]);
                }
            } catch (\Exception $e) {
                Log::warning("PushStemsToDevice: Exception pushing stem", [
                    'stem_type' => $stem->stem_type,
                    'error' => $e->getMessage(),
                ]);
            }
        }

        Log::info("PushStemsToDevice: Successfully pushed stems to device", [
            'upload_id' => $upload->id,
            'device_song_id' => $songId,
        ]);
    }
}
```

**Step 4: Add config and env variable**

Add to `app/config/services.php` (inside the return array):

```php
'stem_device' => [
    'url' => env('STEM_DEVICE_URL'),
],
```

Add to `app/.env.example`:

```
# Stem Device (Pi) - set to push stems to a device over the network
# STEM_DEVICE_URL=http://100.x.x.x:9000
```

**Step 5: Add dispatch trigger in ConvertAndPublishAudio**

At the end of the `handle()` method in `app/app/Jobs/ConvertAndPublishAudio.php`, after the existing `updateUploadRecord()` call, add:

```php
// Check if all stems for this upload are now converted — if so, push to device
if ($this->fileType === 'stem') {
    $upload = $this->upload->fresh();
    $totalStems = $upload->stems()->count();
    $convertedStems = $upload->stems()->where('converted_to_ogg', true)->count();

    if ($totalStems > 0 && $totalStems === $convertedStems) {
        PushStemsToDevice::dispatch($upload);
    }
}
```

Add the import at the top of ConvertAndPublishAudio.php:

```php
use App\Jobs\PushStemsToDevice;
```

**Step 6: Run tests to verify they pass**

Run: `cd app && php artisan test --filter=PushStemsToDeviceTest`
Expected: PASS

**Step 7: Commit**

```bash
cd app
git add app/Jobs/PushStemsToDevice.php \
       tests/Feature/Jobs/PushStemsToDeviceTest.php \
       config/services.php \
       .env.example
git add app/Jobs/ConvertAndPublishAudio.php
git commit -m "feat(app): add PushStemsToDevice job to auto-push stems to Pi"
```

---

## Task 9: Pi Systemd Services

Create systemd unit files so both Pi services start on boot.

**Files:**
- Create: `pi/deploy/wavdash-receiver.service`
- Create: `pi/deploy/wavdash-player.service`
- Create: `pi/deploy/setup.sh`

**Step 1: Write the systemd unit files**

```ini
# pi/deploy/wavdash-receiver.service
[Unit]
Description=WavDash Stem Receiver
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/wavdash-monorepo/pi/receiver
Environment=WAVDASH_STEMS_DIR=/home/pi/wavdash-stems
ExecStart=/home/pi/wavdash-monorepo/pi/receiver/venv/bin/uvicorn main:app --host 0.0.0.0 --port 9000
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```ini
# pi/deploy/wavdash-player.service
[Unit]
Description=WavDash Stem Mixer Player
After=network-online.target wavdash-receiver.service
Wants=network-online.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/wavdash-monorepo/pi/player
Environment=WAVDASH_STEMS_DIR=/home/pi/wavdash-stems
ExecStart=/home/pi/wavdash-monorepo/pi/player/venv/bin/python main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

**Step 2: Write the setup script**

```bash
#!/usr/bin/env bash
# pi/deploy/setup.sh
# Run this on the Raspberry Pi to set up both services.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
STEMS_DIR="$HOME/wavdash-stems"

echo "=== WavDash Stem Mixer Setup ==="

# Create stems directory
mkdir -p "$STEMS_DIR/songs"
echo "Created $STEMS_DIR"

# Set up receiver venv
echo "Setting up receiver..."
cd "$REPO_DIR/receiver"
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# Set up player venv
echo "Setting up player..."
cd "$REPO_DIR/player"
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# Install systemd services
echo "Installing systemd services..."
sudo cp "$REPO_DIR/deploy/wavdash-receiver.service" /etc/systemd/system/
sudo cp "$REPO_DIR/deploy/wavdash-player.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable wavdash-receiver wavdash-player
sudo systemctl start wavdash-receiver
sudo systemctl start wavdash-player

echo ""
echo "=== Setup complete ==="
echo "Receiver: http://$(hostname -I | awk '{print $1}'):9000"
echo "Stems dir: $STEMS_DIR"
echo ""
echo "Check status:"
echo "  sudo systemctl status wavdash-receiver"
echo "  sudo systemctl status wavdash-player"
```

**Step 3: Commit**

```bash
git add -f pi/deploy/
chmod +x pi/deploy/setup.sh
git commit -m "chore(pi): add systemd services and setup script"
```

---

## Task 10: End-to-End Integration Test

Verify the full flow works: WavDash -> Pi receiver -> song appears in library.

**Files:**
- Create: `pi/test_integration.py`

**Step 1: Write the integration test**

```python
# pi/test_integration.py
"""
End-to-end integration test.
Starts the receiver, pushes a fake song, verifies it appears in the song library.

Run: cd pi && python test_integration.py
Requires: receiver and player packages installed.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time

import httpx


def main():
    stems_dir = tempfile.mkdtemp(prefix="wavdash-test-")
    os.environ["WAVDASH_STEMS_DIR"] = stems_dir
    print(f"Using temp stems dir: {stems_dir}")

    # Start receiver in background
    receiver = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", "9099"],
        cwd=os.path.join(os.path.dirname(__file__), "receiver"),
        env={**os.environ},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    try:
        # Wait for receiver to start
        base_url = "http://127.0.0.1:9099"
        for _ in range(20):
            try:
                httpx.get(f"{base_url}/api/songs", timeout=1)
                break
            except httpx.ConnectError:
                time.sleep(0.5)
        else:
            print("FAIL: Receiver did not start")
            return 1

        print("Receiver started")

        # Create a song
        resp = httpx.post(f"{base_url}/api/songs", json={
            "title": "Integration Test Song",
            "artist": "Test",
            "bpm": 128.0,
            "duration": 200.0,
        })
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}"
        song_id = resp.json()["song_id"]
        print(f"Created song: {song_id}")

        # Upload 6 stems
        for stem_type in ["vocals", "drums", "bass", "guitar", "piano", "other"]:
            resp = httpx.post(
                f"{base_url}/api/songs/{song_id}/stems",
                data={"stem_type": stem_type},
                files={"file": (f"{stem_type}.ogg", b"fake-ogg-data", "audio/ogg")},
            )
            assert resp.status_code == 201, f"Stem upload failed: {resp.status_code}"
        print("Uploaded 6 stems")

        # Verify song listing
        resp = httpx.get(f"{base_url}/api/songs")
        songs = resp.json()
        assert len(songs) == 1
        assert songs[0]["title"] == "Integration Test Song"
        print("Song appears in listing")

        # Verify files on disk
        song_dir = os.path.join(stems_dir, "songs", song_id)
        assert os.path.exists(os.path.join(song_dir, "vocals.ogg"))
        assert os.path.exists(os.path.join(song_dir, "meta.json"))
        with open(os.path.join(song_dir, "meta.json")) as f:
            meta = json.load(f)
        assert len(meta["stems"]) == 6
        print("Files verified on disk")

        # Verify song library scanner picks it up
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "player"))
        from song_library import SongLibrary
        lib = SongLibrary(stems_dir)
        scanned = lib.scan()
        assert len(scanned) == 1
        assert scanned[0].title == "Integration Test Song"
        assert len(scanned[0].stem_paths) == 6
        print("Song library scanner works")

        # Delete song
        resp = httpx.delete(f"{base_url}/api/songs/{song_id}")
        assert resp.status_code == 200
        assert not os.path.exists(song_dir)
        print("Song deleted successfully")

        print("\n=== ALL INTEGRATION TESTS PASSED ===")
        return 0

    finally:
        receiver.terminate()
        receiver.wait()
        shutil.rmtree(stems_dir, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
```

**Step 2: Run the integration test**

Run: `cd pi && python test_integration.py`
Expected: "ALL INTEGRATION TESTS PASSED"

**Step 3: Commit**

```bash
git add -f pi/test_integration.py
git commit -m "test(pi): add end-to-end integration test for receiver + library"
```

---

## Summary

| Task | Status | Component | Tests |
|------|--------|-----------|-------|
| 1 | ✅ DONE | Hardware Assembly & Validation | Manual (all controls verified) |
| 2 | | Pi Receiver Service | 7 pytest tests |
| 3 | | Audio Engine | 9 pytest tests |
| 4 | | Hardware I/O | 3 pytest tests (ButtonHandler) |
| 5 | | Song Library | 4 pytest tests |
| 6 | | TFT Display | Manual (requires Pi hardware) |
| 7 | | Main Application | Manual (requires Pi hardware) |
| 8 | | Laravel PushStemsToDevice | 2 PHPUnit tests |
| 9 | | Systemd Services | Manual (deploy to Pi) |
| 10 | | Integration Test | 1 end-to-end script |

**Key change from original plan:** The custom PCB uses a single Adafruit seesaw (ATTiny8x7) at I2C `0x49` instead of two KB2040 boards. This eliminates the need for separate CircuitPython firmware — the seesaw is controlled directly from the Pi using `adafruit-circuitpython-seesaw`. The KB2040 firmware task has been removed.

**Recommended execution order:** Tasks 2–5 can be done without Pi hardware (pure Python, testable anywhere). Tasks 6–7 need the Pi with display/hardware attached. Task 8 is Laravel-side (MacBook). Task 9 deploys to Pi. Task 10 validates the full chain.
