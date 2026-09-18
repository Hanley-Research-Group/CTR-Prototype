"""
ctr_controller.py – on-screen d-pad controller for the CTR robot

Serial handling is identical to connection_test.py:
  - 2 s sleep after Serial() open
  - 0.05 s sleep after every write
  - raw ASCII + "\\n"

Requirements:
    pip install pyserial

Usage:
    python ctr_controller.py
"""

import tkinter as tk
import serial
import time
import threading
import builtins

# ── Config ────────────────────────────────────────────────────────────
COM_PORT     = "/dev/cu.usbmodem3881376934341"
BAUD_RATE    = 250_000
STEP_LIN     = 1      # mm per button press
STEP_ROT     = 5      # degrees per button press
DEFAULT_FEED = 500    # mm/min (feedrate / speed)
MIN_FEED     = 10     # mm/min
MAX_FEED     = 5000   # mm/min
# ─────────────────────────────────────────────────────────────────────

# ── Serial – identical to connection_test.py ──────────────────────────
print(f"Opening {COM_PORT} at {BAUD_RATE} baud...")
ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=2)
time.sleep(2)
print("Connected.")

send_lock = threading.Lock()

def send(cmd):
    """Send exactly like connection_test.py: encode, write, 50 ms pause."""
    print(f"  >> {cmd.strip()}")
    with send_lock:
        ser.write((cmd + "\n").encode("ascii"))
    time.sleep(0.05)

send("G92 X0 Y0 Z0 A0 B0 C0")   # zero on startup

# ── Robot state ───────────────────────────────────────────────────────
state = {"X": 0.0, "Y": 0.0, "Z": 0.0, "A": 0.0, "B": 0.0, "C": 0.0}
steps = {"lin": float(STEP_LIN), "rot": float(STEP_ROT)}
feed  = {"rate": float(DEFAULT_FEED)}   # current feedrate in mm/min

def send_move():
    cmd = (
        f"G0 "
        f"X{state['X'] * 16:.2f} "
        f"Y{state['Y'] * 16:.2f} "
        f"Z{state['Z'] * 16:.2f} "
        f"A{state['A']:.1f} "
        f"B{state['B']:.1f} "
        f"C{state['C']:.1f} "
        f"F{feed['rate']:.0f}"
    )
    threading.Thread(target=send, args=(cmd,), daemon=True).start()

def jog(axis, sign):
    step = steps["lin"] if axis in ("X", "Y", "Z") else steps["rot"]
    state[axis] = round(state[axis] + sign * step, 3)
    send_move()
    refresh_labels()

def home_all():
    for k in state:
        state[k] = 0.0
    threading.Thread(target=send, args=("G92 X0 Y0 Z0 A0 B0 C0",), daemon=True).start()
    refresh_labels()

def nudge_feed(delta):
    """Bump feedrate by delta, clamped to [MIN_FEED, MAX_FEED]."""
    feed["rate"] = max(MIN_FEED, min(MAX_FEED, feed["rate"] + delta))
    feed_var.set(feed["rate"])
    refresh_feed_label()

# ── Styling ───────────────────────────────────────────────────────────
BG        = "#0d0d0f"
PANEL_BG  = "#16161a"
ACCENT    = "#00e5ff"
ACCENT2   = "#f59e0b"   # warm gold for the speed section
DIM       = "#334155"
TEXT      = "#e2e8f0"
BTN_BG    = "#1e1e26"
LABEL_DIM = "#64748b"
FONT_MONO = ("Courier New", 10)
FONT_HEAD = ("Courier New", 11, "bold")
FONT_BIG  = ("Courier New", 20, "bold")
FONT_BTN  = ("Courier New", 16, "bold")
FONT_SM   = ("Courier New", 9)

# ── Build window ──────────────────────────────────────────────────────
root = tk.Tk()
root.title("CTR Controller")
root.configure(bg=BG)
root.resizable(False, False)

val_labels = {}

def refresh_labels():
    for axis, lbl in val_labels.items():
        unit = "mm" if axis in ("X", "Y", "Z") else "°"
        lbl.config(text=f"{state[axis]:+.1f} {unit}")

# ── Serial log (redirect print → pane) ───────────────────────────────
def _log_print(*args, **kwargs):
    msg = " ".join(str(a) for a in args)
    builtins.__orig_print__(msg, **kwargs)
    try:
        log_text.config(state="normal")
        log_text.insert("end", msg + "\n")
        log_text.see("end")
        log_text.config(state="disabled")
    except Exception:
        pass

builtins.__orig_print__ = builtins.print
builtins.print = _log_print

