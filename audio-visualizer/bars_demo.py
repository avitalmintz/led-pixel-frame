# Equalizer bars demo with FAKE bouncing data, to lock in the look before we
# hook up real sound. Green low, yellow mid, red high, bright cap on top of each
# bar. Serpentine panel, bottom-left is pixel 0, y=0 is the bottom row.
import time
import math
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

frames = 360
for f in range(frames):
    np.fill((0, 0, 0))
    for x in range(W):
        a = math.sin(f * 0.15 + x * 0.6) * 0.5 + 0.5
        b = math.sin(f * 0.31 + x * 1.3) * 0.5 + 0.5
        h = int(a * 9 + b * 7)
        if h > H:
            h = H
        for level in range(h):
            np[xy(x, level)] = level_color(level)
        if h > 0:
            np[xy(x, h - 1)] = PEAK
    np.write()
    time.sleep_ms(40)

np.fill((0, 0, 0))
np.write()
print("bars demo done")
