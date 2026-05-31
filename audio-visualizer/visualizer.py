#!/usr/bin/env python3
# Mac side of the sound visualizer. Listens to the mic, splits the sound into 16
# frequency bands, and streams bar heights to the ESP32 over the USB serial.
#
# Frame sent per update: one sync byte 0xFF, then 16 bytes (height 0..16 + 0x20).
import time
import glob
import numpy as np
import sounddevice as sd
import serial

PORT = "/dev/cu.usbserial-0001"
BAUD = 115200
SR = 44100        # mic sample rate
BS = 1024         # samples per chunk -> about 43 updates per second
NB = 16           # number of bars (panel width)
HMAX = 16         # panel height
SENS = 1.3        # overall sensitivity (raise if bars stay short)
DECAY = 0.82      # how slowly bars fall (0..1, higher = slower)


def find_port():
    for pat in ("/dev/cu.usbserial*", "/dev/cu.SLAB_USBtoUART*",
                "/dev/cu.wchusbserial*"):
        hits = glob.glob(pat)
        if hits:
            return hits[0]
    return PORT


def main():
    port = find_port()
    print("opening serial", port, flush=True)
    ser = serial.Serial(port, BAUD, timeout=1)
    ser.setDTR(False)
    ser.setRTS(False)
    time.sleep(2.5)                 # let the board boot into the firmware
    ser.reset_input_buffer()
    print("serial open", flush=True)

    freqs = np.fft.rfftfreq(BS, 1.0 / SR)
    edges = np.logspace(np.log10(40), np.log10(12000), NB + 1)
    band_bins = []
    for i in range(NB):
        idx = np.where((freqs >= edges[i]) & (freqs < edges[i + 1]))[0]
        if len(idx) == 0:
            idx = np.array([int(np.argmin(np.abs(freqs - edges[i])))])
        band_bins.append(idx)
    window = np.hanning(BS)
    treble_boost = np.linspace(1.0, 3.0, NB)

    running_max = 1e-6
    prev = np.zeros(NB)

    print("starting mic - allow microphone access if macOS asks", flush=True)
    stream = sd.InputStream(channels=1, samplerate=SR, blocksize=BS)
    stream.start()
    print("streaming - play music or clap!", flush=True)

    last_dbg = time.time()
    while True:
        data, _ = stream.read(BS)
        samples = data[:, 0]
        spec = np.abs(np.fft.rfft(samples * window))
        vals = np.array([spec[b].mean() for b in band_bins]) * treble_boost
        vals = np.sqrt(vals)
        running_max = max(running_max * 0.999, float(vals.max()))
        norm = vals / (running_max + 1e-9)
        heights = np.clip(norm * HMAX * SENS, 0, HMAX)
        heights = np.maximum(heights, prev * DECAY)
        prev = heights
        ser.write(bytes([0xFF] + [int(h) + 0x20 for h in heights]))

        now = time.time()
        if now - last_dbg > 1.0:
            last_dbg = now
            print("max bar height:", int(heights.max()), flush=True)


if __name__ == "__main__":
    main()
