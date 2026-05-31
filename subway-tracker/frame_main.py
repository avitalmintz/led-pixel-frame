# Generic 16x16 frame display firmware (gets copied to the board as main.py).
# The Mac does all the drawing and streams frames here.
#
# Protocol: sync byte 0xFF, then 256 bytes (one palette index per pixel) in
# row-major order with row 0 = TOP, left to right. Each byte = index + 0x20,
# which keeps every data byte clear of 0x03 (Ctrl-C) so the board stays
# interruptible for code updates.
import sys
import time
from machine import Pin
from neopixel import NeoPixel

DATA_PIN = 13
NUM_LEDS = 256
W = 16
H = 16

np = NeoPixel(Pin(DATA_PIN), NUM_LEDS)

# Palette, already dimmed for USB power. Index order must match the Mac script.
PALETTE = [
    (0, 0, 0),       # 0  off
    (40, 15, 3),     # 1  F orange
    (35, 35, 35),    # 2  white
    (40, 40, 0),     # 3  yellow
    (55, 0, 0),      # 4  red
    (0, 40, 0),      # 5  green
    (16, 6, 1),      # 6  dim orange
    (0, 10, 40),     # 7  blue
    (10, 10, 10),    # 8  gray
    (45, 22, 0),     # 9  amber
    (25, 25, 25),    # 10 dim white
    (3, 3, 3),       # 11 faint
    (0, 0, 0),       # 12
    (0, 0, 0),       # 13
    (0, 0, 0),       # 14
    (0, 0, 0),       # 15
]


def xy(x, y):
    if y % 2 == 0:
        return y * W + x
    return y * W + (W - 1 - x)


def read_exact(n):
    buf = bytearray()
    while len(buf) < n:
        chunk = sys.stdin.buffer.read(n - len(buf))
        if chunk:
            buf.extend(chunk)
    return buf


# short blue blink so we can see the firmware booted
np.fill((0, 0, 3))
np.write()
time.sleep_ms(250)
np.fill((0, 0, 0))
np.write()

while True:
    b = sys.stdin.buffer.read(1)
    if not b or b[0] != 0xFF:
        continue
    frame = read_exact(NUM_LEDS)
    for row in range(H):           # row 0 = top of the image
        y = 15 - row
        base = row * W
        for x in range(W):
            idx = frame[base + x] - 0x20
            if idx < 0 or idx >= len(PALETTE):
                idx = 0
            np[xy(x, y)] = PALETTE[idx]
    np.write()
