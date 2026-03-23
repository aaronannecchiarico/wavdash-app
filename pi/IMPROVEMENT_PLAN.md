# WavDash Raspberry Pi Stem Mixer — Improvement Plan

## Priority 1: Reliability and Correctness (Critical)

### 1.1 Non-Atomic Writes in the Receiver
**Files**: `pi/receiver/main.py`, `pi/player/song_library.py`

- Replace all `json.dump` calls with write-to-temp-then-`os.replace` pattern
- Add `"status": "pending"` field to `meta.json` on song creation
- Auto-promote status to `"ready"` when all expected stems are received
- Add `expected_stems` field to `CreateSongRequest` (default 6)
- In `song_library.py`: wrap `json.load` in `try/except json.JSONDecodeError`; skip songs where `meta.get("status") != "ready"`

### 1.2 No Graceful Shutdown Handling
**Files**: `pi/player/main.py`, `pi/deploy/wavdash-player.service`, `pi/deploy/wavdash-receiver.service`

- Install `signal.signal(signal.SIGTERM, ...)` handler in player that sets `self.running = False`
- Add `TimeoutStopSec=10` to both systemd unit files

### 1.3 No Delivery Confirmation from Pi to Laravel
**Files**: `pi/receiver/main.py`, `app/app/Jobs/PushStemsToDevice.php`, new migration + controller

- Add `upload_id: Optional[str]` to `CreateSongRequest`, store in `meta.json`
- On status → "ready", emit fire-and-forget POST to `WAVDASH_CALLBACK_URL`
- `PushStemsToDevice`: pass `upload_id`, store returned `pi_song_id` on Upload model
- New migration: `pi_song_id` (varchar, nullable) + `pi_delivered_at` (timestamp, nullable) on `uploads`
- New `PiCallbackController` for `POST /api/pi/song-received`

### 1.4 Remove Redundant songs.json Index
**Files**: `pi/receiver/main.py`

- Delete `get_songs_index_path()`, `load_songs_index()`, `save_songs_index()`
- Rewrite `list_songs()` to scan `songs/` directory and build response from `meta.json` files
- Rewrite `delete_song()` to only `shutil.rmtree`; remove index update calls

---

## Priority 2: Operability (High)

### 2.1 Hardcoded Username in Deploy Infrastructure
**Files**: `pi/deploy/setup.sh`, `pi/deploy/wavdash-player.service`, `pi/deploy/wavdash-receiver.service`, `Makefile`

- `setup.sh`: detect `CURRENT_USER=$(whoami)`, `sed` substitute into unit files before `sudo cp`
- Add template comment to unit files: `# Template — setup.sh substitutes the username`
- `Makefile`: change default `PI_HOST` from `aannecchiarico@raspberrypi.local` → `pi@raspberrypi.local`

### 2.2 No Health Endpoint on the Receiver
**Files**: `pi/receiver/main.py`, `app/app/Jobs/PushStemsToDevice.php`

- Add module-level `_start_time = time.monotonic()`
- Add `GET /health` returning `{status, songs_count, disk_free_gb, uptime_s}`
- `PushStemsToDevice`: add 5s pre-flight health check; call `$this->fail()` on non-200 without attempting upload

### 2.3 No Storage Management or Disk Full Protection
**Files**: `pi/receiver/main.py`, `app/app/Jobs/PushStemsToDevice.php`

- In `upload_stem()`: check `shutil.disk_usage` against `WAVDASH_MIN_FREE_MB` (default 500); return HTTP 507 if insufficient
- `PushStemsToDevice`: treat 507 as non-retryable job failure with clear log message

### 2.4 Setup Script Not Idempotent
**Files**: `pi/deploy/setup.sh`, `Makefile`

- `pip install --upgrade -r requirements.txt`
- `systemctl enable --now` instead of separate enable + start
- Add post-start health poll loop (curl `/health` up to 30s)
- Add `--restart` flag for re-deploys
- Add `pi-deploy` Makefile target = `pi-sync` + SSH `setup.sh --restart`

### 2.5 SongLibrary Does Not Handle Corrupt meta.json
**Files**: `pi/player/song_library.py`, `pi/player/main.py`

- Wrap per-song `json.load` + key access in `try/except (json.JSONDecodeError, KeyError, OSError)`; log and `continue`
- In `main.py` display loop: wrap `library.scan()` in `try/except Exception`; keep old list on error

