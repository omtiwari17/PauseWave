# 🎧 Headphone Break Reminder

A lightweight Windows system tray app that reminds you to take regular breaks from headphones — helping protect your hearing over time.

![Python](https://img.shields.io/badge/Python-3.8+-blue?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?logo=windows)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Why?

Prolonged headphone use at high volumes can cause hearing fatigue and long-term damage. The WHO recommends limiting personal audio device use to **60 minutes per session** followed by a break. This app sits quietly in your taskbar and handles the reminders for you.

---

## Features

- 🖥️ Lives in your **system tray** no window clutter
- 🔔 Native **Windows toast notifications** at each phase change
- 🔵 Blue icon while listening, 🟡 amber during break
- ⚙️ Configurable listen and break durations via right-click menu
- ⏸️ Pause / Resume support
- 🔁 Auto-cycles between listening and break phases

---

## Installation

**1. Clone the repo**
```bash
git clone https://github.com/omtiwari17/PauseWave
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

A headphone icon will appear in your system tray (bottom-right corner). Right-click it to start.

---

## Usage

| Action | How |
|---|---|
| Start session | Right-click tray icon → Start |
| Pause / Resume | Right-click → Pause / Resume |
| Stop & reset | Right-click → Stop |
| Change listen duration | Right-click → Listen duration |
| Change break duration | Right-click → Break duration |
| Quit the app | Right-click → Quit |

---

## Auto-start with Windows

To launch the app automatically on boot:

1. Press `Win + R` and type `shell:startup`, hit Enter
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

- Custom duration input (not just preset values)
- Sound alert option in addition to notifications
- Session history / statistics
- Auto-start toggle from the tray menu

---

## License

MIT — see [LICENSE](LICENSE)