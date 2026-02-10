#!/usr/bin/env python3
"""
Sambar HUD - Ultrawide CarPlay and Entertainment System
Designed for Raspberry Pi / Steam Deck with 2560x720 display.
Uses index.html as the full-screen HUD UI (Pi).
"""

import sys
import os
import glob
import platform

import subprocess
import threading
import time

try:
    from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget
    from PyQt6.QtCore import Qt, QUrl, QTimer
    from PyQt6.QtGui import QShortcut, QKeySequence, QGuiApplication
    from PyQt6.QtWebEngineWidgets import QWebEngineView
    from PyQt6.QtWebEngineCore import QWebEnginePage
except ImportError as e:
    print(f"Error importing PyQt6: {e}")
    print("Please install PyQt6 and PyQtWebEngine")
    sys.exit(1)

try:
    from config import Config
    from boot_splash import BootSplash
except ImportError as e:
    print(f"Error importing application modules: {e}")
    sys.exit(1)


def get_app_dir():
    """Directory containing main.py (and index.html, img/)."""
    return os.path.dirname(os.path.abspath(__file__))


def get_effective_screen_size(desired_width: int, desired_height: int, fit_to_screen: bool = True):
    """Return (width, height). If fit_to_screen is True, use full primary screen size (geometry); else use desired size (e.g. 2560x720 on Pi)."""
    if not fit_to_screen:
        return desired_width, desired_height
    app = QApplication.instance()
    if app is None:
        return desired_width, desired_height
    screen = app.primaryScreen()
    if screen is None:
        return desired_width, desired_height
    # Use geometry() (full screen) so the window fills the display; availableGeometry() would subtract taskbar/panels and make the window too small
    geom = screen.geometry()
    w = min(desired_width, geom.width())
    h = min(desired_height, geom.height())
    return w, h


# PIDs for Steam Link session (Xephyr + steamlink) so Home can close them
_xephyr_pid = None
_steamlink_pid = None

# PIDs for LIVI when run in Xephyr frame (so we can kill the frame on exit)
_livi_xephyr_pid = None
_livi_pid = None


def stop_steam_link_session() -> None:
    """Kill Steam Link and (if used) the Xephyr server so the left half shows the HUD again."""
    global _steamlink_pid, _xephyr_pid
    if _steamlink_pid is not None:
        try:
            os.kill(_steamlink_pid, 9)
        except (ProcessLookupError, PermissionError):
            pass
        _steamlink_pid = None
    if _xephyr_pid is not None:
        try:
            os.kill(_xephyr_pid, 9)
        except (ProcessLookupError, PermissionError):
            pass
        _xephyr_pid = None


