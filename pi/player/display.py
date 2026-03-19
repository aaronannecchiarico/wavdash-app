"""TFT Bonnet display driver using Pillow for rendering."""
import time
from typing import Optional

try:
    import board
    import digitalio
    from adafruit_rgb_display import st7789
    from PIL import Image, ImageDraw, ImageFont
    HAS_DISPLAY = True
except ImportError:
    HAS_DISPLAY = False

from audio_engine import MixerState, STEM_TYPES

# TFT Bonnet button/joystick GPIO pins (Adafruit Mini PiTFT)
BUTTON_A_PIN = 23
BUTTON_B_PIN = 24
JOYSTICK_UP = 17
JOYSTICK_DOWN = 22
JOYSTICK_LEFT = 27
JOYSTICK_RIGHT = 5
JOYSTICK_PRESS = 4

WIDTH = 240
HEIGHT = 240
STEM_LABELS = ["VOC", "DRM", "BAS", "GTR", "PNO", "OTH"]


class Display:
    """Drives the TFT Bonnet display and reads its joystick/buttons."""

    def __init__(self):
        if not HAS_DISPLAY:
            raise RuntimeError("Display libraries not available")

        cs_pin = digitalio.DigitalInOut(board.CE0)
        dc_pin = digitalio.DigitalInOut(board.D25)
        reset_pin = digitalio.DigitalInOut(board.D24)
        spi = board.SPI()

        self.display = st7789.ST7789(
            spi, height=HEIGHT, width=WIDTH,
            cs=cs_pin, dc=dc_pin, rst=reset_pin,
            baudrate=24000000,
        )

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
        for name, pin_num in [
            ("a", BUTTON_A_PIN), ("b", BUTTON_B_PIN),
            ("up", JOYSTICK_UP), ("down", JOYSTICK_DOWN),
            ("left", JOYSTICK_LEFT), ("right", JOYSTICK_RIGHT),
            ("press", JOYSTICK_PRESS),
        ]:
            pin = digitalio.DigitalInOut(getattr(board, f"D{pin_num}"))
            pin.direction = digitalio.Direction.INPUT
            pin.pull = digitalio.Pull.UP
            self.buttons[name] = pin

    def read_buttons(self) -> dict[str, bool]:
        """Read joystick + button states. Returns dict with True = pressed."""
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

        # Header — play state + song title
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
