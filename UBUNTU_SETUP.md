# Sambar HUD – Setup on Ubuntu / Linux (non-Pi)

This guide covers installing everything needed to run Sambar HUD on an Ubuntu (or similar Debian-based) Linux machine.

---

## 1. Python 3

Install Python 3 and pip if not already present:

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv
```

Check version (3.8+ recommended):

```bash
python3 --version
```

---

## 2. System packages

These are required for the app and for window positioning (Steam Link / CarPlay overlays).

### Qt 6 and WebEngine (for the HUD UI)

PyQt6 and PyQtWebEngine need Qt6 and Chromium libraries. On Ubuntu you can either install the Qt/WebEngine stack via apt (recommended) or rely on pip and install only the runtime libs.

**Option A – Install Qt6 WebEngine from apt (recommended)**

```bash
sudo apt install -y \
  python3-pyqt6 \
  python3-pyqt6.qtwebengine
```

This pulls in Qt6, Chromium, and dependencies. Then use pip only for the other Python packages (see step 3).

**Option B – Use pip for PyQt6 and install only runtime libs**

If you prefer to install PyQt6 via pip (e.g. to match `requirements.txt` versions), install the runtime libraries Qt/WebEngine need:

```bash
sudo apt install -y \
  libxcb-cursor0 \
  libxcb-icccm4 \
  libxcb-image0 \
  libxcb-keysyms1 \
  libxcb-randr0 \
  libxcb-render-util0 \
  libxcb-xfixes0 \
  libxcb-xinerama0 \
  libxcomposite1 \
  libxcursor1 \
  libxdamage1 \
  libxfixes3 \
  libxi6 \
  libxkbcommon0 \
  libxkbcommon-x11-0 \
  libxrandr2 \
  libxrender1 \
  libxss1 \
  libxtst6 \
  libgl1-mesa-glx \
  libgbm1 \
  libnss3 \
  libnspr4 \
  libatk1.0-0 \
  libatk-bridge2.0-0 \
  libcups2 \
  libdrm2 \
  libxcomposite1 \
  libasound2
```

Then install PyQt6 and PyQtWebEngine with pip in step 3.

### Window positioning (Steam Link / CarPlay)

Required for placing Steam Link and LIVI/CarPlay windows:

```bash
sudo apt install -y wmctrl x11-utils
```

- **wmctrl** – move/resize/raise windows (used for Steam Link and LIVI).
- **x11-utils** – provides **xprop** (used to make overlay windows borderless and skip taskbar).

### Boot sound (optional)

For the splash screen to play `sound/bootintro.mp3`:

```bash
sudo apt install -y python3-pygame
```

If you skip this, the app still runs; the splash just won’t play sound.

---

## 3. Python packages

From the project directory:

```bash
cd /path/to/sambar_hud
```

**If you used Option A (PyQt6 from apt)** – install everything except PyQt6/PyQtWebEngine:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install pyyaml
# Optional: pip install pygame   (or use apt: python3-pygame)
```

If you use the venv, you still get PyQt6 from the system (Python in the venv can see system site-packages if created with `--system-site-packages`, or you can install only the non-Qt deps and run with `python3` that has `python3-pyqt6` and `python3-pyqt6.qtwebengine`). Simpler approach: **don’t use a venv** and install only the pip packages that aren’t provided by apt:

```bash
pip3 install --user pyyaml
# pygame: already installed via apt as python3-pygame
```

**If you used Option B (PyQt6 from pip)** – install full requirements:

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Note: `requirements.txt` includes PyQt6, PyQtWebEngine, pyusb, python-vlc, pyatv, etc. For a minimal run (HUD + Steam Link + CarPlay overlays), the **strict minimum** is:

- PyQt6, PyQtWebEngine (or from apt)
- PyYAML
- pygame (optional; for boot sound)

So a **minimal pip install** (if using apt for PyQt6) is:

```bash
pip3 install --user pyyaml
# Optional: pip3 install --user pygame   (or use apt python3-pygame)
```

---

## 4. Run the app

From the project directory, with a display available (physical or virtual, e.g. Xvfb):

```bash
cd /path/to/sambar_hud
python3 main.py
```

If you use a venv with PyQt6 from pip:

```bash
source venv/bin/activate
python3 main.py
```

---

## 5. Optional: LIVI (CarPlay) and Steam Link

- **LIVI (CarPlay)** – The app can launch LIVI 4.1.2 if the AppImage is at `~/LIVI/pi-carplay-4.1.2-arm64.AppImage`. On x86_64 Ubuntu you’d use the x86_64 LIVI AppImage and adjust the path in `main.py` (or add a config option) if you want CarPlay.
- **Steam Link** – Install from Ubuntu Software / Snap / Flatpak, or:

  ```bash
  sudo apt install -y steamlink
  # or install via Flatpak if you prefer
  ```

- **wmctrl** and **xprop** (from step 2) are required for positioning these windows over the HUD.

---

## 6. Summary checklist

| What              | How |
|-------------------|-----|
| Python 3          | `sudo apt install python3 python3-pip python3-venv` |
| Qt6 + WebEngine   | `sudo apt install python3-pyqt6 python3-pyqt6.qtwebengine` **or** pip install PyQt6 + PyQtWebEngine + system libs above |
| wmctrl            | `sudo apt install wmctrl` |
| xprop             | `sudo apt install x11-utils` |
| PyYAML            | `pip3 install pyyaml` |
| pygame (optional) | `sudo apt install python3-pygame` or `pip3 install pygame` |
| Run               | `cd sambar_hud && python3 main.py` |

---

## 7. Troubleshooting

- **“No module named 'PyQt6'”** – Install Qt from apt: `sudo apt install python3-pyqt6 python3-pyqt6.qtwebengine`, or enable your venv and run `pip install -r requirements.txt` (Option B).
- **“index.html not found”** – Run from the project root: `cd /path/to/sambar_hud`.
- **Steam Link / LIVI windows don’t move** – Ensure `wmctrl` and `xprop` are installed and that you’re in an X session (not pure Wayland without Xwayland), and that the window manager supports wmctrl.
- **Display not available** – For headless testing, use a virtual framebuffer: `Xvfb :99 -screen 0 2560x720x24 &` then `export DISPLAY=:99` before `python3 main.py`.
