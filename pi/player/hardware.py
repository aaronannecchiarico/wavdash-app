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
        long_press_ms: int = 700,
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

        PCB layout: two rows of 6 LEDs each.
        - Top row (pixels 0-5): idle dim green
        - Bottom row (pixels 6-11): active stem indicators near buttons
        Stem 0 = pixel 6, stem 1 = pixel 7, ... stem 5 = pixel 11.
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

            # Bottom row: pixels 6-11 = stems 0-5
            self.pixels[6 + stem_idx] = color
            # Top row: dim green idle
            self.pixels[stem_idx] = (0, 30, 0)
