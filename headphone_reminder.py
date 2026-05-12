"""
Headphone Break Reminder — System Tray App
Requirements: pip install plyer pystray pillow
Run: python headphone_reminder.py
"""

import threading
import time
import pystray
from PIL import Image, ImageDraw
from plyer import notification

# ── Default settings ──────────────────────────────────────────────
LISTEN_MINUTES = 60
BREAK_MINUTES  = 10

# ── State ─────────────────────────────────────────────────────────
state = {
    "listen_min": LISTEN_MINUTES,
    "break_min":  BREAK_MINUTES,
    "phase":      "idle",       # idle | listening | break
    "remaining":  0,
    "cycles":     0,
    "running":    False,
}

tray_icon = None
timer_thread = None
stop_event = threading.Event()


# ── Icon generator ────────────────────────────────────────────────
def make_icon(color="#4A90D9"):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    # headphone arc
    d.arc([8, 8, 56, 50], start=180, end=0, fill=color, width=6)
    # left ear cup
    d.ellipse([4, 36, 20, 54], fill=color)
    # right ear cup
    d.ellipse([44, 36, 60, 54], fill=color)
    return img


def get_icon_color():
    if state["phase"] == "listening":
        return "#4A90D9"   # blue  — listening
    elif state["phase"] == "break":
        return "#E8A838"   # amber — break
    return "#888888"       # gray  — idle


# ── Notification helper ───────────────────────────────────────────
def notify(title, message):
    try:
        notification.notify(
            title=title,
            message=message,
            app_name="Headphone Reminder",
            timeout=8,
        )
    except Exception as e:
        print(f"Notification error: {e}")


# ── Core timer loop ───────────────────────────────────────────────
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

            if state["running"] and not stop_event.is_set():
                state["phase"] = "break"
                state["cycles"] += 1
                notify(
                    "🎧 Time for a break!",
                    f"You've been listening for {state['listen_min']} min.\n"
                    f"Rest your ears for {state['break_min']} min."
                )
                update_tray_icon()

        elif state["phase"] == "break":
            state["remaining"] = state["break_min"] * 60
            while state["remaining"] > 0 and state["running"] and not stop_event.is_set():
                time.sleep(1)
                state["remaining"] -= 1
                update_tray_tooltip()

            if state["running"] and not stop_event.is_set():
                state["phase"] = "listening"
                notify(
                    "✅ Break over — headphones back on!",
                    f"Enjoy your next {state['listen_min']} min session."
                )
                update_tray_icon()

        else:
            time.sleep(0.5)


def update_tray_tooltip():
    if tray_icon is None:
        return
    mins = state["remaining"] // 60
    secs = state["remaining"] % 60
    phase_label = "Listening" if state["phase"] == "listening" else "Break"
    tray_icon.title = f"Headphone Reminder — {phase_label}: {mins:02d}:{secs:02d}"


def update_tray_icon():
    if tray_icon is None:
        return
    tray_icon.icon = make_icon(get_icon_color())
    update_tray_tooltip()


# ── Tray menu actions ─────────────────────────────────────────────
def action_start(icon, item):
    if state["running"]:
        return
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
    state["running"] = False
    state["phase"]   = "idle"
    state["remaining"] = 0
    state["cycles"]  = 0
    tray_icon.icon   = make_icon(get_icon_color())
    tray_icon.title  = "Headphone Reminder — Idle"


def action_quit(icon, item):
    stop_event.set()
    state["running"] = False
    icon.stop()


# ── Listen duration setters ───────────────────────────────────────
def set_listen(mins):
    def handler(icon, item):
        state["listen_min"] = mins
        notify("Listen duration updated", f"Will remind every {mins} min.")
    return handler


def set_break(mins):
    def handler(icon, item):
        state["break_min"] = mins
        notify("Break duration updated", f"Break length set to {mins} min.")
    return handler


# ── Status item (dynamic label) ───────────────────────────────────
def status_text(item):
    if not state["running"]:
        return "Status: idle"
    mins = state["remaining"] // 60
    secs = state["remaining"] % 60
    label = "Listening" if state["phase"] == "listening" else "Break"
    return f"Status: {label} — {mins:02d}:{secs:02d} left  (cycle #{state['cycles']})"


# ── Build tray menu ───────────────────────────────────────────────
def build_menu():
    return pystray.Menu(
        pystray.MenuItem(status_text, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("▶  Start",  action_start),
        pystray.MenuItem("⏸  Pause / Resume", action_pause),
        pystray.MenuItem("⏹  Stop",   action_stop),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Listen duration", pystray.Menu(
            pystray.MenuItem("30 min", set_listen(30)),
            pystray.MenuItem("45 min", set_listen(45)),
            pystray.MenuItem("60 min", set_listen(60)),
            pystray.MenuItem("90 min", set_listen(90)),
        )),
        pystray.MenuItem("Break duration", pystray.Menu(
            pystray.MenuItem("5 min",  set_break(5)),
            pystray.MenuItem("10 min", set_break(10)),
            pystray.MenuItem("15 min", set_break(15)),
            pystray.MenuItem("20 min", set_break(20)),
        )),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", action_quit),
    )


# ── Entry point ───────────────────────────────────────────────────
def main():
    global tray_icon, timer_thread

    timer_thread = threading.Thread(target=timer_loop, daemon=True)
    timer_thread.start()

    tray_icon = pystray.Icon(
        name="headphone_reminder",
        icon=make_icon(get_icon_color()),
        title="Headphone Reminder — Idle",
        menu=build_menu(),
    )
    tray_icon.run()


if __name__ == "__main__":
    main()