---

## Priority 3: Feature Completeness (Medium)

### 3.1 Additive (AFL) Solo Mode
**Files**: `pi/player/audio_engine.py`, `pi/player/main.py`, `pi/player/display.py`

- Add `solo_mode: str = "exclusive"` to `MixerState`
- Modify `toggle_solo()` to support both exclusive and additive modes
- Bind mode toggle to encoder press gesture
- Show `SOLO: EXC` / `SOLO: ADD` indicator in `render_now_playing()`

### 3.2 Remote Control API on the Player
**Files**: new `pi/player/api.py`, `pi/player/main.py`, `pi/player/requirements.txt`

- New FastAPI app with read/write endpoints: `/api/status`, `/api/play`, `/api/pause`, `/api/seek`, `/api/fader/{idx}`, `/api/mute/{idx}`, `/api/solo/{idx}`, `/api/load`
- Run as daemon thread via `uvicorn.Server` on port 9001
- Add `threading.RLock` around `load_stems` and status reads of `engine.stems`

### 3.3 Loading Progress Indicator
**Files**: `pi/player/main.py`, `pi/player/display.py`

- Add `self._loading_progress: float = 0.0` to `StemMixerApp`
- Update after each stem file loaded: `_loading_progress = stems_loaded / len(STEM_TYPES)`
- `render_loading()`: accept `progress: float` param; draw proportional fill bar

### 3.4 Audio Engine Position Overflow Fix
**Files**: `pi/player/audio_engine.py`

- In `mix_frames()` end-of-song branch: `self.position = self.num_frames` (clamp, not `start + count`)

---

## Priority 4: Performance and Hardware (Low)

### 4.1 Interrupt-Driven Button Input
**Files**: `pi/player/hardware.py`, `pi/player/main.py`, `pi/player/requirements.txt`

- Configure seesaw INT pin interrupt via `RPi.GPIO`
- Add `wait_for_button_event(timeout)` blocking method to `HardwareController`
- Hardware loop blocks on event rather than sleeping; fader reads remain 30Hz polled
- Fall back to polling if interrupt setup fails

### 4.2 System Metrics and Hardware Health Telemetry
**Files**: `pi/player/main.py`, `pi/receiver/main.py`, `pi/receiver/requirements.txt`

- Track `_audio_underruns` and `_i2c_errors` counters in player
- Expose via remote control API `/api/status` (from 3.2)
- Receiver health endpoint: add `cpu_temp_c`, `cpu_percent`, `mem_free_mb` using `psutil`

### 4.3 Configurable Audio Blocksize
**Files**: `pi/player/main.py`

- Read `WAVDASH_AUDIO_BLOCKSIZE` env var (default `1024`)
- Log chosen blocksize and latency at startup

### 4.4 Fader Value Hysteresis
**Files**: `pi/player/hardware.py`

- Add `_last_fader_raw: list[int] = [0] * 6` to `HardwareController`
- Only emit fader update if `abs(raw - last) > 2` raw counts

---

## Implementation Sequence

| # | Item | Est. |
|---|------|------|
| 1 | 1.1 Atomic writes + song status | 2h |
| 2 | 2.5 SongLibrary exception handling | 30m |
| 3 | 2.1 Hardcoded username | 30m |
| 4 | 1.2 SIGTERM handling | 1h |
| 5 | 2.2 Health endpoint | 1h |
| 6 | 2.3 Disk space management | 1h |
| 7 | 1.4 Remove songs.json index | 1h |
| 8 | 1.3 Delivery confirmation | 3h |
| 9 | 2.4 Idempotent setup.sh | 2h |
| 10 | 3.4 Position clamp fix | 15m |
| 11 | 3.3 Loading progress | 1h |
| 12 | 3.1 AFL solo mode | 2h |
| 13 | 4.4 Fader hysteresis | 1h |
| 14 | 4.2 Metrics/telemetry | 2h |
| 15 | 3.2 Remote control API | 4h |
| 16 | 4.3 Blocksize tuning | 30m |
| 17 | 4.1 Interrupt-driven hardware | 4h |

**Release 1** (items 1–4): Data safety and clean shutdown — interdependent, ship together.
**Release 2** (items 5–9): Operability — health, disk management, idempotent deploy.
**Release 3+** (items 10–17): Features and performance — can be done individually.
