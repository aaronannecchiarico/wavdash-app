"""LED diagnostic — lights up each pixel pair one at a time.

Run on the Pi to determine the physical pixel-to-fader mapping.
Each pair stays lit for 4 seconds. Note which physical fader lights up.
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
COLOR_NAMES = ["RED", "GREEN", "BLUE", "YELLOW", "MAGENTA", "CYAN"]

print("LED Diagnostic — watch which physical fader LEDs light up")
print("Each pair lights for 4 seconds. Note the physical fader position.")
print("=" * 60)

for pair in range(6):
    pixels.fill((0, 0, 0))
    idx_a = pair * 2
    idx_b = pair * 2 + 1
    color = COLORS[pair]
    pixels[idx_a] = color
    pixels[idx_b] = color
    print(f"Pixel pair {pair} (indices {idx_a},{idx_b}) = {COLOR_NAMES[pair]}  [4s]")
    time.sleep(4)

# All on at once with different colors to confirm
print("\nAll pairs lit with different colors:")
for pair in range(6):
    pixels[pair * 2] = COLORS[pair]
    pixels[pair * 2 + 1] = COLORS[pair]
    print(f"  Pair {pair} = {COLOR_NAMES[pair]}")

print("\nLeaving all lit for 10 seconds — note the color at each physical fader position")
print("Report: fader 1 (leftmost) = ?, fader 2 = ?, ... fader 6 (rightmost) = ?")
time.sleep(10)

pixels.fill((0, 0, 0))
print("Done!")
