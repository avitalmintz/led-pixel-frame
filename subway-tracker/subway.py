#!/usr/bin/env python3
# Live F-train tracker for Delancey St-Essex St on the 16x16 panel.
# Top half = uptown (toward Queens), bottom half = downtown (toward Brooklyn).
# Each half: a big orange F arrow that flows in its travel direction, plus a live
# countdown that goes white -> yellow -> orange -> flashing red as the train nears.
# Draws palette-index frames and streams them to the ESP32.
#
# Usage:
#   python subway.py demo   -> fake times (7 and 12), no network, ~14s
#   python subway.py        -> live MTA feed, runs until stopped
import sys
import time
import glob

PORT_DEFAULT = "/dev/cu.usbserial-0001"
BAUD = 115200
REFRESH = 20.0
FPS = 8
W = H = 16

# palette indices, must match PALETTE in frame_main.py
OFF, ORANGE, WHITE, YELLOW, RED, GREEN, DIMOR, BLUE, GRAY, AMBER, DIMWHITE, FAINT = range(12)

DIGITS = {
    "0": ["###", "#.#", "#.#", "#.#", "###"],
    "1": [".#.", "##.", ".#.", ".#.", "###"],
    "2": ["###", "..#", "###", "#..", "###"],
    "3": ["###", "..#", "###", "..#", "###"],
    "4": ["#.#", "#.#", "###", "..#", "..#"],
    "5": ["###", "#..", "###", "..#", "###"],
    "6": ["###", "#..", "###", "#.#", "###"],
    "7": ["###", "..#", "..#", ".#.", ".#."],
    "8": ["###", "#.#", "###", "#.#", "###"],
    "9": ["###", "#.#", "###", "..#", "###"],
    "-": ["...", "...", "###", "...", "..."],
}

ARROW_UP = ["..#..", ".###.", "#####", "..#..", "..#..", "..#..", "..#.."]
ARROW_DN = ["..#..", "..#..", "..#..", "..#..", "#####", ".###.", "..#.."]


def find_port():
    for pat in ("/dev/cu.usbserial*", "/dev/cu.SLAB_USBtoUART*",
                "/dev/cu.wchusbserial*"):
        hits = glob.glob(pat)
        if hits:
            return hits[0]
    return PORT_DEFAULT


def new_grid():
    return [[OFF] * W for _ in range(H)]


def blit(grid, glyph, top, left, color):
    for r, line in enumerate(glyph):
        for c, ch in enumerate(line):
            if ch == "#":
                rr, cc = top + r, left + c
                if 0 <= rr < H and 0 <= cc < W:
                    grid[rr][cc] = color


def draw_arrow(grid, up, top, frame):
    glyph = ARROW_UP if up else ARROW_DN
    direction = -1 if up else 1
    for r, line in enumerate(glyph):
        for c, ch in enumerate(line):
            if ch == "#":
                band = ((r + direction * frame) % 4) == 0
                grid[top + r][c] = WHITE if band else ORANGE


def urgency_color(mins):
    if mins <= 1:
        return RED
    if mins <= 4:
        return ORANGE
    if mins <= 8:
        return YELLOW
    return WHITE


def draw_minutes(grid, mins, top, frame):
    if mins is None:
        text, color, visible = "--", GRAY, True
    else:
        v = int(round(mins))
        v = 0 if v < 0 else (99 if v > 99 else v)
        text = str(v)
        color = urgency_color(mins)
        visible = ((frame // 2) % 2 == 0) if mins <= 1 else True
    if not visible:
        return
    dtop = top + 1
    if len(text) == 1:
        blit(grid, DIGITS.get(text, DIGITS["-"]), dtop, 11, color)
    else:
        blit(grid, DIGITS.get(text[-2], DIGITS["-"]), dtop, 7, color)
        blit(grid, DIGITS.get(text[-1], DIGITS["-"]), dtop, 11, color)


def render(up_mins, dn_mins, frame):
    grid = new_grid()
    draw_arrow(grid, True, 0, frame)       # uptown, top half
    draw_minutes(grid, up_mins, 0, frame)
    draw_arrow(grid, False, 9, frame)      # downtown, bottom half
    draw_minutes(grid, dn_mins, 9, frame)
    for c in range(W):                     # faint divider
        grid[7][c] = FAINT
    return grid


def pack(grid):
    out = bytearray()
    out.append(0xFF)
    for r in range(H):
        for c in range(W):
            out.append(grid[r][c] + 0x20)
    return bytes(out)


def get_trains(feed):
    feed.refresh()
    ref = feed.last_generated
    up, dn = [], []
    for t in feed.trips:
        if getattr(t, "route_id", None) != "F":
            continue
        d = getattr(t, "direction", "?")
        for stu in t.stop_time_updates:
            sid = getattr(stu, "stop_id", "") or ""
            if sid.startswith("F15"):
                arr = getattr(stu, "arrival", None)
                if not arr:
                    continue
                m = (arr - ref).total_seconds() / 60.0
                if m >= 0:
                    (up if d == "N" else dn).append(m)
    up.sort()
    dn.sort()
    return up, dn


def main():
    import serial
    demo = len(sys.argv) > 1 and sys.argv[1] == "demo"
    port = find_port()
    print("opening serial", port, flush=True)
    ser = serial.Serial(port, BAUD, timeout=1)
    ser.dtr = False
    ser.rts = False
    time.sleep(2.5)
    ser.reset_input_buffer()
    print("serial open", flush=True)

    frame = 0
    if demo:
        print("demo mode: fake times 7 and 12", flush=True)
        t0 = time.time()
        while time.time() - t0 < 14:
            ser.write(pack(render(7.0, 12.0, frame)))
            frame += 1
            time.sleep(1.0 / FPS)
        print("demo done", flush=True)
        return

    from nyct_gtfs import NYCTFeed
    print("loading MTA feed...", flush=True)
    feed = NYCTFeed("F")
    up, dn = get_trains(feed)
    last_fetch = time.time()
    print("uptown", [round(m, 1) for m in up[:3]],
          "downtown", [round(m, 1) for m in dn[:3]], flush=True)

    while True:
        now = time.time()
        if now - last_fetch > REFRESH:
            try:
                up, dn = get_trains(feed)
                print("refresh uptown", [round(m, 1) for m in up[:3]],
                      "downtown", [round(m, 1) for m in dn[:3]], flush=True)
            except Exception as e:
                print("refresh error:", e, flush=True)
            last_fetch = now
        elapsed = (now - last_fetch) / 60.0
        up_eff = (up[0] - elapsed) if up else None
        dn_eff = (dn[0] - elapsed) if dn else None
        ser.write(pack(render(up_eff, dn_eff, frame)))
        frame += 1
        time.sleep(1.0 / FPS)


if __name__ == "__main__":
    main()
