# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

"""
This test will initialize the display using displayio and draw a solid white
background, a smaller black rectangle, and some white text.
"""

import time
import board
import digitalio
# import displayio

# from fourwire import FourWire
# import terminalio
# from adafruit_display_text import label
# from i2cdisplaybus import I2CDisplayBus

from adafruit_seesaw.analoginput import AnalogInput
from adafruit_seesaw.digitalio import DigitalIO
from adafruit_seesaw.seesaw import Seesaw
from adafruit_seesaw.neopixel import NeoPixel
from adafruit_seesaw.rotaryio import IncrementalEncoder
from pydub import AudioSegment
from pydub.playback import play

# import adafruit_displayio_ssd1306

# displayio.release_displays()

# Use for I2C
i2c = board.I2C()  # uses board.SCL and board.SDA
# i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller

ANO_Encoder = Seesaw(i2c, addr=0x4A)

ANO_Encoder.pin_mode(1, ANO_Encoder.INPUT_PULLUP)
ANO_Encoder.pin_mode(2, ANO_Encoder.INPUT_PULLUP)
ANO_Encoder.pin_mode(3, ANO_Encoder.INPUT_PULLUP)
ANO_Encoder.pin_mode(4, ANO_Encoder.INPUT_PULLUP)
ANO_Encoder.pin_mode(5, ANO_Encoder.INPUT_PULLUP)

select = DigitalIO(ANO_Encoder, 1)
select_held = False
up = DigitalIO(ANO_Encoder, 2)
up_held = False
left = DigitalIO(ANO_Encoder, 3)
left_held = False
down = DigitalIO(ANO_Encoder, 4)
down_held = False
right = DigitalIO(ANO_Encoder, 5)
right_held = False

encoder = IncrementalEncoder(ANO_Encoder)
last_position = None

buttons = [select, up, left, down, right]
button_names = ["Select", "Up", "Left", "Down", "Right"]
button_states = [select_held, up_held, left_held, down_held, right_held]

# display_bus = I2CDisplayBus(i2c, device_address=0x3C)

ss = Seesaw(i2c)

NEOPIXEL_PIN = 20  # Can be any pin
NEOPIXEL_NUM = 12  # No more than 60 pixels!

pixels = NeoPixel(ss, NEOPIXEL_PIN, NEOPIXEL_NUM)
pixels.brightness = 0.3  # Not so bright!

for pixel in range(NEOPIXEL_NUM):
    pixels[pixel] = (255, 0, 0)  # Bright red!

SLIDER_0_PIN = 0
slider_0 = AnalogInput(ss, SLIDER_0_PIN)

SLIDER_1_PIN = 1
slider_1 = AnalogInput(ss, SLIDER_1_PIN)

SLIDER_2_PIN = 2
slider_2 = AnalogInput(ss, SLIDER_2_PIN)

SLIDER_3_PIN = 3
slider_3 = AnalogInput(ss, SLIDER_3_PIN)

SLIDER_4_PIN = 6
slider_4 = AnalogInput(ss, SLIDER_4_PIN)

SLIDER_5_PIN = 7
slider_5 = AnalogInput(ss, SLIDER_5_PIN)

BTN_0_PIN = 19
btn_0 = DigitalIO(ss, BTN_0_PIN)
btn_0.direction = digitalio.Direction.INPUT
btn_0.pull = digitalio.Pull.UP

BTN_1_PIN = 18
btn_1 = DigitalIO(ss, BTN_1_PIN)
btn_1.direction = digitalio.Direction.INPUT
btn_1.pull = digitalio.Pull.UP

BTN_2_PIN = 14
btn_2 = DigitalIO(ss, BTN_2_PIN)
btn_2.direction = digitalio.Direction.INPUT
btn_2.pull = digitalio.Pull.UP

BTN_3_PIN = 13
btn_3 = DigitalIO(ss, BTN_3_PIN)
btn_3.direction = digitalio.Direction.INPUT
btn_3.pull = digitalio.Pull.UP

BTN_4_PIN = 12
btn_4 = DigitalIO(ss, BTN_4_PIN)
btn_4.direction = digitalio.Direction.INPUT
btn_4.pull = digitalio.Pull.UP

BTN_5_PIN = 9
btn_5 = DigitalIO(ss, BTN_5_PIN)
btn_5.direction = digitalio.Direction.INPUT
btn_5.pull = digitalio.Pull.UP

WIDTH = 128
HEIGHT = 64  # Change to 64 if needed
BORDER = 2

# display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=WIDTH, height=HEIGHT)

# # Make the display context
# splash = displayio.Group()
# display.root_group = splash

# # Draw a label
# text = "Hello World!"
# text_area_0 = label.Label(terminalio.FONT, text=text, color=0xFFFFFF, x=5, y=5)
# text_area_1 = label.Label(terminalio.FONT, text=text, color=0xFFFFFF, x=5, y=15)
# text_area_2 = label.Label(terminalio.FONT, text=text, color=0xFFFFFF, x=5, y=25)
# text_area_3 = label.Label(terminalio.FONT, text=text, color=0xFFFFFF, x=5, y=35)
# text_area_4 = label.Label(terminalio.FONT, text=text, color=0xFFFFFF, x=5, y=45)
# text_area_5 = label.Label(terminalio.FONT, text=text, color=0xFFFFFF, x=5, y=55)
# splash.append(text_area_0)
# splash.append(text_area_1)
# splash.append(text_area_2)
# splash.append(text_area_3)
# splash.append(text_area_4)
# splash.append(text_area_5)
sound = AudioSegment.from_file("/home/aannecchiarico/test_files/vocals.wav", format="wav")


while True:
    position = encoder.position

    if position != last_position:
        last_position = position
        print(f"Position: {position}")

    for b in range(5):
        if not buttons[b].value and button_states[b] is False:
            button_states[b] = True
            print(f"{button_names[b]} button pressed")

        if buttons[b].value and button_states[b] is True:
            button_states[b] = False
            print(f"{button_names[b]} button released")
    if btn_0.value == False:
        play(sound)
    print(f"0: B: {int(btn_0.value)} S: {slider_0.value}")
    print(f"1: B: {int(btn_1.value)} S: {slider_1.value}")
    print(f"2: B: {int(btn_2.value)} S: {slider_2.value}")
    print(f"3: B: {int(btn_3.value)} S: {slider_3.value}")
    print(f"4: B: {int(btn_4.value)} S: {slider_4.value}")
    print(f"5: B: {int(btn_5.value)} S: {slider_5.value}")


