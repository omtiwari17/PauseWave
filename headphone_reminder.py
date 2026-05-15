"""
Headphone Break Reminder — System Tray App with Settings Window
Requirements: pip install winotify pystray pillow screeninfo
Run: python headphone_reminder.py
"""

import threading
import time
import tkinter as tk
from tkinter import ttk
import pystray
from PIL import Image, ImageDraw
from winotify import Notification, audio
from screeninfo import get_monitors

# ── State ─────────────────────────────────────────────────────────
state = {
    "listen_min":    60,
    "break_min":     10,
    "phase":         "idle",   # idle | listening | break
    "remaining":     0,
    "cycles":        0,
    "running":       False,
    "target_monitor": 0,       # index into get_monitors() list
}

tray_icon    = None
stop_event   = threading.Event()
settings_win = None
popup_win    = None


# ── Icon ──────────────────────────────────────────────────────────
def make_icon(color="#4A90D9"):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.arc([8, 8, 56, 50], start=180, end=0, fill=color, width=6)
    d.ellipse([4, 36, 20, 54], fill=color)
    d.ellipse([44, 36, 60, 54], fill=color)
    return img

def get_icon_color():
    if state["phase"] == "listening": return "#4A90D9"
    if state["phase"] == "break":     return "#E8A838"
    return "#888888"


# ── Notifications ─────────────────────────────────────────────────
def notify(title, message):
    try:
        toast = Notification(app_id="Headphone Reminder", title=title,
                             msg=message, duration="short")
        toast.set_audio(audio.Default, loop=False)
        toast.show()
    except Exception as e:
        print(f"Notification error: {e}")


# ── Monitor helpers ───────────────────────────────────────────────
def get_monitor_list():
    try:
        return get_monitors()
    except Exception:
        return []

def get_target_monitor():
    monitors = get_monitor_list()
    idx = state["target_monitor"]
    if not monitors:
        return None
    idx = min(idx, len(monitors) - 1)
    return monitors[idx]


# ── Break popup ───────────────────────────────────────────────────
def show_break_popup():
    global popup_win

    # if popup already open, just bring it forward
    if popup_win and popup_win.winfo_exists():
        popup_win.lift()
        popup_win.focus_force()
        return

    mon = get_target_monitor()

    popup = tk.Toplevel()
    popup.title("Take a Break!")
    popup.configure(bg="#1e1e2e")
    popup.resizable(False, False)
    popup.attributes("-topmost", True)      # always on top
    popup.attributes("-toolwindow", True)   # no taskbar entry
    popup.overrideredirect(False)           # keep title bar so user can't dismiss easily

    # prevent closing with X — must use the button
    popup.protocol("WM_DELETE_WINDOW", lambda: None)

    W, H = 400, 360

    # position on target monitor
    if mon:
        x = mon.x + (mon.width  - W) // 2
        y = mon.y + (mon.height - H) // 2
    else:
        popup.update_idletasks()
        sw = popup.winfo_screenwidth()
        sh = popup.winfo_screenheight()
        x = (sw - W) // 2
        y = (sh - H) // 2

    popup.geometry(f"{W}x{H}+{x}+{y}")

    BG     = "#1e1e2e"
    CARD   = "#2a2a3e"
    ACCENT = "#E8A838"
    TEXT   = "#e0e0f0"
    SUBTEXT= "#888aaa"

    tk.Label(popup, text="🎧", font=("Segoe UI", 40), bg=BG).pack(pady=(30, 4))
    tk.Label(popup, text="Time for a break!", font=("Segoe UI", 16, "bold"),
             bg=BG, fg=TEXT).pack()
    tk.Label(popup, text=f"Rest your ears for {state['break_min']} minutes.\nStep away from the headphones.",
             font=("Segoe UI", 10), bg=BG, fg=SUBTEXT, justify="center").pack(pady=8)

    # countdown inside popup
    countdown_var = tk.StringVar(value=f"{state['break_min']}:00")
    tk.Label(popup, textvariable=countdown_var, font=("Segoe UI", 22, "bold"),
             bg=BG, fg=ACCENT).pack(pady=4)

    def tick_popup():
        if not popup.winfo_exists():
            return
        rem = state["remaining"]
        m, s = divmod(rem, 60)
        countdown_var.set(f"{m:02d}:{s:02d}")
        popup.after(1000, tick_popup)

    tick_popup()

    def on_acknowledge():
        global popup_win
        popup_win = None
        popup.destroy()

    tk.Button(popup, text="✓  Got it, taking a break",
              font=("Segoe UI", 11, "bold"), bg=ACCENT, fg="#1e1e2e",
              relief="flat", cursor="hand2", pady=8,
              command=on_acknowledge).pack(fill="x", padx=40, pady=(12, 6))

    tk.Label(popup, text="This window will close automatically when break ends.",
             font=("Segoe UI", 8), bg=BG, fg=SUBTEXT).pack(pady=(0, 10))

    popup_win = popup
    popup.focus_force()


