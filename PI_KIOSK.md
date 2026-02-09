# Running Sambar HUD on Raspberry Pi (kiosk / fullscreen)

The app runs in **kiosk-style fullscreen**: frameless, no window chrome, fills the whole display (2560×720). It starts automatically after boot when you use the setup script.

---

## Quick start (recommended)

1. **Copy the project to your Pi** (e.g. clone or copy the `sambar_hud` folder).

2. **From the project directory, run the setup script:**
   ```bash
   cd sambar_hud
   chmod +x setup_kiosk.sh
   ./setup_kiosk.sh
   ```
   This installs system packages (X11, Openbox, unclutter, GStreamer, etc.), installs Python dependencies with `pip3 install --break-system-packages` (avoids the “externally-managed-environment” error on Pi OS), creates a systemd service, and configures display/autologin.

3. **Reboot:**
   ```bash
   sudo reboot
   ```
   After reboot, Sambar HUD starts automatically in fullscreen on `DISPLAY=:0`.

---

## Manual run (fullscreen)

To run once without enabling boot startup:

```bash
cd sambar_hud
python3 main.py
```

The window is already **fullscreen and frameless** (no title bar, no borders). It uses:

- `FramelessWindowHint`
- `WindowStaysOnTopHint`
- `WindowFullScreen`

So it always fills the screen. Make sure your Pi is in a desktop session (e.g. auto-login) so `DISPLAY=:0` exists.

---

## Kiosk behavior

- **Auto-start:** The systemd service `sambar-hud.service` starts the app after the graphical target (and a short delay so the display is ready).
- **Auto-login:** The setup script enables autologin for user `pi` so the desktop (and `:0`) is available without typing a password.
- **Screen blanking:** Disabled via `xset` in Openbox autostart (no screen saver).
- **Cursor:** Hidden when idle with `unclutter` (optional, in Openbox autostart).

---

## Service commands

| Action | Command |
|--------|--------|
| Start now | `sudo systemctl start sambar-hud.service` |
| Stop | `sudo systemctl stop sambar-hud.service` |
| Enable on boot | `sudo systemctl enable sambar-hud.service` |
| Disable on boot | `sudo systemctl disable sambar-hud.service` |
| View logs | `journalctl -u sambar-hud.service -f` |

---

## Display resolution

The setup script adds to `/boot/config.txt` (if not already set):

```
hdmi_group=2
hdmi_mode=87
hdmi_cvt=2560 720 60 6 0 0 0
gpu_mem=128
```

Adjust for your panel. For a different resolution, change `hdmi_cvt` and the `screen_width` / `screen_height` in `config.yaml`.

---

## If the app doesn’t start on boot

1. Check that the display is up: `echo $DISPLAY` in a desktop session should be `:0`.
2. Check the service: `sudo systemctl status sambar-hud.service`.
3. Check logs: `journalctl -u sambar-hud.service -n 50`.
4. If you see **“externally-managed-environment”**, the setup script uses `pip3 install --break-system-packages` so dependencies install anyway. If you ran setup before that change, run `./setup_kiosk.sh` again.
5. If you see **“metadata-generation-failed”**, the setup script now installs PyQt6 from apt and uses `requirements-pi.txt` for the rest. Re-run `./setup_kiosk.sh`.
6. If you see **UnicodeEncodeError** during pip install, the script now sets `LANG`, `LC_ALL`, and `PYTHONUTF8=1` so pip uses UTF-8. If it still fails, run manually: `export LANG=C.UTF-8 LC_ALL=C.UTF-8 PYTHONUTF8=1` then `pip3 install --break-system-packages -r requirements-pi.txt`.

---

## Disabling kiosk / going back to desktop

- Disable the service:  
  `sudo systemctl disable sambar-hud.service`  
- Reboot or stop the service:  
  `sudo systemctl stop sambar-hud.service`  
- You can still run the app manually with `python3 main.py` when you want fullscreen.
