"""LED diagnostic — lights up each pixel pair one at a time.

Run on the Pi to determine the physical pixel-to-fader mapping.
For each pair, note which physical fader's LEDs light up.
"""
import time
import board
from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw.neopixel import NeoPixel

NEOPIXEL_PIN = 20
NEOPIXEL_COUNT = 12

i2c = board.I2C()
pcb = Seesaw(i2c)
pixels = NeoPixel(pcb, NEOPIXEL_PIN, NEOPIXEL_COUNT)
pixels.brightness = 0.4

COLORS = [
    (255, 0, 0),    # Red
    (0, 255, 0),    # Green
    (0, 0, 255),    # Blue
    (255, 255, 0),  # Yellow
    (255, 0, 255),  # Magenta
    (0, 255, 255),  # Cyan
]

print("LED Diagnostic — watch which physical fader LEDs light up")
print("=" * 60)

for pair in range(6):
    pixels.fill((0, 0, 0))
    idx_a = pair * 2
    idx_b = pair * 2 + 1
    color = COLORS[pair]
    pixels[idx_a] = color
    pixels[idx_b] = color
    color_name = ["RED", "GREEN", "BLUE", "YELLOW", "MAGENTA", "CYAN"][pair]
    print(f"Pixel pair {pair} (indices {idx_a},{idx_b}) = {color_name}")
    print(f"  -> Which physical fader position is lit? (1=leftmost, 6=rightmost)")
    input("  Press Enter for next pair...")

pixels.fill((0, 0, 0))
print("\nDone! Report the mapping: pixel pair -> physical fader position")
