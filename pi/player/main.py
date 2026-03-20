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

# Try hardware imports — fall back to mocks for development
try:
    from hardware import HardwareController, ButtonHandler
    HAS_HARDWARE = True
except (ImportError, RuntimeError):
    HAS_HARDWARE = False

try:
    from display import Display, MockDisplay
    HAS_DISPLAY = True
except (ImportError, RuntimeError):
    from display import MockDisplay
    HAS_DISPLAY = False

STEMS_DIR = Path(os.environ.get("WAVDASH_STEMS_DIR", os.path.expanduser("~/wavdash-stems")))
POLL_HZ = 60
DISPLAY_FPS = 15
LIBRARY_RESCAN_INTERVAL = 5.0  # Seconds between library rescans


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

        # Button handlers for mute/solo
        self.button_handlers: list[ButtonHandler] = []
        if HAS_HARDWARE:
            for i in range(6):
                handler = ButtonHandler(
                    on_short_press=lambda idx=i: self.engine.state.toggle_mute(idx),
                    on_long_press=lambda idx=i: self.engine.state.toggle_solo(idx),
                )
                self.button_handlers.append(handler)

        # Encoder select button — handled in display loop directly
        self.encoder_pressed = False

        # Background loading state
        self._loading = False
        self._loading_song: Song | None = None

    def load_song(self, song: Song):
        """Start loading a song's stems in a background thread."""
        if sf is None:
            print("soundfile not available — cannot load audio")
            return

        self.engine.state.playing = False
        self._loading = True
        self._loading_song = song
        self.screen = "loading"

        thread = threading.Thread(target=self._load_stems_worker, args=(song,), daemon=True)
        thread.start()

    def _load_stems_worker(self, song: Song):
        """Background worker that reads stem files from disk."""
        try:
            stems = {}
            for stem_type in STEM_TYPES:
                if stem_type in song.stem_paths:
                    data, sr = sf.read(str(song.stem_paths[stem_type]), dtype="float32")
                    if data.ndim == 1:
                        data = np.column_stack([data, data])  # Mono → stereo
                    stems[stem_type] = data
                    self.engine.sample_rate = sr

            if stems:
                self.engine.load_stems(stems)
                self.current_song = song
                self.screen = "playing"
                self.engine.state.playing = True
                print(f"Loaded: {song.title}")
            else:
                self.screen = "library"
        except Exception as e:
            print(f"Failed to load {song.title}: {e}", file=sys.stderr)
            self.screen = "library"
        finally:
            self._loading = False
            self._loading_song = None

    def _audio_callback(self, outdata, frames, time_info, status):
        """sounddevice output callback — called from audio thread."""
        if status:
            print(f"Audio: {status}", file=sys.stderr)
        outdata[:] = self.engine.mix_frames(frames)

    def _hardware_loop(self):
        """Hardware I/O polling thread."""
        poll_interval = 1.0 / POLL_HZ
        while self.running:
            now = time.monotonic()

            if self.hw:
                # Read faders
                try:
                    faders = self.hw.read_faders()
                    for i, val in enumerate(faders):
                        self.engine.state.set_fader(i, val)
                except Exception:
                    pass

                # Read buttons
                try:
                    buttons = self.hw.read_buttons()
                    for i, pressed in enumerate(buttons):
                        self.button_handlers[i].update(pressed, now)
                except Exception:
                    pass

                # Update LEDs
                try:
                    self.hw.update_leds(self.engine.state)
                except Exception:
                    pass

                # Encoder is read in the display loop — no accumulation needed

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

            # Read TFT bonnet inputs (or ANO directional buttons if no TFT bonnet)
            btn = self.display.read_buttons()

            # Also check ANO encoder directional buttons for navigation
            if self.hw:
                try:
                    ano_btn = self.hw.read_ano_buttons()
                    # Merge ANO buttons — they supplement the display buttons
                    for key in ["up", "down", "left", "right", "select"]:
                        if ano_btn.get(key):
                            btn[key] = True
                    # Map ANO "select" to display "press"
                    if ano_btn.get("select"):
                        btn["press"] = True
                except Exception:
                    pass

            # Read encoder directly — no accumulation, just current delta
            enc_delta = 0
            enc_pressed = False
            if self.hw:
                try:
                    enc_delta = self.hw.read_encoder_delta()
                except Exception:
                    pass
                try:
                    sel = self.hw.read_encoder_select()
                    if sel and not self.encoder_pressed:
                        enc_pressed = True  # Rising edge only
                    self.encoder_pressed = sel
                except Exception:
                    pass

            if self.screen == "loading":
                if self._loading_song:
                    self.display.render_loading(self._loading_song)
                time.sleep(display_interval)
                continue

            if self.screen == "library":
                # Clamp encoder to ±1 for single-step menu navigation
                enc_nav = max(-1, min(1, enc_delta))

                # Navigation: joystick, ANO up/down, or encoder scroll
                if (btn.get("down") or enc_nav > 0) and self.selected_index < len(self.songs) - 1:
                    self.selected_index += 1
                    if not enc_nav:
                        time.sleep(0.15)  # Debounce for buttons only
                elif (btn.get("up") or enc_nav < 0) and self.selected_index > 0:
                    self.selected_index -= 1
                    if not enc_nav:
                        time.sleep(0.15)
                elif (btn.get("press") or btn.get("b") or enc_pressed) and self.songs:
                    self.load_song(self.songs[self.selected_index])

                self.display.render_library(self.songs, self.selected_index)

            elif self.screen == "playing":
                if btn.get("left") or btn.get("a"):
                    self.engine.state.playing = False
                    self.screen = "library"
                elif btn.get("b") or enc_pressed:
                    self.engine.state.playing = not self.engine.state.playing

                # Encoder scroll = seek (clamp to ±2, 0.5s per detent)
                if enc_delta != 0:
                    clamped = max(-2, min(2, enc_delta))
                    seek_seconds = clamped * 0.5
                    seek_frames = int(seek_seconds * self.engine.sample_rate)
                    new_pos = self.engine.position + seek_frames
                    self.engine.seek(new_pos)

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
