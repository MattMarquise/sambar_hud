# Steam Link Setup Guide

Tapping the **Steam icon** on the left panel launches Steam Link and keeps its window **only on the left half** of the screen (1280×720 at 0,0). CarPlay stays on the right.

## 1. Install Steam Link on the Pi

You must install the Steam Link app on the Raspberry Pi. For example:

```bash
sudo apt-get update
sudo apt-get install steamlink
```

If your Pi OS doesn’t list `steamlink`, install it from **Add / Remove Software** (search for “Steam Link”) or from the [Steam Link for Raspberry Pi](https://github.com/ValveSoftware/SteamLink) project.

## 2. Window positioning (wmctrl)

The HUD uses **wmctrl** to move the Steam Link window to the left half and remove fullscreen. The kiosk setup script installs it; if you didn’t run that:

```bash
sudo apt-get install wmctrl xdotool
```

## Window Positioning Tools

For automatic window positioning, install:
```bash
sudo apt-get install wmctrl xdotool
```

## Configuration

### Method 1: Using Helper Script (Recommended)

The `scripts/start_steam_link_left.sh` script automatically:
- Launches Steam Link
- Positions it on the left side (x=0, y=0, 1280x720)
- Handles window management

Make sure it's executable:
```bash
chmod +x scripts/start_steam_link_left.sh
```

### Method 2: Manual Configuration

If Steam Link launches in fullscreen mode, you may need to:

1. **Configure Steam Link for windowed mode**:
   - Launch Steam Link
   - Go to Settings
   - Disable fullscreen mode if available

2. **Use window manager**:
   ```bash
   # Find Steam Link window
   wmctrl -l
   
   # Position window (replace WINDOW_ID)
   wmctrl -i -r WINDOW_ID -e 0,0,0,1280,720
   ```

### Method 3: X11 Configuration

You can configure X11 to restrict Steam Link to a specific display area:

```bash
# Create a virtual display for left side
Xephyr -screen 1280x720 :1 &
DISPLAY=:1 steamlink &
```

## Troubleshooting

### Steam Link opens in fullscreen
- Install `wmctrl`: `sudo apt-get install wmctrl`
- The helper script will automatically position it
- Or manually: `wmctrl -r "Steam Link" -e 0,0,0,1280,720`

### Window not found
- Try different window names: "Steam Link", "steamlink", "Steam"
- List windows: `wmctrl -l` or `xdotool search --name ""`

### Performance issues
- Ensure GPU memory is sufficient: `gpu_mem=128` in `/boot/config.txt`
- Close other applications
- Use wired network connection for best streaming quality

## Integration with Sambar HUD

The `entertainment_panel.py` automatically:
- Detects Steam Link installation
- Launches it when Steam is selected
- Positions window on left side
- Shows overlay controls for exiting

## Overlay Controls

When Steam Link (or any app) is running, an overlay appears at the bottom with:
- **Exit App**: Closes the current app and returns to menu
- **Back to Menu**: Returns to app selection
- **Hide/Show**: Toggles overlay visibility

The overlay can be hidden to avoid blocking content, but can be shown again by clicking the "Show" button.