def close_break_popup():
    global popup_win
    if popup_win and popup_win.winfo_exists():
        popup_win.destroy()
        popup_win = None


# ── Timer loop ────────────────────────────────────────────────────
def timer_loop():
    while not stop_event.is_set():
        if not state["running"]:
            time.sleep(0.5)
            continue

        if state["phase"] == "listening":
            state["remaining"] = state["listen_min"] * 60
            while state["remaining"] > 0 and state["running"] and not stop_event.is_set():
                time.sleep(1)
                state["remaining"] -= 1
                update_tray_tooltip()
                refresh_settings_timer()

            if state["running"] and not stop_event.is_set():
                state["phase"] = "break"
                state["cycles"] += 1
                notify("🎧 Time for a break!",
                       f"Listened {state['listen_min']} min — rest {state['break_min']} min.")
                update_tray_icon()
                # show blocking popup on chosen monitor
                if settings_win:
                    settings_win.after(0, show_break_popup)

        elif state["phase"] == "break":
            state["remaining"] = state["break_min"] * 60
            while state["remaining"] > 0 and state["running"] and not stop_event.is_set():
                time.sleep(1)
                state["remaining"] -= 1
                update_tray_tooltip()
                refresh_settings_timer()

            if state["running"] and not stop_event.is_set():
                state["phase"] = "listening"
                notify("✅ Break over — headphones back on!",
                       f"Enjoy your next {state['listen_min']} min session.")
                update_tray_icon()
                if settings_win:
                    settings_win.after(0, close_break_popup)

        else:
            time.sleep(0.5)


def update_tray_tooltip():
    if tray_icon is None: return
    m, s = divmod(state["remaining"], 60)
    label = "Listening" if state["phase"] == "listening" else "Break"
    tray_icon.title = f"Headphone Reminder — {label}: {m:02d}:{s:02d}"

def update_tray_icon():
    if tray_icon is None: return
    tray_icon.icon = make_icon(get_icon_color())
    update_tray_tooltip()


