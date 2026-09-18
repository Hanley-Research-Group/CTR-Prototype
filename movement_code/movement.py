"""
stress_test.py – sequential combination stress test

Animation sequence (loops forever):
  1. A only
  2. B only
  3. C only
  4. A + B
  5. A + C
  6. B + C
  7. A + B + C

Linear axes: bounce ±LINEAR_MM (×16 steps)
Rotary axes: bounce ±ROTATE_DEG

Press +/- to adjust speed, r to reverse, q to quit.
"""

import serial
import time
import sys
import tty
import termios
import threading

# ── Config ────────────────────────────────────────────────────────────
COM_PORT    = "/dev/cu.usbmodem3881376934341"
BAUD_RATE   = 250_000
LINEAR_MM   = 5      # bounce distance in mm
ROTATE_DEG  = 360     # bounce distance in degrees
FEED_RATE   = 2000    # starting speed
FEED_STEP   = 500     # how much +/- changes the feed rate
# ─────────────────────────────────────────────────────────────────────

feed_rate = FEED_RATE
running   = True
direction = 1   # +1 = normal, -1 = reversed

# Each "cart" maps to a linear axis (X/Y/Z) and a rotary axis (A/B/C)
CARTS = {
    "A": ("X", "A"),
    "B": ("Y", "B"),
    "C": ("Z", "C"),
}

SEQUENCE = [
    ["A"],
    ["B"],
    ["C"],
    ["A", "B"],
    ["A", "C"],
    ["B", "C"],
    ["A", "B", "C"],
]

def send(ser, cmd):
    print(f"  >> {cmd.strip()}")
    ser.write((cmd + "\n").encode("ascii"))
    time.sleep(0.05)

def build_move(active_carts, d, f, extended):
    """Build a G0 command. extended=True → move out, False → return home."""
    lin = LINEAR_MM * 16
    rot = ROTATE_DEG
    parts = [f"F{f}"]
    # All axes: active ones move, inactive ones stay at 0
    for cart, (lin_ax, rot_ax) in CARTS.items():
        if cart in active_carts:
            val_lin = lin * d if extended else 0
            val_rot = rot * d if extended else 0
        else:
            val_lin = 0
            val_rot = 0
        parts.append(f"{lin_ax}{val_lin}")
        parts.append(f"{rot_ax}{val_rot}")
    return "G0 " + " ".join(parts)

# ── Live keypress thread ──────────────────────────────────────────────
def key_listener():
    global feed_rate, running, direction
    fd = sys.stdin.fileno()
    old = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        while running:
            ch = sys.stdin.read(1)
            if ch in ("+", "="):
                feed_rate = min(feed_rate + FEED_STEP, 100_000)
                print(f"\n  [speed] F={feed_rate}")
            elif ch == "-":
                feed_rate = max(feed_rate - FEED_STEP, 100)
                print(f"\n  [speed] F={feed_rate}")
            elif ch == "r":
                direction *= -1
                label = "REVERSED" if direction == -1 else "NORMAL"
                print(f"\n  [direction] {label}")
            elif ch in ("\x03", "q"):
                running = False
                break
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old)

# ── Main ──────────────────────────────────────────────────────────────
print(f"Opening {COM_PORT} at {BAUD_RATE} baud...")
ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=2)
time.sleep(2)
print("Connected.\n")

send(ser, "G92 X0 Y0 Z0 A0 B0 C0")
print(f"Starting at F={feed_rate}  |  + speed up   - slow down   r reverse   q quit\n")

key_thread = threading.Thread(target=key_listener, daemon=True)
key_thread.start()

try:
    while running:
        for combo in SEQUENCE:
            if not running:
                break
            label = " + ".join(combo)
            print(f"\n── [{label}] ──")
            f = feed_rate
            d = direction
            send(ser, build_move(combo, d, f, extended=True))
            if not running:
                break
            send(ser, build_move(combo, d, f, extended=False))

except KeyboardInterrupt:
    pass

running = False
print("\n\nStopped. Returning to home...")
send(ser, "G0 F10000 X0 Y0 Z0 A0 B0 C0")
time.sleep(2)
ser.close()
print("Done.")