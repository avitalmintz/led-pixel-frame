# Resident visualizer firmware for the ESP32. Gets copied to the board as main.py
# so it runs on boot. It listens on the USB serial for frames from the Mac and
# draws equalizer bars.
#
# Frame format: one sync byte 0xFF, then 16 bytes (one per column).
# Each column byte = height (0..16) + 0x20. The +0x20 keeps every data byte
# clear of 0x03 (Ctrl-C), so the board stays interruptible for code updates.
import sys
import time
from machine import Pin
from neopixel import NeoPixel

DATA_PIN = 13
NUM_LEDS = 256
W = 16
H = 16
B = 22       # brightness, keep low on USB power

np = NeoPixel(Pin(DATA_PIN), NUM_LEDS)


def xy(x, y):
    if y % 2 == 0:
        return y * W + x
    return y * W + (W - 1 - x)


def level_color(level):
    if level <= 7:
        return (0, B, 0)        # green low
    if level <= 11:
        return (B, B, 0)        # yellow mid
    return (B, 0, 0)            # red high


PEAK = (B, B, B)


def show(heights):
    np.fill((0, 0, 0))
    for x in range(W):
        h = heights[x]
        for level in range(h):
            np[xy(x, level)] = level_color(level)
        if h > 0:
            np[xy(x, h - 1)] = PEAK
    np.write()


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
time.sleep_ms(300)
np.fill((0, 0, 0))
np.write()

heights = [0] * W
while True:
    b = sys.stdin.buffer.read(1)
    if not b or b[0] != 0xFF:
        continue
    frame = read_exact(W)
    for x in range(W):
        v = frame[x] - 0x20
        if v < 0:
            v = 0
        elif v > H:
            v = H
        heights[x] = v
    show(heights)