# ── Widgets ───────────────────────────────────────────────────────────
def dpad_btn(parent, symbol, cmd, row, col):
    b = tk.Button(
        parent, text=symbol, font=FONT_BTN,
        bg=BTN_BG, fg=TEXT, activebackground=ACCENT,
        activeforeground=BG, relief="flat", bd=0,
        width=3, height=1, cursor="hand2", command=cmd,
    )
    b.grid(row=row, column=col, padx=3, pady=3, sticky="nsew")
    b.bind("<Enter>", lambda e: b.config(bg=ACCENT, fg=BG))
    b.bind("<Leave>", lambda e: b.config(bg=BTN_BG, fg=TEXT))
    return b

def axis_panel(parent, title, axis, up_sym, dn_sym, unit, row, col):
    frame = tk.Frame(parent, bg=PANEL_BG, bd=0,
                     highlightthickness=1, highlightbackground=DIM)
    frame.grid(row=row, column=col, padx=8, pady=8, sticky="nsew")

    tk.Label(frame, text=title, font=FONT_HEAD, bg=PANEL_BG,
             fg=ACCENT).grid(row=0, column=0, columnspan=3, pady=(10, 2))

    val = tk.Label(frame, text=f"+0.0 {unit}", font=FONT_BIG,
                   bg=PANEL_BG, fg=TEXT, width=9)
    val.grid(row=1, column=0, columnspan=3, pady=4)
    val_labels[axis] = val

    bf = tk.Frame(frame, bg=PANEL_BG)
    bf.grid(row=2, column=0, columnspan=3, pady=(4, 6))
    dpad_btn(bf, up_sym, lambda: jog(axis, +1), 0, 1)
    tk.Label(bf, text=axis, font=FONT_HEAD, bg=PANEL_BG,
             fg=LABEL_DIM, width=3).grid(row=1, column=1, pady=1)
    dpad_btn(bf, dn_sym, lambda: jog(axis, -1), 2, 1)

    step_lbl = tk.Label(frame, text="", font=FONT_SM, bg=PANEL_BG, fg=LABEL_DIM)
    step_lbl.grid(row=3, column=0, columnspan=3, pady=(0, 8))

    def _tick():
        s = steps["lin"] if axis in ("X", "Y", "Z") else steps["rot"]
        step_lbl.config(text=f"step  {s:.1f} {unit}")
        frame.after(200, _tick)
    _tick()

# ── Header ────────────────────────────────────────────────────────────
hdr = tk.Frame(root, bg=BG)
hdr.pack(fill="x", padx=16, pady=(16, 4))
tk.Label(hdr, text="◈ CTR CONTROLLER", font=("Courier New", 15, "bold"),
         bg=BG, fg=ACCENT).pack(side="left")
tk.Label(hdr, text=f"  {COM_PORT}", font=FONT_SM,
         bg=BG, fg=LABEL_DIM).pack(side="left")
tk.Frame(root, bg=DIM, height=1).pack(fill="x", padx=16, pady=4)

# ── Axis panels ───────────────────────────────────────────────────────
panels = tk.Frame(root, bg=BG)
panels.pack(padx=16, pady=8)
axis_panel(panels, "LINEAR X", "X", "▲", "▼", "mm", 0, 0)
axis_panel(panels, "LINEAR Y", "Y", "▲", "▼", "mm", 0, 1)
axis_panel(panels, "LINEAR Z", "Z", "▲", "▼", "mm", 0, 2)
axis_panel(panels, "ROTARY A", "A", "↻", "↺",  "°", 1, 0)
axis_panel(panels, "ROTARY B", "B", "↻", "↺",  "°", 1, 1)
axis_panel(panels, "ROTARY C", "C", "↻", "↺",  "°", 1, 2)
tk.Frame(root, bg=DIM, height=1).pack(fill="x", padx=16, pady=4)

# ── Controls bar ──────────────────────────────────────────────────────
ctrl = tk.Frame(root, bg=BG)
ctrl.pack(padx=16, pady=8, fill="x")

home_btn = tk.Button(
    ctrl, text="⌂  HOME ALL", font=FONT_HEAD,
    bg="#1e293b", fg="#f87171", activebackground="#f87171",
    activeforeground=BG, relief="flat", bd=0,
    cursor="hand2", padx=16, pady=8, command=home_all,
)
home_btn.pack(side="left")
home_btn.bind("<Enter>", lambda e: home_btn.config(bg="#f87171", fg=BG))
home_btn.bind("<Leave>", lambda e: home_btn.config(bg="#1e293b", fg="#f87171"))

def make_slider(parent, label, var, from_, to, key):
    f = tk.Frame(parent, bg=BG)
    f.pack(side="right", padx=12)
    tk.Label(f, text=label, font=FONT_SM, bg=BG, fg=LABEL_DIM).pack()
    tk.Scale(f, variable=var, from_=from_, to=to, orient="horizontal",
             length=110, bg=BG, fg=TEXT, troughcolor=DIM,
             highlightthickness=0, bd=0, font=FONT_SM, sliderlength=16,
             resolution=0.1,
             command=lambda v: steps.update({key: float(v)})).pack()

