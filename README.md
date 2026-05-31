# led-pixel-frame

Pixel-art displays for a 16x16 WS2812B LED panel driven by an ESP32. Two
independent projects live in this repo:

- **subway-tracker**: a live NYC F-train countdown for the Delancey St-Essex St
  station, uptown and downtown at a glance.
- **audio-visualizer**: a real-time equalizer that dances to your microphone.

## How it works

The ESP32 runs a tiny "dumb display" firmware that  
listens on the USB serial port and lights pixels. All of the
artwork is computed on the Mac in Python and streamed over the cable, frame by
frame. That means you can change the look instantly by editing Python, with no
re-flashing of the board.

The panel is wired in a serpentine layout (each row runs the opposite
direction from the last), 256 WS2812B pixels total, data on GPIO 13, GRB color
order. Brightness is kept low on purpose because the panel is powered over USB.

## Hardware

- ESP32 dev board running MicroPython
- WS2812B 16x16 LED panel (256 pixels), data line on GPIO 13
- A USB cable from the Mac to the ESP32

## Setup

Flash MicroPython onto the ESP32 once, then use `mpremote` to copy firmware to
the board and to run the on-board demos:

```
pip install mpremote
```

The Mac scripts auto-detect the serial port (they look for `/dev/cu.usbserial*`
and similar), so you usually do not need to configure anything. Each project
lists its own Python dependencies below.

---

## subway-tracker

Live F-train arrivals at Delancey St-Essex St. The panel splits in half: the
top shows uptown trains (toward Queens) and the bottom shows downtown (toward
Brooklyn). Each half has an orange F arrow that flows in its travel direction,
next to a countdown that shifts white, yellow, orange, then flashing red as the
train gets close. Data comes from the MTA's public realtime feed, no API key
needed (via the `nyct-gtfs` library).

Files:
- `subway.py`: the Mac renderer that fetches arrivals and streams frames
- `frame_main.py`: the ESP32 display firmware (copy to the board as `main.py`)
- `test_mta.py`: a quick check that live data is flowing

Run it:

```
pip install -r subway-tracker/requirements.txt

# copy the display firmware to the board (once)
mpremote connect /dev/cu.usbserial-0001 fs cp subway-tracker/frame_main.py :main.py
mpremote connect /dev/cu.usbserial-0001 reset

# live trains
python subway-tracker/subway.py

# or an offline demo with fake times (7 and 12 minutes)
python subway-tracker/subway.py demo
```

---

## audio-visualizer

Listens to the Mac microphone, splits the sound into 16 frequency bands, and
draws bouncing equalizer bars: green low, yellow mid, red high, with a bright
cap riding the top of each bar. It reacts to anything the mic can hear,
including music playing out of your speakers.

Files:
- `visualizer.py`: the Mac script that captures audio and streams bar heights
- `viz_main.py`: the ESP32 bars firmware (copy to the board as `main.py`)
- `bars_demo.py`: fake bouncing bars to preview the look, runs on the board

Run it:

```
pip install -r audio-visualizer/requirements.txt

# copy the bars firmware to the board (once)
mpremote connect /dev/cu.usbserial-0001 fs cp audio-visualizer/viz_main.py :main.py
mpremote connect /dev/cu.usbserial-0001 reset

# start the visualizer (allow microphone access if macOS asks)
python audio-visualizer/visualizer.py

# or preview the look with fake data, no mic needed
mpremote run audio-visualizer/bars_demo.py
```
