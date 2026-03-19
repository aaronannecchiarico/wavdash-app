# WavDash Pi Stem Mixer

A hardware stem mixer built on Raspberry Pi 5 that receives stems from the WavDash platform and provides real-time mixing with physical faders, buttons, LEDs, and a TFT display.

## How It Works

```
WavDash App (Laravel)          Raspberry Pi 5
┌─────────────────┐            ┌─────────────────────────────┐
│ Upload song      │            │                             │
│ ↓                │            │  Receiver (FastAPI :9000)   │
│ Stem separation  │            │  ↓                          │
│ ↓                │  Tailscale │  ~/wavdash-stems/songs/     │
│ OGG conversion   │───HTTP────→│  ↓                          │
│ ↓                │            │  Player (main.py)           │
│ PushStemsToDevice│            │  ├─ Audio Engine → UM2 out  │
│                  │            │  ├─ Hardware I/O (I2C)      │
│                  │            │  └─ TFT Display (SPI)       │
└─────────────────┘            └─────────────────────────────┘
```

**Automatic flow:** When a user uploads a song and all 6 stems finish converting to OGG, Laravel automatically pushes them to the Pi over Tailscale. No manual trigger needed — gated by the `STEM_DEVICE_URL` env var.

## Hardware

| Component | Address/Interface | Purpose |
|-----------|-------------------|---------|
| Custom PCB (seesaw ATTiny8x7) | I2C `0x49` | 6 faders, 6 buttons, 12 NeoPixels |
| ANO Rotary Encoder (seesaw) | I2C `0x4A` | Master volume + 5 directional buttons |
| Adafruit TFT Bonnet (ST7789) | SPI + GPIO | 240x240 display, joystick, 2 buttons |
| Behringer UM2 | USB Audio | Stereo audio output |

### Controls

- **6 Faders** — Individual stem volume (vocals, drums, bass, guitar, piano, other)
- **6 Buttons** — Short press = mute, long press = solo (exclusive)
- **Rotary Encoder** — Master volume, press = play/pause
- **ANO Directional Buttons** — Navigate song library
- **TFT Joystick** — Navigate library + select songs
- **LEDs** — Green (playing, brightness = fader level), Red (muted), Blue (soloed), Dim white (stopped)

### Display Screens

- **Library** — Song list with title/BPM, joystick/ANO navigation, press to load
- **Now Playing** — 6 stem meters with fader levels, mute/solo state, playback position + progress bar

## Project Structure

```
pi/
├── receiver/              # FastAPI stem receiver service
│   ├── main.py            # POST /api/songs, POST /api/songs/{id}/stems, etc.
│   ├── requirements.txt
│   └── test_receiver.py   # 9 tests
├── player/                # Main mixer application
│   ├── audio_engine.py    # 6-stem mixing with fader/mute/solo/master volume
│   ├── hardware.py        # Seesaw I2C controller (PCB + ANO encoder)
│   ├── song_library.py    # Scans ~/wavdash-stems/ for available songs
│   ├── display.py         # TFT Bonnet ST7789 driver + MockDisplay
│   ├── main.py            # Threaded app: audio callback + hardware poll + display loop
│   ├── requirements.txt
│   ├── test_audio_engine.py   # 13 tests
│   ├── test_hardware.py       # 3 tests
│   └── test_song_library.py   # 4 tests
├── deploy/                # Deployment scripts
│   ├── wavdash-receiver.service   # systemd unit
│   ├── wavdash-player.service     # systemd unit
│   └── setup.sh                   # One-shot Pi setup
├── examples/              # Validated hardware test scripts
│   ├── main.py            # Full hardware test (PCB + ANO + audio)
│   ├── rotary_encoder_example.py
│   └── bonnet_example.py
└── test_integration.py    # End-to-end: receiver → disk → song library
```

## Services

### Receiver (`wavdash-receiver.service`)

FastAPI on port 9000. Accepts stems from WavDash.

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/songs` | POST | Create a song (title, artist, bpm, duration) |
| `/api/songs` | GET | List all songs |
| `/api/songs/{id}/stems` | POST | Upload an OGG stem file |
| `/api/songs/{id}` | DELETE | Delete song + files |

Songs are stored as:
```
~/wavdash-stems/songs/{song_id}/
├── meta.json          # title, artist, bpm, duration, stems list
├── vocals.ogg
├── drums.ogg
├── bass.ogg
├── guitar.ogg
├── piano.ogg
└── other.ogg
```

### Player (`wavdash-player.service`)

Threaded Python application with three loops:
- **Audio callback** (sounddevice) — Mixes stems in real-time at 44.1kHz
- **Hardware poll** (60Hz) — Reads faders/buttons/encoder, updates LEDs
- **Display loop** (15fps) — Renders TFT, reads joystick, rescans library every 5s

## Dev Workflow

All Pi code lives in `pi/` locally. Use Makefile targets to sync and test:

```bash
make pi-sync       # rsync pi/ → Pi's ~/wavdash/
make pi-test       # Sync + run pytest on Pi
make pi-run        # Sync + run player interactively
make pi-receiver   # Sync + start receiver interactively
make pi-ssh        # SSH to Pi
```

## Setup

### Prerequisites

- Raspberry Pi 5 with Raspberry Pi OS
- Tailscale installed and authenticated
- Python 3.11+ with venv at `~/env/`
- I2C and SPI enabled (`sudo raspi-config` → Interface Options)
- System packages: `libportaudio2 portaudio19-dev libsndfile1`

### Install

```bash
# From your dev machine
make pi-sync

# On the Pi
bash ~/wavdash/deploy/setup.sh
```

This installs Python deps into `~/env/`, copies systemd units, enables and starts both services.

### Configure WavDash to Push Stems

Add to `app/.env`:
```
STEM_DEVICE_URL=http://<pi-tailscale-ip>:9000
```

Find the Pi's Tailscale IP: `ssh raspberrypi.local "tailscale ip -4"`

### Manual Testing

```bash
# Check services
sudo systemctl status wavdash-receiver
sudo systemctl status wavdash-player

# View receiver logs
journalctl -u wavdash-receiver -f

# Test receiver API
curl http://localhost:9000/api/songs

# Run player interactively (stop service first)
sudo systemctl stop wavdash-player
cd ~/wavdash/player && source ~/env/bin/activate && python main.py
```

## Tests

29 tests total, all passing on Pi (Python 3.13) and macOS (Python 3.11):

| Suite | Tests | Coverage |
|-------|-------|----------|
| `receiver/test_receiver.py` | 9 | CRUD + stem upload + validation |
| `player/test_audio_engine.py` | 13 | Mixing, mute, solo, fader, master vol, playback |
| `player/test_hardware.py` | 3 | Button handler short/long press detection |
| `player/test_song_library.py` | 4 | Scan, stem paths, empty dir, rescan |
| `test_integration.py` | 1 | Full receiver → disk → library pipeline |

Run locally: `cd pi/player && pytest -v`
Run on Pi: `make pi-test`

## Laravel Integration

**Job:** `app/app/Jobs/PushStemsToDevice.php`
- Dispatched automatically when all stems for an upload finish OGG conversion
- Creates song on Pi receiver, then uploads each stem file
- 3 retries, 120s timeout
- Gated by `services.stem_device.url` config (empty = disabled)

**Trigger:** End of `ConvertAndPublishAudio::handle()` — checks if all stems are `converted_to_ogg`, dispatches if complete.

**Config:** `app/config/services.php` → `stem_device.url`
**Env:** `STEM_DEVICE_URL` in `app/.env`