lin_var = tk.DoubleVar(value=STEP_LIN)
rot_var = tk.DoubleVar(value=STEP_ROT)
make_slider(ctrl, "lin step (mm)", lin_var, 0.1, 100,  "lin")
make_slider(ctrl, "rot step (°)",  rot_var,   1, 45, "rot")
tk.Frame(root, bg=DIM, height=1).pack(fill="x", padx=16, pady=4)

# ── Speed / Feedrate panel ────────────────────────────────────────────
speed_frame = tk.Frame(root, bg=PANEL_BG, bd=0,
                       highlightthickness=1, highlightbackground=DIM)
speed_frame.pack(fill="x", padx=16, pady=(4, 8))

tk.Label(speed_frame, text="SPEED  (feedrate)", font=FONT_HEAD,
         bg=PANEL_BG, fg=ACCENT2).pack(side="left", padx=14, pady=10)

feed_var = tk.DoubleVar(value=DEFAULT_FEED)

feed_display = tk.Label(speed_frame, text=f"{DEFAULT_FEED:.0f} mm/min",
                        font=("Courier New", 13, "bold"),
                        bg=PANEL_BG, fg=TEXT, width=12, anchor="e")
feed_display.pack(side="right", padx=14)

def refresh_feed_label(*_):
    v = feed_var.get()
    feed["rate"] = v
    feed_display.config(text=f"{v:.0f} mm/min")

feed_slider = tk.Scale(
    speed_frame, variable=feed_var,
    from_=MIN_FEED, to=MAX_FEED,
    orient="horizontal", length=380,
    bg=PANEL_BG, fg=TEXT, troughcolor=DIM,
    highlightthickness=0, bd=0, font=FONT_SM, sliderlength=18,
    resolution=10,
    activebackground=ACCENT2,
    command=refresh_feed_label,
)
feed_slider.pack(side="left", padx=8, pady=8)

# Preset speed buttons
preset_frame = tk.Frame(speed_frame, bg=PANEL_BG)
preset_frame.pack(side="left", padx=6)

def make_preset(parent, label, value):
    def _set():
        feed_var.set(value)
        refresh_feed_label()
    b = tk.Button(parent, text=label, font=FONT_SM,
                  bg=BTN_BG, fg=ACCENT2,
                  activebackground=ACCENT2, activeforeground=BG,
                  relief="flat", bd=0, padx=8, pady=4,
                  cursor="hand2", command=_set)
    b.pack(side="left", padx=3)
    b.bind("<Enter>", lambda e: b.config(bg=ACCENT2, fg=BG))
    b.bind("<Leave>", lambda e: b.config(bg=BTN_BG, fg=ACCENT2))

make_preset(preset_frame, "SLOW\n100",   100)
make_preset(preset_frame, "MED\n500",    500)
make_preset(preset_frame, "FAST\n2000", 2000)
make_preset(preset_frame, "MAX\n5000",  5000)

tk.Frame(root, bg=DIM, height=1).pack(fill="x", padx=16, pady=4)

# ── Serial log pane ───────────────────────────────────────────────────
log_frame = tk.Frame(root, bg=BG)
log_frame.pack(fill="x", padx=16, pady=(0, 8))
tk.Label(log_frame, text="SERIAL LOG", font=FONT_SM,
         bg=BG, fg=LABEL_DIM).pack(anchor="w")
log_text = tk.Text(log_frame, height=5, bg=PANEL_BG, fg="#4ade80",
                   font=FONT_MONO, relief="flat", bd=0,
                   state="disabled")
log_text.pack(fill="x")

# ── Keyboard shortcuts ────────────────────────────────────────────────
key_map = {
    "Left":  ("X", -1), "Right": ("X", +1),
    "Up":    ("Z", +1), "Down":  ("Z", -1),
    "w": ("Y", +1), "s": ("Y", -1),
    "a": ("A", +1), "d": ("A", -1),
    "q": ("B", +1), "e": ("B", -1),
    "z": ("C", +1), "x": ("C", -1),
}

FEED_NUDGE = 50   # mm/min per keypress

def on_key(event):
    k = event.keysym
    if k == "h":
        home_all()
    elif k in key_map:
        axis, sign = key_map[k]
        jog(axis, sign)
    elif k in ("[", "minus"):          # [ or – → slower
        nudge_feed(-FEED_NUDGE)
    elif k in ("]", "equal"):          # ] or = → faster
        nudge_feed(+FEED_NUDGE)

root.bind("<Key>", on_key)
tk.Label(root,
         text="Keyboard: ←→ X   WS Y   ↑↓ Z   AD A   QE B   ZX C   H=home   [ / ] = speed ±50",
         font=FONT_SM, bg=BG, fg=LABEL_DIM).pack(pady=(0, 10))

# ── Cleanup ───────────────────────────────────────────────────────────
def on_close():
    builtins.print = builtins.__orig_print__
    ser.close()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_close)
refresh_labels()
root.mainloop()