# ── Settings window ───────────────────────────────────────────────
def build_settings_window():
    global settings_win

    win = tk.Tk()
    win.title("Headphone Reminder — Settings")
    win.geometry("380x520")
    win.resizable(False, False)
    win.configure(bg="#1e1e2e")
    win.protocol("WM_DELETE_WINDOW", win.withdraw)

    BG      = "#1e1e2e"
    CARD    = "#2a2a3e"
    ACCENT  = "#4A90D9"
    TEXT    = "#e0e0f0"
    SUBTEXT = "#888aaa"
    FONT    = ("Segoe UI", 10)
    BOLD    = ("Segoe UI", 10, "bold")

    # Header
    hdr = tk.Frame(win, bg=BG)
    hdr.pack(fill="x", padx=20, pady=(20, 4))
    tk.Label(hdr, text="🎧  Headphone Reminder", font=("Segoe UI", 14, "bold"),
             bg=BG, fg=TEXT).pack(anchor="w")
    tk.Label(hdr, text="Protect your hearing with regular breaks",
             font=("Segoe UI", 9), bg=BG, fg=SUBTEXT).pack(anchor="w")

    ttk.Separator(win).pack(fill="x", padx=20, pady=10)

    # Status card
    status_card = tk.Frame(win, bg=CARD)
    status_card.pack(fill="x", padx=20, pady=(0, 10))

    status_label = tk.Label(status_card, text="Status: Idle", font=BOLD,
                            bg=CARD, fg=ACCENT)
    status_label.pack(anchor="w", padx=14, pady=(10, 0))

    timer_label = tk.Label(status_card, text="—", font=("Segoe UI", 28, "bold"),
                           bg=CARD, fg=TEXT)
    timer_label.pack(anchor="w", padx=14)

    cycle_label = tk.Label(status_card, text="Cycles completed: 0",
                           font=("Segoe UI", 9), bg=CARD, fg=SUBTEXT)
    cycle_label.pack(anchor="w", padx=14, pady=(0, 10))

    # Sliders
    slider_frame = tk.Frame(win, bg=BG)
    slider_frame.pack(fill="x", padx=20, pady=(0, 6))

    listen_row = tk.Frame(slider_frame, bg=BG)
    listen_row.pack(fill="x", pady=4)
    listen_lbl = tk.Label(listen_row, text=f"Listen: {state['listen_min']} min",
                          font=FONT, bg=BG, fg=TEXT, width=18, anchor="w")
    listen_lbl.pack(side="left")
    listen_var = tk.IntVar(value=state["listen_min"])
    def on_listen(val):
        v = int(float(val))
        state["listen_min"] = v
        listen_lbl.config(text=f"Listen: {v} min")
    tk.Scale(listen_row, from_=10, to=120, orient="horizontal",
             variable=listen_var, command=on_listen,
             bg=BG, fg=TEXT, troughcolor=CARD, highlightthickness=0,
             activebackground=ACCENT, length=180, showvalue=False).pack(side="left")

    break_row = tk.Frame(slider_frame, bg=BG)
    break_row.pack(fill="x", pady=4)
    break_lbl = tk.Label(break_row, text=f"Break:  {state['break_min']} min",
                         font=FONT, bg=BG, fg=TEXT, width=18, anchor="w")
    break_lbl.pack(side="left")
    break_var = tk.IntVar(value=state["break_min"])
    def on_break(val):
        v = int(float(val))
        state["break_min"] = v
        break_lbl.config(text=f"Break:  {v} min")
    tk.Scale(break_row, from_=2, to=30, orient="horizontal",
             variable=break_var, command=on_break,
             bg=BG, fg=TEXT, troughcolor=CARD, highlightthickness=0,
             activebackground=ACCENT, length=180, showvalue=False).pack(side="left")

    ttk.Separator(win).pack(fill="x", padx=20, pady=8)

    # ── Monitor picker ────────────────────────────────────────────
    mon_frame = tk.Frame(win, bg=BG)
    mon_frame.pack(fill="x", padx=20, pady=(0, 8))

    tk.Label(mon_frame, text="Popup monitor", font=BOLD,
             bg=BG, fg=TEXT).pack(anchor="w", pady=(0, 6))

    monitors = get_monitor_list()
    mon_var = tk.IntVar(value=state["target_monitor"])

    if monitors:
        btn_row = tk.Frame(mon_frame, bg=BG)
        btn_row.pack(fill="x")
        for i, m in enumerate(monitors):
            label = f"Monitor {i+1}  ({m.width}×{m.height})"
            if m.is_primary:
                label += "  [primary]"
            rb = tk.Radiobutton(
                btn_row, text=label, variable=mon_var, value=i,
                bg=BG, fg=TEXT, selectcolor=CARD, activebackground=BG,
                activeforeground=TEXT, font=FONT,
                command=lambda idx=i: state.update({"target_monitor": idx})
            )
            rb.pack(anchor="w", pady=1)
    else:
        tk.Label(mon_frame, text="Could not detect monitors.",
                 font=FONT, bg=BG, fg=SUBTEXT).pack(anchor="w")

    ttk.Separator(win).pack(fill="x", padx=20, pady=8)

    # Buttons
    btn_frame = tk.Frame(win, bg=BG)
    btn_frame.pack(fill="x", padx=20, pady=4)
    BTN = dict(font=BOLD, relief="flat", cursor="hand2", pady=6)

    def btn_start():
        if state["running"]: return
        state["running"] = True
        state["phase"]   = "listening"
        state["cycles"]  = 0
        update_tray_icon()
        notify("Headphone Reminder started",
               f"You'll be reminded every {state['listen_min']} min.")
        refresh_ui()

    def btn_pause():
        state["running"] = not state["running"]
        if not state["running"]:
            if tray_icon: tray_icon.title = "Headphone Reminder — Paused"
        else:
            update_tray_tooltip()
        refresh_ui()

    def btn_stop():
        state["running"]   = False
        state["phase"]     = "idle"
        state["remaining"] = 0
        state["cycles"]    = 0
        if tray_icon:
            tray_icon.icon  = make_icon(get_icon_color())
            tray_icon.title = "Headphone Reminder — Idle"
        close_break_popup()
        refresh_ui()

    start_btn = tk.Button(btn_frame, text="▶  Start",  bg=ACCENT, fg="white",
                          command=btn_start, **BTN)
    start_btn.pack(side="left", expand=True, fill="x", padx=(0, 4))

    pause_btn = tk.Button(btn_frame, text="⏸  Pause", bg=CARD, fg=TEXT,
                          command=btn_pause, **BTN)
    pause_btn.pack(side="left", expand=True, fill="x", padx=4)

    stop_btn  = tk.Button(btn_frame, text="⏹  Stop",  bg="#c0392b", fg="white",
                          command=btn_stop, **BTN)
    stop_btn.pack(side="left", expand=True, fill="x", padx=(4, 0))

    tk.Label(win, text="Closing this window keeps the app running in the system tray.",
             font=("Segoe UI", 8), bg=BG, fg=SUBTEXT).pack(pady=(10, 4))

    # Live refresh
    def refresh_ui():
        phase = state["phase"].capitalize() if state["phase"] != "idle" else "Idle"
        if not state["running"] and state["phase"] not in ("idle",):
            phase = "Paused"
        status_label.config(text=f"Status: {phase}")
        if state["remaining"] > 0:
            m, s = divmod(state["remaining"], 60)
            timer_label.config(text=f"{m:02d}:{s:02d}")
        else:
            timer_label.config(text="—")
        cycle_label.config(text=f"Cycles completed: {state['cycles']}")
        start_btn.config(state="disabled" if state["running"] else "normal")
        pause_btn.config(text="▶  Resume" if (not state["running"] and state["phase"] != "idle")
                         else "⏸  Pause")

    win._refresh_ui = refresh_ui
    win.withdraw()
    settings_win = win
    return win


