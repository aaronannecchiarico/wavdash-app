# Pi Stem Mixer — Design Document

**Date:** 2026-03-17
**Updated:** 2026-03-18
**Status:** Approved — Hardware Complete

## Overview

Host WavDash on a MacBook for demo/local use. After stem separation, automatically push OGG Opus stem files to a Raspberry Pi 5 over Tailscale. The Pi runs a hardware stem mixer with 6 faders, buttons, rotary encoder, and TFT display, outputting mixed stereo audio through a Behringer UM2 USB interface.

## Hardware

### Components

- **Raspberry Pi 5** (4GB) with active cooling
- **Custom PCB** with 6 linear faders (S1–S6), 6 tactile buttons, 12 RGB LEDs (WS2812, 2 per fader), onboard **Adafruit seesaw (ATTiny8x7)** for I2C control
- **Adafruit ANO Rotary Encoder** (I2C seesaw at `0x4A` — master volume + 5 navigation buttons)
- **Adafruit Mini PiTFT Bonnet** (ST7789 240x240 TFT + 5-way joystick + 2 buttons — song browsing/UI)
- **OzzMaker QWIIC HAT** + QWIIC/Stemma QT cables (I2C daisy-chain)
- **Behringer UPhoria UM2** (USB audio interface — stereo output)

### I2C Bus Wiring

All I2C devices daisy-chained via QWIIC/Stemma QT cables:

```
Pi 5 GPIO (I2C1: SDA=GPIO2, SCL=GPIO3)
  │
  └─ OzzMaker QWIIC HAT (solders to Pi GPIO, exposes QWIIC ports)
       │
       ├─── QWIIC cable ──→ Custom PCB seesaw (0x49 default)
       │                     6 faders + 6 buttons + 12 NeoPixels
       │
       └─── QWIIC cable ──→ Adafruit ANO Rotary Encoder (0x4A)
                             rotary position + select/up/left/down/right buttons
```

### TFT Bonnet

- Sits directly on Pi 5 GPIO header (on top of QWIIC HAT pass-through)
- Uses SPI for display (ST7789, 240x240, `board.CE0`/`board.D25`/`board.D24`)
- GPIO for joystick and buttons (does not conflict with I2C pins)

### Custom PCB — Seesaw Pin Map

The PCB has a single Adafruit seesaw (ATTiny8x7) at I2C address `0x49` (default). All faders, buttons, and LEDs are connected to seesaw pins:

| Seesaw Pin | Connected To | Code Reference |
|------------|-------------|----------------|
| 0 | Fader S1 wiper (analog) | `slider_0` — Vocals |
| 1 | Fader S2 wiper (analog) | `slider_1` — Drums |
| 2 | Fader S3 wiper (analog) | `slider_2` — Bass |
| 3 | Fader S4 wiper (analog) | `slider_3` — Guitar |
| 6 | Fader S5 wiper (analog) | `slider_4` — Piano |
| 7 | Fader S6 wiper (analog) | `slider_5` — Other |
| 19 | Button S1 (digital, pull-up, active low) | `btn_0` — Vocals |
| 18 | Button S2 (digital, pull-up, active low) | `btn_1` — Drums |
| 14 | Button S3 (digital, pull-up, active low) | `btn_2` — Bass |
| 13 | Button S4 (digital, pull-up, active low) | `btn_3` — Guitar |
| 12 | Button S5 (digital, pull-up, active low) | `btn_4` — Piano |
| 9 | Button S6 (digital, pull-up, active low) | `btn_5` — Other |
| 20 | NeoPixel data out (12 LEDs daisy-chained) | `pixels` |

### ANO Rotary Encoder — Seesaw Pin Map

The ANO rotary encoder is a separate seesaw device at I2C address `0x4A`:

| Seesaw Pin | Connected To | Code Reference |
|------------|-------------|----------------|
| encoder | Rotary position (quadrature) | `encoder.position` — Master volume |
| 1 | Select/center button (pull-up, active low) | `select` — Play/pause |
| 2 | Up button (pull-up, active low) | `up` |
| 3 | Left button (pull-up, active low) | `left` |
| 4 | Down button (pull-up, active low) | `down` |
| 5 | Right button (pull-up, active low) | `right` |

### TFT Bonnet — GPIO Pin Map

| GPIO Pin | Board Ref | Connected To | Code Reference |
|----------|-----------|-------------|----------------|
| GPIO 5 | `board.D5` | Button A | `button_A` |
| GPIO 6 | `board.D6` | Button B | `button_B` |
| GPIO 27 | `board.D27` | Joystick Left | `button_L` |
| GPIO 23 | `board.D23` | Joystick Right | `button_R` |
| GPIO 17 | `board.D17` | Joystick Up | `button_U` |
| GPIO 22 | `board.D22` | Joystick Down | `button_D` |
| GPIO 4 | `board.D4` | Joystick Center/Press | `button_C` |
| GPIO 26 | `board.D26` | Backlight control | `backlight` |
| CE0 | `board.CE0` | SPI chip select | Display CS |
| GPIO 25 | `board.D25` | Data/command | Display DC |
| GPIO 24 | `board.D24` | Reset | Display RST |
| SPI0 | `board.SPI()` | SPI bus (MOSI/SCLK) | Display data |