def _get_steam_link_window_id() -> str | None:
    """Return wmctrl window id for Steam Link (or Xephyr Steam Link) window, or None."""
    try:
        out = subprocess.run(
            ["wmctrl", "-l"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if out.returncode != 0:
            return None
        for line in out.stdout.splitlines():
            # "0x... 0 desktop title" or "0x... 1 window title"
            parts = line.split(None, 2)
            if len(parts) < 3:
                continue
            wid, _desk, title = parts[0], parts[1], parts[2]
            if "Steam Link" in title or "steamlink" in title.lower() or "SambarSteamLink" in title:
                return wid
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


# Left-half geometry: position (0,0), size 1280x720 (overridden when positioning with explicit size)
_LEFT_HALF_GEOM = "0,0,0,1280,720"

# Sidebar width (px) so LIVI doesn't cover the right-edge sidebar
_LIVI_SIDEBAR_WIDTH = 88


def _get_livi_window_id() -> str | None:
    """Return wmctrl window id for LIVI (CarPlay) window, or None. Tries title and WM_CLASS."""
    # Try wmctrl -l (title only)
    try:
        out = subprocess.run(
            ["wmctrl", "-l"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if out.returncode == 0:
            for line in out.stdout.splitlines():
                parts = line.split(None, 2)
                if len(parts) < 3:
                    continue
                wid, _desk, title = parts[0], parts[1], parts[2]
                if "LIVI" in title or "livi" in title.lower() or "CarPlay" in title:
                    return wid
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    # Try wmctrl -l -x (WM_CLASS) for Electron/LIVI
    try:
        out = subprocess.run(
            ["wmctrl", "-l", "-x"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if out.returncode == 0:
            for line in out.stdout.splitlines():
                parts = line.split(None, 3)
                if len(parts) < 4:
                    continue
                wid = parts[0]
                rest = line.lower()
                if "livi" in rest or "carplay" in rest or "electron" in rest:
                    return wid
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def _livi_right_geom(effective_width: int, effective_height: int) -> str:
    """wmctrl -e format: gravity,x,y,width,height.
    LIVI width = distance from screen center to left edge of sidebar (so sidebar stays visible).
    LIVI height = full screen height (top to bottom).
    """
    center_x = effective_width // 2
    livi_width = center_x - _LIVI_SIDEBAR_WIDTH  # center to sidebar left edge
    livi_height = effective_height  # full screen height
    return f"0,{center_x},0,{livi_width},{livi_height}"


def _unmaximize_window(wmctrl_window_id: str) -> None:
    """Remove maximized/fullscreen so the window can be moved and resized (e.g. for LIVI/Steam Link)."""
    try:
        subprocess.run(
            ["wmctrl", "-i", "-r", wmctrl_window_id, "-b", "remove,maximized_vert,maximized_horz,fullscreen"],
            capture_output=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def _position_livi_window(wmctrl_window_id: str, effective_width: int, effective_height: int) -> None:
    """Move and resize LIVI to the right half, full height, leaving 88px for the sidebar."""
    geom = _livi_right_geom(effective_width, effective_height)
    try:
        subprocess.run(
            ["wmctrl", "-i", "-r", wmctrl_window_id, "-e", geom],
            capture_output=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def _position_livi_window_xdotool(effective_width: int, effective_height: int) -> bool:
    """Position LIVI using xdotool. Activate window first, then move and resize (full right-half height/width)."""
    x = effective_width // 2
    y = 0
    w = (effective_width // 2) - _LIVI_SIDEBAR_WIDTH
    h = effective_height
    for name in ["SambarLIVI", "LIVI", "CarPlay", "livi", "pi-carplay"]:
        try:
            out = subprocess.run(
                ["xdotool", "search", "--name", name],
                capture_output=True,
                text=True,
                timeout=2,
            )
            if out.returncode != 0 or not out.stdout.strip():
                continue
            wid = out.stdout.splitlines()[0].strip()
            subprocess.run(["xdotool", "windowactivate", "--sync", wid], capture_output=True, timeout=2)
            subprocess.run(["xdotool", "windowmove", "--sync", wid, str(x), str(y)], capture_output=True, timeout=2)
            subprocess.run(["xdotool", "windowsize", "--sync", wid, str(w), str(h)], capture_output=True, timeout=2)
            return True
        except (FileNotFoundError, subprocess.TimeoutExpired):
            continue
    return False


def _raise_livi_window(wmctrl_window_id: str) -> None:
    """Raise/activate LIVI window so it appears in front (not behind our HUD)."""
    _raise_window(wmctrl_window_id)


def _position_window_left(wmctrl_window_id: str) -> None:
    """Move and resize a window to the left half (0,0 1280x720) using wmctrl."""
    try:
        subprocess.run(
            ["wmctrl", "-i", "-r", wmctrl_window_id, "-e", _LEFT_HALF_GEOM],
            capture_output=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def _raise_window(wmctrl_window_id: str) -> None:
    """Raise a window by wmctrl id so it appears in front."""
    try:
        subprocess.run(
            ["wmctrl", "-i", "-a", wmctrl_window_id],
            capture_output=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def _set_overlay_window_flags(wmctrl_window_id: str) -> None:
    """Set overlay window to skip taskbar and pager so Pi desktop taskbar doesn't appear; try to remove decorations."""
    try:
        subprocess.run(
            ["wmctrl", "-i", "-r", wmctrl_window_id, "-b", "add,skip_taskbar,skip_pager"],
            capture_output=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def _remove_window_decorations(wmctrl_window_id: str) -> None:
    """Remove window title bar/decorations (borderless) via _MOTIF_WM_HINTS. Call early so geometry uses full height."""
    try:
        try:
            dec_id = str(int(wmctrl_window_id, 16))
        except ValueError:
            dec_id = wmctrl_window_id
        subprocess.run(
            ["xprop", "-id", dec_id, "-f", "_MOTIF_WM_HINTS", "32c", "-set", "_MOTIF_WM_HINTS", "2", "0", "0", "0", "0", "0", "0", "0", "0"],
            capture_output=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def _set_livi_stays_above(wmctrl_window_id: str) -> None:
    """Keep LIVI window above our HUD; remove title bar so it looks borderless."""
    try:
        subprocess.run(
            ["wmctrl", "-i", "-r", wmctrl_window_id, "-b", "add,above"],
            capture_output=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    _remove_window_decorations(wmctrl_window_id)


def _embed_livi_in_main_window(main_window: "MainWindow", wmctrl_window_id: str) -> bool:
    """
    Embed the LIVI X11 window into our main window (right half). Only works when Qt platform is xcb (X11).
    Returns True if embedding was done, False if skipped or failed.
    """
    if not getattr(main_window, "_livi_embed_holder", None):
        return False
    try:
        wid_int = int(wmctrl_window_id, 16)
    except (ValueError, TypeError):
        return False
    try:
        from PyQt6.QtGui import QWindow
        foreign = QWindow.fromWinId(wid_int)
        if not foreign:
            return False
        container = QWidget.createWindowContainer(foreign, main_window._livi_embed_holder)
        if not container:
            return False
        holder = main_window._livi_embed_holder
        container.setGeometry(0, 0, holder.width(), holder.height())
        main_window._livi_embed_holder.show()
        main_window._livi_embedded = True
        return True
    except Exception:
        return False


def _set_livi_vertical_maximize(wmctrl_window_id: str) -> None:
    """Ask WM to maximize LIVI vertically only so it fills top-to-bottom (full height)."""
    try:
        subprocess.run(
            ["wmctrl", "-i", "-r", wmctrl_window_id, "-b", "add,maximized_vert"],
            capture_output=True,
            timeout=2,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def launch_steam_link_left(app_dir: str) -> None:
    """Run Steam Link on the left half only (1280x720).
    Tries: (1) --windowed + wmctrl position, (2) Xephyr with 1280x720, (3) direct launch."""
    global _xephyr_pid, _steamlink_pid
    stop_steam_link_session()

    # ---- 1) Prefer windowed Steam Link: launch with --windowed then position to left half ----
    windowed_launchers = [
        # Flatpak (common on Steam Deck / modern distros)
        ["flatpak", "run", "--command=steamlink", "com.valvesoftware.SteamLink", "--windowed"],
        ["flatpak", "run", "com.valvesoftware.SteamLink", "--windowed"],
        # Apt/deb
        ["steamlink", "--windowed"],
        ["steam-link", "--windowed"],
    ]

    for cmd in windowed_launchers:
        try:
            p = subprocess.Popen(
                cmd,
                start_new_session=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            _steamlink_pid = p.pid
            break
        except FileNotFoundError:
            continue
    else:
        # No windowed launcher found; try Xephyr
        _launch_steam_link_via_xephyr()
        return

    def run():
        wid = None
        for _ in range(25):
            time.sleep(0.4)
            wid = _get_steam_link_window_id()
            if wid:
                break
        if wid:
            _set_overlay_window_flags(wid)
            _position_window_left(wid)
            time.sleep(0.5)
            _position_window_left(wid)
            for w in QApplication.topLevelWidgets():
                if type(w).__name__ == "MainWindow":
                    QTimer.singleShot(0, lambda mw=w: _set_overlay_mode(mw, True))
                    break
            _raise_window(wid)  # Bring Steam Link to front on the left half
            # Return focus to our app so Pi taskbar doesn't stay visible
            for w in QApplication.topLevelWidgets():
                if type(w).__name__ == "MainWindow":
                    QTimer.singleShot(200, lambda mw=w: (mw.raise_(), mw.activateWindow()))
                    break
            for _ in range(8):
                time.sleep(1.0)
                w = _get_steam_link_window_id()
                if w:
                    _position_window_left(w)
                    _set_overlay_window_flags(w)
                    _raise_window(w)
    threading.Thread(target=run, daemon=True).start()


def _launch_steam_link_via_xephyr() -> None:
    """Run Steam Link inside a 1280x720 Xephyr window placed on the left half (fallback)."""
    global _xephyr_pid, _steamlink_pid
    display_num = 99
    xephyr_display = f":{display_num}"
    title = "SambarSteamLink"

    try:
        proc = subprocess.Popen(
            [
                "Xephyr",
                xephyr_display,
                "-screen", "1280x720",
                "-title", title,
                "-br",
                "-ac",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        _xephyr_pid = proc.pid
    except FileNotFoundError:
        # No Xephyr; last resort: launch fullscreen
        for c in ["steamlink", "steam-link"]:
            try:
                p = subprocess.Popen(
                    [c],
                    start_new_session=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                _steamlink_pid = p.pid
                break
            except FileNotFoundError:
                continue
        return

    def run():
        global _steamlink_pid
        time.sleep(2)
        try:
            out = subprocess.run(
                ["wmctrl", "-l"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            for line in out.stdout.splitlines():
                if title in line:
                    wid = line.split(None, 1)[0]
                    _set_overlay_window_flags(wid)
                    _position_window_left(wid)
                    for w in QApplication.topLevelWidgets():
                        if type(w).__name__ == "MainWindow":
                            QTimer.singleShot(0, lambda mw=w: _set_overlay_mode(mw, True))
                            break
                    _raise_window(wid)
                    for w in QApplication.topLevelWidgets():
                        if type(w).__name__ == "MainWindow":
                            QTimer.singleShot(200, lambda mw=w: (mw.raise_(), mw.activateWindow()))
                            break
                    break
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        env = os.environ.copy()
        env["DISPLAY"] = xephyr_display
        for c in ["steamlink", "steam-link"]:
            try:
                p = subprocess.Popen(
                    [c],
                    env=env,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                _steamlink_pid = p.pid
                break
            except FileNotFoundError:
                continue

    threading.Thread(target=run, daemon=True).start()


def _kill_other_livi_processes() -> None:
    """Stop any already-running LIVI/carplay processes (e.g. from autostart) so we can run 4.1.2 only."""
    try:
        # Match LIVI AppImages and pi-carplay; avoid killing our own process
        subprocess.run(
            ["pkill", "-f", "LIVI.AppImage"],
            capture_output=True,
            timeout=2,
        )
        subprocess.run(
            ["pkill", "-f", "pi-carplay.*AppImage"],
            capture_output=True,
            timeout=2,
        )
        time.sleep(0.5)  # Let processes exit
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass


def _find_livi_appimage(config: "Config") -> str | None:
    """Resolve LIVI AppImage path: config carplay.livi_appimage_path, or ~/LIVI/ by arch (x86_64 vs arm64)."""
    path_cfg = config.get("carplay.livi_appimage_path") if config else None
    if path_cfg:
        exe = os.path.expanduser(path_cfg)
        if os.path.isfile(exe):
            return exe
    livi_dir = os.path.expanduser("~/LIVI")
    if not os.path.isdir(livi_dir):
        return None
    machine = platform.machine().lower()
    if machine in ("x86_64", "amd64"):
        pattern = os.path.join(livi_dir, "*x86_64*.AppImage")
    elif machine in ("aarch64", "arm64"):
        pattern = os.path.join(livi_dir, "*arm64*.AppImage")
    else:
        pattern = os.path.join(livi_dir, "*.AppImage")
    candidates = sorted(glob.glob(pattern), reverse=True)  # prefer newer by name
    for exe in candidates:
        if os.path.isfile(exe):
            return exe
    return None


def _launch_livi(app_dir: str, config: "Config") -> bool:
    """Launch LIVI (CarPlay) AppImage. Path from config or ~/LIVI/ (x86_64 or arm64). Returns True if launched."""
    exe = _find_livi_appimage(config)
    if not exe:
        return False
    _kill_other_livi_processes()
    env = os.environ.copy()
    # So LIVI's spawned pw-play (audio) is findable: our wrapper first, then /usr/bin, /bin
    scripts_dir = os.path.join(get_app_dir(), "scripts")
    path_parts = []
    if os.path.isdir(scripts_dir):
        path_parts.append(scripts_dir)
    for d in ("/usr/local/bin", "/usr/bin", "/bin"):
        if os.path.isdir(d):
            path_parts.append(d)
    path_parts.append(env.get("PATH", ""))
    env["PATH"] = os.pathsep.join(path_parts)
    # On Wayland, run LIVI under X11 (XWayland) so wmctrl can see and position its window
    livi_args = [exe, "--no-sandbox"]
    if os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland":
        livi_args.append("--ozone-platform=x11")
    try:
        subprocess.Popen(
            livi_args,
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            cwd=os.path.dirname(exe),
            env=env,
        )
        return True
    except (FileNotFoundError, PermissionError):
        return False


def _get_window_id_by_title(title_substring: str) -> str | None:
    """Return wmctrl window id (hex string) for the first window whose title contains the given string, or None."""
    try:
        out = subprocess.run(
            ["wmctrl", "-l"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if out.returncode != 0:
            return None
        for line in out.stdout.splitlines():
            parts = line.split(None, 2)
            if len(parts) < 3:
                continue
            wid, _desk, title = parts[0], parts[1], parts[2]
            if title_substring in title:
                return wid
        return None
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def _launch_livi_via_xephyr(
    app_dir: str, config: "Config", eff_w: int, eff_h: int, main_window: "MainWindow"
) -> bool:
    """
    Run LIVI inside a dedicated Xephyr 'frame' (nested X server) sized to the right half.
    We only position that one frame; LIVI runs full-size inside it so no separate window or menu placement.
    Returns True if Xephyr was started (LIVI is launched in the background thread).
    """
    global _livi_xephyr_pid, _livi_pid
    exe = _find_livi_appimage(config)
    if not exe:
        return False
    _kill_other_livi_processes()
    livi_w = (eff_w // 2) - _LIVI_SIDEBAR_WIDTH
    livi_h = eff_h
    display_num = 98
    xephyr_display = f":{display_num}"
    title = "SambarLIVI"
    try:
        proc = subprocess.Popen(
            [
                "Xephyr",
                xephyr_display,
                "-screen", f"{livi_w}x{livi_h}",
                "-title", title,
                "-br",
                "-ac",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        _livi_xephyr_pid = proc.pid
    except FileNotFoundError:
        return False

    def run():
        global _livi_pid
        time.sleep(2)
        wid = _get_window_id_by_title(title)
        if wid:
            _unmaximize_window(wid)
            time.sleep(0.1)
            _remove_window_decorations(wid)
            _position_livi_window(wid, eff_w, eff_h)
            _position_livi_window_xdotool(eff_w, eff_h)
            _set_overlay_window_flags(wid)
            _set_livi_stays_above(wid)
            _raise_livi_window(wid)
            for w in QApplication.topLevelWidgets():
                if type(w).__name__ == "MainWindow":
                    QTimer.singleShot(0, lambda mw=w: _set_overlay_mode(mw, True))
                    break
        env = os.environ.copy()
        scripts_dir = os.path.join(get_app_dir(), "scripts")
        path_parts = [scripts_dir] if os.path.isdir(scripts_dir) else []
        for d in ("/usr/local/bin", "/usr/bin", "/bin"):
            if os.path.isdir(d):
                path_parts.append(d)
        path_parts.append(env.get("PATH", ""))
        env["PATH"] = os.pathsep.join(path_parts)
        env["DISPLAY"] = xephyr_display
        # Force LIVI to use X11 (the Xephyr display); otherwise on Wayland it opens on the host and ignores DISPLAY
        env.pop("WAYLAND_DISPLAY", None)
        env.pop("XDG_SESSION_TYPE", None)
        livi_args = [exe, "--no-sandbox", "--ozone-platform=x11"]
        try:
            p = subprocess.Popen(
                livi_args,
                env=env,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                cwd=os.path.dirname(exe),
                start_new_session=True,
            )
            _livi_pid = p.pid
        except (FileNotFoundError, PermissionError):
            pass

    threading.Thread(target=run, daemon=True).start()
    return True


def _set_overlay_mode(main_window: "MainWindow", on: bool) -> None:
    """When on: remove StaysOnTop so Steam Link / CarPlay windows can display over our app. When off: restore StaysOnTop."""
    if main_window is None:
        return
    if on:
        main_window.setWindowFlags(Qt.WindowType.FramelessWindowHint)
    else:
        main_window.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
    main_window.show()


def launch_livi_and_apply_layout(main_window: "MainWindow") -> None:
    """Launch LIVI (CarPlay), position it over the right side (not covering the sidebar), full height, no title bar."""
    app = QApplication.instance()
    if app and app.primaryScreen():
        r = app.primaryScreen().geometry()
        eff_w, eff_h = r.width(), r.height()
    else:
        eff_w = getattr(main_window, "_effective_width", 2560)
        eff_h = getattr(main_window, "_effective_height", 720)

    # Prefer running LIVI inside a Xephyr frame (one window to position; LIVI fills the frame)
    use_xephyr = main_window.config.get("carplay.livi_use_xephyr", True)
    if use_xephyr and _launch_livi_via_xephyr(get_app_dir(), main_window.config, eff_w, eff_h, main_window):
        _set_overlay_mode(main_window, True)
        main_window.throttle_page(True)
        return

    if not _launch_livi(get_app_dir(), main_window.config):
        return
    _set_overlay_mode(main_window, True)
    main_window.throttle_page(True)  # Reduce our CPU use so CarPlay audio doesn't skip

    def run():
        use_embed = False
        gui = QGuiApplication.instance()
        if gui and gui.platformName() == "xcb":
            use_embed = True
        for _ in range(50):
            time.sleep(0.4)
            wid = _get_livi_window_id()
            if not wid:
                continue
            if use_embed:
                # Embed LIVI inside our window (X11 only): no WM positioning, full control of size and no title bar
                QTimer.singleShot(0, lambda mw=main_window, w=wid: _embed_livi_in_main_window(mw, w))
                break
            _unmaximize_window(wid)
            time.sleep(0.1)
            _remove_window_decorations(wid)
            _position_livi_window(wid, eff_w, eff_h)
            _position_livi_window_xdotool(eff_w, eff_h)
            _set_overlay_window_flags(wid)
            _set_livi_stays_above(wid)
            time.sleep(0.3)
            _position_livi_window(wid, eff_w, eff_h)
            _position_livi_window_xdotool(eff_w, eff_h)
            _raise_livi_window(wid)
            time.sleep(0.6)
            _position_livi_window(wid, eff_w, eff_h)
            _position_livi_window_xdotool(eff_w, eff_h)
            _remove_window_decorations(wid)
            _raise_livi_window(wid)
            time.sleep(1.0)
            w = _get_livi_window_id()
            if w:
                _position_livi_window(w, eff_w, eff_h)
                _position_livi_window_xdotool(eff_w, eff_h)
                _remove_window_decorations(w)
                _set_livi_stays_above(w)
                _raise_livi_window(w)
            time.sleep(1.0)
            w = _get_livi_window_id()
            if w:
                _position_livi_window(w, eff_w, eff_h)
                _position_livi_window_xdotool(eff_w, eff_h)
                _remove_window_decorations(w)
                _set_livi_stays_above(w)
                _raise_livi_window(w)
            for _ in range(6):
                time.sleep(1.0)
                w = _get_livi_window_id()
                if w:
                    _set_livi_stays_above(w)
                    _raise_livi_window(w)
            break
    threading.Thread(target=run, daemon=True).start()


class SambarWebPage(QWebEnginePage):
    """Intercepts sambar:// URLs: Steam Link, home, quit."""

    def __init__(self, profile, app_dir: str, parent=None):
        super().__init__(profile, parent)
        self._app_dir = app_dir

    def acceptNavigationRequest(self, url, nav_type, is_main_frame):
        if not is_main_frame:
            return True
        if url.scheme() == "sambar":
            host = url.host().lower()
            if host == "launch-steamlink":
                launch_steam_link_left(self._app_dir)
            elif host == "home":
                wid = _get_steam_link_window_id()
                if wid:
                    try:
                        subprocess.run(["wmctrl", "-i", "-c", wid], capture_output=True, timeout=2)
                    except (FileNotFoundError, subprocess.TimeoutExpired):
                        pass
                stop_steam_link_session()
                w = self.parent()
                mw = w.window() if w else None
                if mw is None or type(mw).__name__ != "MainWindow":
                    for tw in QApplication.topLevelWidgets():
                        if type(tw).__name__ == "MainWindow":
                            mw = tw
                            break
                if mw is not None and hasattr(mw, "_do_home"):
                    QTimer.singleShot(0, mw._do_home)
            elif host == "quit":
                app = QApplication.instance()
                if app:
                    app.quit()
            elif host == "light":
                pass  # Placeholder for wired/wifi RGB LED control
            return False
        return True


class MainWindow(QMainWindow):
    """Full-screen window showing index.html (HUD UI)."""

    def __init__(self):
        super().__init__()
        self.config = Config()
        self.hud_url = None
        self.view = None
        self._livi_embedded = False
        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )

        desired_width = self.config.get("screen_width", 2560)
        desired_height = self.config.get("screen_height", 720)
        fit_to_screen = self.config.get("fit_to_screen", False)
        self._effective_width, self._effective_height = get_effective_screen_size(
            desired_width, desired_height, fit_to_screen
        )
        self.setFixedSize(self._effective_width, self._effective_height)
        self.setGeometry(0, 0, self._effective_width, self._effective_height)

        app_dir = get_app_dir()
        index_path = os.path.join(app_dir, "index.html")

        if not os.path.isfile(index_path):
            from PyQt6.QtWidgets import QLabel
            err = QLabel(
                f"index.html not found at:\n{index_path}\n\n"
                "Run from the sambar_hud directory."
            )
            err.setStyleSheet("font-size: 18px; padding: 40px;")
            self.setCentralWidget(err)
            self.setWindowTitle("Sambar HUD - Error")
            return

        self.hud_url = QUrl.fromLocalFile(index_path)

        # Central container: full-size HUD view + right-half placeholder for embedded LIVI (X11 only)
        central = QWidget(self)
        central.setFixedSize(self._effective_width, self._effective_height)
        ew, eh = self._effective_width, self._effective_height

        from PyQt6.QtWebEngineCore import QWebEngineProfile
        profile = QWebEngineProfile.defaultProfile()
        page = SambarWebPage(profile, app_dir, self)
        self.view = QWebEngineView(central)
        self.view.setGeometry(0, 0, ew, eh)
        self.view.setPage(page)
        try:
            from PyQt6.QtWebEngineCore import QWebEngineSettings
            s = self.view.settings()
            s.setAttribute(QWebEngineSettings.WebAttribute.LocalStorageEnabled, False)
            s.setAttribute(QWebEngineSettings.WebAttribute.PluginsEnabled, False)
            s.setAttribute(QWebEngineSettings.WebAttribute.JavascriptCanOpenWindows, False)
            # Reduce CPU/memory so CarPlay (LIVI) runs smoother on Pi
            s.setAttribute(QWebEngineSettings.WebAttribute.DnsPrefetchEnabled, False)
            s.setAttribute(QWebEngineSettings.WebAttribute.AutoLoadIconsForPage, False)
            if hasattr(QWebEngineSettings.WebAttribute, "ScrollAnimatorEnabled"):
                s.setAttribute(QWebEngineSettings.WebAttribute.ScrollAnimatorEnabled, False)
        except Exception:
            pass
        self.view.setUrl(self.hud_url)

        self._livi_embed_holder = QWidget(central)
        self._livi_embed_holder.setGeometry(ew // 2, 0, ew // 2 - _LIVI_SIDEBAR_WIDTH, eh)
        self._livi_embed_holder.hide()

        self.setCentralWidget(central)
        self.setWindowTitle("Sambar HUD")
        self._apply_hud_zoom()
        self.view.loadFinished.connect(self._apply_hud_zoom)
        self._install_quit_shortcuts()

    def _apply_hud_zoom(self) -> None:
        """Scale the 2560x720 HUD to fit the window when fit_to_screen is True; else use 1:1 (no zoom)."""
        if self.view is None:
            return
        if not self.config.get("fit_to_screen", False):
            self.view.setZoomFactor(1.0)
            return
        zoom = min(
            self._effective_width / 2560.0,
            self._effective_height / 720.0,
            1.0,
        )
        self.view.setZoomFactor(zoom)

    def _install_quit_shortcuts(self) -> None:
        """Ctrl+Q and Escape quit the application."""
        app = QApplication.instance()
        if app is None:
            return
        quit_fn = app.quit
        QShortcut(QKeySequence.StandardKey.Quit, self).activated.connect(quit_fn)
        QShortcut(QKeySequence(Qt.Key.Key_Escape), self).activated.connect(quit_fn)

    def _keep_livi_on_top_if_shown(self) -> None:
        """When our window gets focus (e.g. user tapped left), keep LIVI on top on the right so it doesn't disappear."""
        if getattr(self, "_livi_embedded", False):
            return  # LIVI is embedded; no separate window to raise
        wid = _get_livi_window_id()
        if wid is None:
            return
        _set_livi_stays_above(wid)
        _raise_livi_window(wid)

    def focusInEvent(self, event):
        """Re-raise LIVI when our window gets focus so CarPlay stays visible on the right."""
        super().focusInEvent(event)
        QTimer.singleShot(50, self._keep_livi_on_top_if_shown)

    def restoreFullScreen(self) -> None:
        """Restore fullscreen when Steam/LIVI layout is closed. Re-add StaysOnTop so HUD stays on top."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setWindowState(Qt.WindowState.WindowNoState)
        self.setFixedSize(self._effective_width, self._effective_height)
        self.setGeometry(0, 0, self._effective_width, self._effective_height)
        self.showFullScreen()

    def _do_home(self) -> None:
        """Called after Home click (deferred): restore fullscreen with StaysOnTop, reload only if needed, raise."""
        _set_overlay_mode(self, False)
        self.throttle_page(False)  # Restore normal clock updates
        self.restoreFullScreen()
        # Only reload if we're not already showing the HUD (avoids transparent flash / layout glitch)
        if self.hud_url is not None and self.view is not None:
            try:
                if self.view.url() != self.hud_url:
                    self.view.setUrl(self.hud_url)
            except Exception:
                self.view.setUrl(self.hud_url)
        self.raise_()
        self.activateWindow()

    def go_home(self):
        if self.hud_url is not None and self.view is not None:
            self.view.setUrl(self.hud_url)

    def show_main(self):
        self.showFullScreen()
        self.raise_()
        self.activateWindow()

    def throttle_page(self, throttle: bool) -> None:
        """When True (CarPlay visible), slow clock updates to reduce CPU so LIVI gets more. When False, restore."""
        if self.view is None:
            return
        try:
            self.view.page().runJavaScript(
                "if (typeof window.setClockThrottle === 'function') window.setClockThrottle(" + ("true" if throttle else "false") + ");"
            )
        except Exception:
            pass


def main():
    os.environ.setdefault("LANG", "C.UTF-8")
    os.environ.setdefault("LC_ALL", "C.UTF-8")
    if "QT_QPA_PLATFORM" not in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "xcb"

    # Reduce WebEngine/Chromium load so CarPlay (LIVI) gets more CPU on Pi (less audio skipping)
    _argv = sys.argv
    if "--disable-background-networking" not in _argv:
        _argv += [
            "--disable-background-networking",
            "--disable-sync",
            "--no-first-run",
            "--renderer-process-limit=1",
            "--disable-smooth-scrolling",
            "--disable-threaded-scrolling",
        ]

    # Lower our process priority so LIVI and audio get more CPU
    try:
        os.nice(10)
    except (PermissionError, AttributeError, OSError):
        pass

    app = QApplication(_argv)
    app.setApplicationName("Sambar HUD")
    app.setApplicationVersion("1.0.0")

    config = Config()
    screen_width = config.get("screen_width", 2560)
    screen_height = config.get("screen_height", 720)
    fit_to_screen = config.get("fit_to_screen", False)
    splash_width, splash_height = get_effective_screen_size(screen_width, screen_height, fit_to_screen)
    boot_duration = 3000  # ms – 3s so bootintro.mp3 plays before fade to main

    main_window = MainWindow()
    main_window.hide()

    splash = BootSplash(
        width=splash_width,
        height=splash_height,
        duration_ms=boot_duration,
        parent=None,
    )
    splash.setWindowFlags(
        Qt.WindowType.FramelessWindowHint
        | Qt.WindowType.WindowStaysOnTopHint
    )
    splash.setGeometry(0, 0, splash_width, splash_height)

    def on_splash_finished():
        splash.close()
        main_window.show_main()
        # Auto-open LIVI (CarPlay) and position it on the right half, leaving 88px for sidebar
        if config.get("carplay.livi_auto_launch", True):
            QTimer.singleShot(800, lambda: launch_livi_and_apply_layout(main_window))

    splash.show_and_finish(on_splash_finished)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
