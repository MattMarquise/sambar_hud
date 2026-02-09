# CarPlay Setup Guide for Sambar HUD

This guide covers two ways to get CarPlay on the right half of the Sambar HUD display.

---

## Quick setup: LIVI on Linux PC (x86_64) or Raspberry Pi

1. **Install LIVI**
   - **Releases**: [LIVI on GitHub](https://github.com/f-io/LIVI/releases) — download the AppImage for your system:
     - **Linux PC**: `pi-carplay-*-x86_64.AppImage` (or `LIVI-*-x86_64.AppImage`)
     - **Raspberry Pi**: `pi-carplay-*-arm64.AppImage`
   - Create a folder and put the AppImage there:
     ```bash
     mkdir -p ~/LIVI
     # Move the downloaded AppImage into ~/LIVI/ (e.g. pi-carplay-4.1.2-x86_64.AppImage)
     chmod +x ~/LIVI/*.AppImage
     ```

2. **USB dongle (Carlinkit CPC200-CCPA or CPC200-CCPW)**
   - Plug the dongle into the PC or Pi. For non-Pi Linux, add udev rules so your user can access it:
     ```bash
     sudo bash -c 'echo "SUBSYSTEM==\"usb\", ATTR{idVendor}==\"1314\", ATTR{idProduct}==\"152*\", MODE=\"0660\", OWNER=\"${SUDO_USER:-$USER}\"" > /etc/udev/rules.d/99-LIVI.rules; udevadm control --reload-rules; udevadm trigger'
     ```
     Then unplug and replug the dongle (or reboot).

3. **Window positioning (optional)**
   - Sambar HUD will auto-launch LIVI and place its window on the right half (leaving the sidebar visible). Install `wmctrl` if the window doesn't move:
     ```bash
     sudo apt install wmctrl
     ```

4. **Config (optional)**
   - In `config.yaml`, under `carplay`, you can set:
     - `livi_appimage_path: ~/LIVI/pi-carplay-4.1.2-x86_64.AppImage` (or your exact path) if auto-detect doesn't find it.
     - `livi_auto_launch: false` to disable auto-starting LIVI on boot.

Sambar HUD will look for an AppImage in `~/LIVI/` by architecture (x86_64 on PC, arm64 on Pi). No need to edit code.

---

## If your Carlinkit dongle requires “wired CarPlay” on the Pi

Many Carlinkit dongles only enable **wireless** CarPlay after the vehicle computer (your Raspberry Pi) is already running a **wired CarPlay host**. The dongle plugs into the Pi via USB; the Pi runs the CarPlay stack and displays the UI; the iPhone then connects to the dongle wirelessly.

To get that working, install a CarPlay host on the Pi first:

### Option 1: LIVI (formerly Pi-CarPlay, recommended)

- **Site**: [Pi-CarPlay](https://f-io.github.io/pi-carplay/) · **GitHub**: [LIVI](https://github.com/f-io/LIVI) (project moved here)
- **Supported USB adapters**: Carlinkit **CPC200-CCPA** (wireless/wired) and **CPC200-CCPW** (wired) only. Other models (e.g. **CCPM "mini"**, U2W, 2.0, 3.0) may use different USB IDs and are **not** listed as supported.
- **What it does**: Standalone CarPlay (and Android Auto) head unit for Linux. The dongle connects to the Pi over USB; LIVI shows the CarPlay UI on your display.
- **Install**: Use LIVI's [setup-pi.sh](https://raw.githubusercontent.com/f-io/LIVI/main/setup-pi.sh) on Raspberry Pi (it installs udev rules for the dongle). Pre-built AppImages: [LIVI Releases](https://github.com/f-io/LIVI/releases).

**Flow**: Pi runs LIVI → dongle is wired to Pi → iPhone connects to the dongle (wireless or USB, depending on dongle). Once LIVI is working, you can run Sambar HUD and use the right half for LIVI’s window and the left half for Steam Link.

#### LIVI: Dongle not detected

If LIVI runs but does **not** see your Carlinkit dongle:

1. **Check supported model** — LIVI supports **CPC200-CCPA** and **CPC200-CCPW** only. "Carlinkit mini" is often **CPC200-CCPM**, a different (wired-only) variant **not** in LIVI's supported list. Check the label or product page for CCPA/CCPW; if you have CCPM or another series, LIVI may not support it (open an issue at [f-io/LIVI/issues](https://github.com/f-io/LIVI/issues)).

2. **Confirm the Pi sees the dongle** — With the dongle plugged in, run `lsusb`. Look for **Vendor ID 1314** and **Product ID 152x** (e.g. 1520, 1521). If it doesn't appear, try another USB port (prefer powered), unplug/replug, or another cable.

3. **Install udev rules** — LIVI needs udev rules so your user can access the USB dongle. On Pi, re-run LIVI's installer (it writes `/etc/udev/rules.d/52-carplay.rules`): `curl -LO https://raw.githubusercontent.com/f-io/LIVI/main/setup-pi.sh && chmod +x setup-pi.sh && ./setup-pi.sh`. On other Linux (x86_64), add a rule manually:
   ```bash
   sudo bash -c 'echo "SUBSYSTEM==\"usb\", ATTR{idVendor}==\"1314\", ATTR{idProduct}==\"152*\", MODE=\"0660\", OWNER=\"${SUDO_USER:-$USER}\"" > /etc/udev/rules.d/99-LIVI.rules; udevadm control --reload-rules; udevadm trigger'
   ```
   Then **unplug and replug** the dongle (or reboot) and start LIVI again.

4. **If your dongle has different USB IDs** — If `lsusb` shows vendor 1314 but a product ID other than 152*, LIVI may not recognize it. Open an issue on the LIVI repo with your `lsusb` output to ask if that device can be added.

### Option 2: FastCarPlay

- **GitHub**: [FastCarPlay](https://github.com/niellun/FastCarPlay) – Linux CarPlay/Android Auto receiver for Carlinkit dongles.
- Use this if your dongle is supported and you prefer this stack; integration with Sambar HUD is similar (run FastCarPlay, then show its window or feed on the right half).

### Integrating with Sambar HUD

- Run Pi-CarPlay (or FastCarPlay) so CarPlay works on the Pi.
- Either:
  - Run Sambar HUD and **position the Pi-CarPlay window** on the right half (1280,0 1280x720) with `wmctrl`/`xdotool`, or
  - Use a **video capture** path: if the CarPlay app outputs to a virtual/video device, point Sambar HUD’s CarPlay feed at that device (see “Option A/B” below).

---

## If your Carlinkit outputs video (HDMI or USB video)

Some setups use a Carlinkit (or similar) that **outputs a video stream** (HDMI or USB UVC). The Pi does **not** run a CarPlay stack; it only displays that video. Sambar HUD can capture that feed and show it on the right half.

### How It Works

1. **Carlinkit** – Handles wireless CarPlay (iPhone ↔ dongle).
2. **Video feed** – Carlinkit outputs video (HDMI or USB video).
3. **Sambar HUD** – Captures that feed and shows it only on the right half of the app.

No CarPlay host is required on the Pi in this case; we only display the Carlinkit output.

## Hardware Setup

### Option A: Carlinkit with HDMI out (common)

- **Carlinkit** – Wireless CarPlay, HDMI output.
- **USB HDMI capture dongle** – HDMI in, USB out (plugged into the Pi).
- **Wiring**: Carlinkit HDMI → capture dongle → Pi USB.

The Pi sees the capture dongle as a video device (e.g. `/dev/video0`). Sambar HUD reads that device and shows it on the right half.

### Option B: Carlinkit with USB video out

- If the Carlinkit sends video over USB (UVC), plug it into the Pi.
- It will appear as `/dev/video0` (or another `/dev/videoX`).
- Sambar HUD uses that device for the right-half feed.

## Software Requirements

- **ffmpeg** (for `ffplay`) and/or **GStreamer** – used to display the video feed.
- **wmctrl** and/or **xdotool** – used to keep the video window on the right half (optional but recommended).

On Raspberry Pi OS:

```bash
sudo apt-get update
sudo apt-get install -y ffmpeg gstreamer1.0-tools gstreamer1.0-plugins-base \
  gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly \
  wmctrl xdotool
```

## Configuration

### Video device

By default the app uses `/dev/video0`. If your Carlinkit feed is on another device (e.g. `/dev/video1`), set:

```bash
export CARPLAY_VIDEO_DEVICE=/dev/video1
```

before starting Sambar HUD, or set this in your environment / launch script.

### In the app

- **Show CarPlay** – Starts reading the video device and shows it on the right half. The video window is moved to position (1280, 0) with size 1280x720.
- **Hide CarPlay** – Stops the feed and returns the right panel to the idle message.

## Usage

1. Connect hardware:
   - **Option A**: Carlinkit HDMI → USB HDMI capture → Pi USB.
   - **Option B**: Carlinkit USB (video) → Pi USB.
2. Connect iPhone to the Carlinkit (wireless CarPlay as per dongle instructions).
3. Start Sambar HUD.
4. Click **Show CarPlay** on the right panel.
5. The Carlinkit feed appears only on the right half of the screen.

## Troubleshooting

### "No video device"

- Run: `ls /dev/video*`  
  If nothing appears, the capture dongle or Carlinkit USB video is not detected.
- Try another USB port.
- For HDMI capture dongles, ensure HDMI is connected before boot or replug after boot.

### Wrong device

- List devices: `v4l2-ctl --list-devices`.
- Set the correct one: `export CARPLAY_VIDEO_DEVICE=/dev/videoX`.

### Feed not fullscreen on the right half

- Install window positioning tools:  
  `sudo apt-get install wmctrl xdotool`
- The app will try to move the video window to (1280, 0) and 1280x720.

### No picture / black screen

- Confirm the Carlinkit is on and the iPhone is connected (wireless CarPlay).
- Test the device from the command line:
  - GStreamer:  
    `gst-launch-1.0 v4l2src device=/dev/video0 ! videoconvert ! xvimagesink`
  - ffplay:  
    `ffplay -f v4l2 /dev/video0`
- If that works, the same device will be used for the right-half feed in Sambar HUD.

## Summary

- **Dongle needs “wired CarPlay” on the Pi** → Install **Pi-CarPlay** (or FastCarPlay), then position its window or feed on the right half.
- **Dongle outputs video only** → Use HDMI/USB capture and Sambar HUD shows that feed on the **right half** of the screen.
