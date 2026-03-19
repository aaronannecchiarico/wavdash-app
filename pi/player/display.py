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

    def render_loading(self, song):
        """Render a loading screen while stems are being buffered."""
        self.draw.rectangle((0, 0, WIDTH, HEIGHT), fill=(0, 0, 0))

        self.draw.text((10, 80), "Loading...", fill=(0, 200, 255), font=self.font_large)
        self.draw.text((10, 110), song.title[:22], fill=(255, 255, 255), font=self.font)

        # Simple loading bar outline
        bar_y = 145
        self.draw.rectangle((30, bar_y, WIDTH - 30, bar_y + 10), outline=(100, 100, 100))

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

    def render_loading(self, song):
        pass

    def render_now_playing(self, song, mixer_state, position_s, duration_s):
        pass