### Power

- Pi 5: USB-C (5V/5A recommended)
- Custom PCB seesaw: 3.3V via QWIIC from Pi
- ANO Encoder seesaw: 3.3V via QWIIC from Pi
- Faders: wiper between 3.3V and GND
- UM2: separate USB connection to Pi

### Audio Output

```
Pi 5 USB ──→ Behringer UM2 ──→ 1/4" or XLR out to speaker/PA
```

## Part A: MacBook Hosting & Auto-Push

### Hosting

Run WavDash via `make dev-detached` on MacBook. Accessible at `http://<macbook-tailscale-ip>:8000` from any Tailscale device. No nginx, no SSL — local demo only.

### Auto-Push Flow

1. User uploads song via WavDash web UI
2. Demucs `htdemucs_6s` separates into 6 stems (vocals, drums, bass, guitar, piano, other)
3. `ConvertAndPublishAudio` job converts WAV → OGG Opus (existing pipeline)
4. **New:** `PushStemsToDevice` job fires after conversion completes
5. Job POSTs song metadata + 6 OGG files to `http://<pi-tailscale-ip>:9000/api/songs/{song_id}/stems`
6. Pi receiver confirms receipt
7. WavDash UI shows "Synced to device"

### Configuration

New `.env` variable:

```bash
STEM_DEVICE_URL=http://100.x.x.x:9000  # Pi's Tailscale IP. Unset = push disabled.
```

### What Gets Pushed

- 6 OGG Opus stem files (already generated by existing pipeline)
- Song metadata: title, artist, BPM, duration, stem mapping

## Part B: Pi Software

### B1: HTTP Receiver Service

Lightweight FastAPI service on Pi at port 9000.

**Endpoints:**

- `POST /api/songs` — Receive song metadata, create entry, return `song_id`
- `POST /api/songs/{song_id}/stems` — Receive stem file (multipart) with `stem_type` field
- `GET /api/songs` — List all stored songs
- `DELETE /api/songs/{song_id}` — Remove song and stems

**Storage:**

```
~/wavdash-stems/
├── songs.json          # JSON index of all songs
└── songs/
    └── {song_id}/
        ├── meta.json   # title, artist, BPM, duration, stem list
        ├── vocals.ogg
        ├── drums.ogg
        ├── bass.ogg
        ├── guitar.ogg
        ├── piano.ogg
        └── other.ogg
```

No database — filesystem + JSON index. Runs as a systemd unit (starts on boot).

### B2: Stem Player Application

Python application handling hardware I/O, audio mixing, and TFT UI.

**Architecture — single process, three threads:**

1. **Audio thread** — `sounddevice` OutputStream callback. Pre-loads all 6 stems into memory as numpy arrays. Mixes 6 channels applying fader volumes and mute/solo states, outputs stereo to UM2. Target latency: ~20ms.

2. **Hardware I/O thread** — Polls I2C bus at ~60Hz:
   - PCB seesaw (`0x49`): reads 6 analog faders via `AnalogInput`, reads 6 buttons via `DigitalIO`, writes 12 NeoPixels via `NeoPixel`
   - ANO encoder seesaw (`0x4A`): reads rotary position via `IncrementalEncoder`, reads 5 navigation buttons via `DigitalIO`
   - Button state reading with short-press/long-press detection (mute/solo)

3. **Main thread** — Drives TFT bonnet UI:
   - Song browser screen
   - Now-playing screen
   - Joystick + bonnet button input (GPIO direct read)

**Shared state (protected by lock):**

- `fader_values[6]` — float array (0.0–1.0)
- `mute_states[6]` — boolean array
- `solo_states[6]` — boolean array
- `master_volume` — float (0.0–1.0)
- `playback_state` — playing / paused / stopped
- `current_song` — which song is loaded

**Song loading:** When user selects a song, all 6 OGG stems are decoded into memory as numpy arrays. Pi 5 with 4GB can hold ~15 minutes of 6-channel audio comfortably.

**Audio mixing (callback):**

```python
for each frame:
    mix = sum(stem[i] * fader[i] * (not muted[i]) for i in 6)
    if any_soloed:
        mix = sum(stem[i] * fader[i] for soloed stems only)
    output = mix * master_volume
```

### Controls