def refresh_settings_timer():
    if settings_win and settings_win.winfo_exists():
        try:
            settings_win.after(0, settings_win._refresh_ui)
        except Exception:
            pass


# ── Tray ──────────────────────────────────────────────────────────
def action_open_settings(icon, item):
    if settings_win:
        settings_win.after(0, _show_settings)

def _show_settings():
    settings_win.deiconify()
    settings_win.lift()
    settings_win.focus_force()

def action_start(icon, item):
    if state["running"]: return
    state["running"] = True
    state["phase"]   = "listening"
    state["cycles"]  = 0
    update_tray_icon()
    notify("Headphone Reminder started",
           f"You'll be reminded every {state['listen_min']} min.")

def action_pause(icon, item):
    state["running"] = not state["running"]
    if not state["running"]:
        tray_icon.title = "Headphone Reminder — Paused"
    else:
        update_tray_tooltip()

def action_stop(icon, item):
    state["running"]   = False
    state["phase"]     = "idle"
    state["remaining"] = 0
    state["cycles"]    = 0
    tray_icon.icon  = make_icon(get_icon_color())
    tray_icon.title = "Headphone Reminder — Idle"
    if settings_win:
        settings_win.after(0, close_break_popup)

def action_quit(icon, item):
    stop_event.set()
    state["running"] = False
    if settings_win:
        settings_win.after(0, settings_win.destroy)
    icon.stop()

def status_text(item):
    if not state["running"]: return "Status: Idle"
    m, s = divmod(state["remaining"], 60)
    label = "Listening" if state["phase"] == "listening" else "Break"
    return f"Status: {label} — {m:02d}:{s:02d}  (#{state['cycles']})"

def build_menu():
    return pystray.Menu(
        pystray.MenuItem(status_text, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("⚙  Open Settings", action_open_settings),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("▶  Start",          action_start),
        pystray.MenuItem("⏸  Pause / Resume", action_pause),
        pystray.MenuItem("⏹  Stop",           action_stop),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit",              action_quit),
    )


# ── Entry point ───────────────────────────────────────────────────
def main():
    global tray_icon

    win = build_settings_window()
    threading.Thread(target=timer_loop, daemon=True).start()

    tray_icon = pystray.Icon(
        name="headphone_reminder",
        icon=make_icon(get_icon_color()),
        title="Headphone Reminder — Idle",
        menu=build_menu(),
    )
    threading.Thread(target=tray_icon.run, daemon=True).start()

    win.mainloop()


if __name__ == "__main__":
    main()