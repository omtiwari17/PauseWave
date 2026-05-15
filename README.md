# 🎧 Headphone Break Reminder

A lightweight Windows system tray app that reminds you to take regular breaks from headphones — helping protect your hearing over time.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Why?

Prolonged headphone use at high volumes can cause hearing fatigue and long-term damage. The WHO recommends limiting personal audio device use to **60 minutes per session** followed by a break. This app sits quietly in your taskbar and handles the reminders for you — and unlike a notification you can swipe away, it pops up a window you actually have to acknowledge.

---

## Features

- 🖥️ Lives in your **system tray** no window clutter
- 🔔 Native **Windows toast notifications** at each phase change
- 🪟 **Blocking popup window** when break time hits can't be dismissed with X, must acknowledge it
- 🖥️ **Multi-monitor support** choose which monitor the popup appears on from settings
- 🎛️ **Settings window** with sliders for listen and break duration
- 🔵 Blue tray icon while listening, 🟡 amber during break
- ⏸️ Pause / Resume support
- 🔁 Auto-cycles between listening and break phases indefinitely
- 🔒 Closing the settings window keeps the app running in the tray (Discord-style)

---

## Installation

**1. Clone the repo**
```bash
git clone https://github.com/omtiwari17/PauseWave.git
cd headphone-break-reminder
```

**2. Install dependencies**
```bash
pip install -r requirements.txt
```

**3. Run**
```bash
python headphone_reminder.py
```

A headphone icon will appear in your system tray (bottom-right corner). Right-click it to open settings and start your session.

---

## Usage

### System tray (right-click menu)

| Action | How |
|---|---|
| Open settings | Right-click → ⚙ Open Settings |
| Start session | Right-click → ▶ Start |
| Pause / Resume | Right-click → ⏸ Pause / Resume |
| Stop & reset | Right-click → ⏹ Stop |
| Quit the app | Right-click → Quit |

### Settings window

| Setting | Description |
|---|---|
| Listen duration | Slider: how long you listen before a break (10–120 min) |
| Break duration | Slider: how long your break lasts (2–30 min) |
| Popup monitor | Radio buttons: pick which monitor the break popup appears on |
| Start / Pause / Stop | Control the session without going to the tray |

### Break popup

When your listening time is up, a popup window appears on your chosen monitor centered on screen. The X button is disabled — you must click **"✓ Got it, taking a break"** to dismiss it. The popup also shows a live countdown of your remaining break time and closes automatically when the break ends.

---

## Auto-start with Windows

To launch the app automatically on boot:

1. Press `Win + R`, type `shell:startup`, hit Enter
2. Place a shortcut to `headphone_reminder.py` in that folder

---

## Requirements

- Windows 10 or later
- Python 3.8+
- See `requirements.txt`

---

## Project Structure

```
headphone-break-reminder/
├── headphone_reminder.py   # Main app
├── requirements.txt        # Dependencies
├── .gitignore
├── LICENSE
└── README.md
```

---

## Contributing

Pull requests are welcome! Some ideas for future improvements:

- Sound alarm during break popup
- Session history and statistics
- Auto-start with Windows toggle from settings
- Custom duration input (beyond slider range)
- Dark/light theme toggle

---

## License

MIT — see [LICENSE](LICENSE)