| Control | Hardware | Action |
|---------|----------|--------|
| Faders 1–6 | PCB seesaw pins 0,1,2,3,6,7 | Individual stem volume (vocals, drums, bass, guitar, piano, other) |
| Buttons 1–6 (short press) | PCB seesaw pins 19,18,14,13,12,9 | Toggle mute on that stem |
| Buttons 1–6 (long press) | PCB seesaw pins 19,18,14,13,12,9 | Solo that stem |
| Rotary encoder turn | ANO seesaw `0x4A` encoder | Master volume |
| Rotary encoder select | ANO seesaw `0x4A` pin 1 | Play / pause |
| ANO up/down | ANO seesaw `0x4A` pins 2,4 | Alternative: scroll song library |
| Joystick up/down | Bonnet GPIO D17/D22 | Scroll song library |
| Joystick press | Bonnet GPIO D4 | Load & play selected song |
| Joystick left | Bonnet GPIO D27 | Back to library from now-playing |
| Bonnet Button A | GPIO D5 | Stop (return to library) |
| Bonnet Button B | GPIO D6 | Reserved |

### LED Behavior

| State | LED Color | Behavior |
|-------|-----------|----------|
| Active (playing) | Green | Solid, brightness follows fader position |
| Muted | Red | Solid |
| Soloed | Blue | Solid |
| Stopped / No song | Dim white | Solid |

Both LEDs per fader (2 of 12 total on seesaw pin 20) show the same color.

**LED-to-Fader Mapping** (12 NeoPixels on single chain, pin 20):

| Pixel Index | Position | Fader |
|-------------|----------|-------|
| 0, 1 | Top row left pair | S1 (Vocals) |
| 2, 3 | Top row center-left pair | S2 (Drums) |
| 4, 5 | Top row center-right pair | S3 (Bass) |
| 6, 7 | Bottom row left pair | S4 (Guitar) |
| 8, 9 | Bottom row center pair | S5 (Piano) |
| 10, 11 | Bottom row right pair | S6 (Other) |

> **Note:** The exact pixel-to-fader mapping may need adjustment based on how the NeoPixels are physically wired on the PCB. Update this table after verifying on hardware.

### TFT Screens

**Song Library:**

```
┌──────────────────────┐
│  WavDash Stems       │
│──────────────────────│
│  > Song Title A      │
│    Song Title B      │
│    Song Title C      │
│    Song Title D      │
│──────────────────────│
│  4 songs  up/dn      │
└──────────────────────┘
```

**Now Playing:**

```
┌──────────────────────┐
│  > Song Title A      │
│  120 BPM             │
│──────────────────────│
│  VOC ████████░░ 80%  │
│  DRM ██████░░░░ 60%  │
│  BAS █████░░░░░ 50%  │
│  GTR ████████░░ 80%  │
│  PNO ░░░░░░░░░░ MUTE │
│  OTH ██████████ 100% │
│──────────────────────│
│  01:23 / 03:45       │
└──────────────────────┘
```

## Codebase Location

| Component | Location |
|-----------|----------|
| PushStemsToDevice job | `app/app/Jobs/PushStemsToDevice.php` |
| Device config | `app/.env` → `STEM_DEVICE_URL` |
| Pi receiver service | `pi/receiver/` |
| Pi player app | `pi/player/` |
| Pi systemd units | `pi/deploy/` |
| Hardware test scripts | `pi/main.py`, `pi/rotary_encoder_example.py`, `pi/bonnet_example.py` |

## Hardware-to-Code Reference

### I2C Device Summary

| Device | I2C Address | Library | Purpose |
|--------|-------------|---------|---------|
| Custom PCB seesaw | `0x49` (default) | `adafruit_seesaw.seesaw.Seesaw(i2c)` | Faders, buttons, LEDs |
| ANO Rotary Encoder | `0x4A` | `adafruit_seesaw.seesaw.Seesaw(i2c, addr=0x4A)` | Rotary + nav buttons |

### Python Libraries Required

| Library | Used For |
|---------|----------|
| `adafruit-blinka` | Board/GPIO/I2C/SPI abstraction |
| `adafruit-circuitpython-seesaw` | PCB + ANO encoder I2C comms (`AnalogInput`, `DigitalIO`, `NeoPixel`, `IncrementalEncoder`) |
| `adafruit-circuitpython-rgb-display` | ST7789 TFT bonnet display |
| `Pillow` | Image rendering for TFT |
| `sounddevice` | Audio output stream to UM2 |
| `soundfile` | OGG file decoding |
| `numpy` | Audio buffer manipulation |

## End-to-End Flow

```
MacBook (WavDash)                          Pi 5
─────────────────                          ────

1. User uploads song.mp3
   via web UI at :8000

2. Demucs htdemucs_6s
   separates 6 stems

3. ConvertAndPublishAudio
   converts WAV → OGG Opus

4. PushStemsToDevice job
   POSTs metadata + 6 OGGs ──────────→  5. FastAPI receiver
   to Pi Tailscale IP:9000               saves to ~/wavdash-stems/
                                          updates songs.json

6. WavDash UI shows                    7. Song appears in
   "Synced to device" ←────────────       TFT song library

                                       8. User selects song
                                          via joystick on TFT

                                       9. 6 OGGs decoded into
                                          memory as numpy arrays

                                      10. Audio callback mixes
                                          stems with fader values
                                          → stereo out via UM2

                                      11. Faders, buttons, rotary
                                          control mix in real-time
                                          LEDs + TFT update live
```
