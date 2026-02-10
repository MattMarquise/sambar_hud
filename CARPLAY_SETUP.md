# CarPlay Setup Guide for Sambar HUD

This guide covers two ways to get CarPlay on the right half of the Sambar HUD display.

---

## Quick setup: LIVI on Linux PC (x86_64) or Raspberry Pi

1. **Install LIVI** (detailed steps)
   - Open the LIVI releases page in your browser: **https://github.com/f-io/LIVI/releases**
   - Pick a release (e.g. the latest, such as **v5.1.0** or **v4.1.3**). Click the release tag to open it.
   - Scroll to the **Assets** section and expand it if it’s collapsed.
   - Download the AppImage that matches your machine:
     - **Linux PC (Intel/AMD 64-bit)**: choose the file whose name contains **x86_64** and ends in **.AppImage** (e.g. `LIVI-5.1.0-x86_64.AppImage` or `pi-carplay-4.1.3-x86_64.AppImage`).
     - **Raspberry Pi (64-bit)**: choose the file whose name contains **arm64** and ends in **.AppImage** (e.g. `LIVI-5.1.0-arm64.AppImage` or `pi-carplay-4.1.3-arm64.AppImage`).
   - After the download finishes, create the LIVI folder and put the AppImage there. In a terminal:
     ```bash
     mkdir -p ~/LIVI
     ```
     Then move the downloaded file into `~/LIVI`. For example, if it’s in your Downloads folder and named `LIVI-5.1.0-x86_64.AppImage`:
     ```bash
     mv ~/Downloads/LIVI-5.1.0-x86_64.AppImage ~/LIVI/
     ```
     (Use the actual filename you downloaded.)
   - Make the AppImage executable:
     ```bash
     chmod +x ~/LIVI/*.AppImage
     ```
   - Check that Sambar HUD will find it:
     ```bash
     ls ~/LIVI/
     ```
     You should see one (or more) `.AppImage` files. Sambar HUD looks for any file in `~/LIVI/` whose name contains `x86_64` (on a PC) or `arm64` (on a Pi) and ends with `.AppImage`.

2. **USB dongle (Carlinkit CPC200-CCPA or CPC200-CCPW)**
   - Plug the dongle into the PC or Pi. For non-Pi Linux, add udev rules so your user can access it:
     ```bash
     sudo bash -c 'echo "SUBSYSTEM==\"usb\", ATTR{idVendor}==\"1314\", ATTR{idProduct}==\"152*\", MODE=\"0660\", OWNER=\"${SUDO_USER:-$USER}\"" > /etc/udev/rules.d/99-LIVI.rules; udevadm control --reload-rules; udevadm trigger'
     ```
     Then unplug and replug the dongle (or reboot).

3. **Window positioning (optional)**
   - Sambar HUD will auto-launch LIVI and place its window on the right half (leaving the sidebar visible). Install `wmctrl` (and optionally `xdotool`) if the window doesn't move:
     ```bash
     sudo apt install wmctrl xdotool
     ```
   - **On Wayland (e.g. KDE/Plasma):** wmctrl and xdotool only work with X11 windows. Sambar HUD automatically launches LIVI with `--ozone-platform=x11` so it runs under XWayland; then wmctrl can see and position the LIVI window. If positioning still fails, try logging in with an **X11 session** (e.g. "Plasma (X11)") instead of Wayland.

4. **Config (optional)**
   - In `config.yaml`, under `carplay`, you can set:
     - `livi_appimage_path: ~/LIVI/pi-carplay-4.1.2-x86_64.AppImage` (or your exact path) if auto-detect doesn't find it.
     - `livi_auto_launch: false` to disable auto-starting LIVI on boot.

Sambar HUD will look for an AppImage in `~/LIVI/` by architecture (x86_64 on PC, arm64 on Pi). No need to edit code.

### Dongle connects then disconnects (Linux PC)

If the Carlinkit works on the Pi but on a Linux PC it **connects, then disconnects, then briefly reconnects**, the usual cause is **USB autosuspend**: the kernel suspends the USB port to save power, and the dongle drops off. Try the following.

**1. Disable USB autosuspend for the Carlinkit (recommended)**

With the dongle plugged in, find its USB device path:

```bash
lsusb
```

Look for a line with `1314` and `152x` (e.g. `Bus 001 Device 005: ID 1314:1521 ...`). Note the bus and device numbers. Then:

```bash
# Replace 1-5 with your bus-device (e.g. 1-5 for Bus 001 Device 005)
echo -1 | sudo tee /sys/bus/usb/devices/1-5/power/autosuspend_delay_ms
echo on | sudo tee /sys/bus/usb/devices/1-5/power/control
```

Use the actual bus–port path. You can list paths for vendor 1314:

```bash
for d in /sys/bus/usb/devices/*/idVendor; do
  [ "$(cat "$d")" = "1314" ] && echo "${d%/idVendor}"
done
```

Then run the two `echo` commands above with that path (e.g. `1-5` or `3-2.1`). **This lasts until you unplug the dongle or reboot.** If it fixes the problem, make it persistent (see below).

**2. Make it persistent (udev)**

Create a udev rule that disables autosuspend whenever the Carlinkit is connected:

```bash
sudo tee /etc/udev/rules.d/99-carlinkit-no-suspend.rules << 'EOF'
# Disable USB autosuspend for Carlinkit (LIVI) so it doesn't connect/disconnect
ACTION=="add", SUBSYSTEM=="usb", ATTR{idVendor}=="1314", ATTR{idProduct}=="152*", TEST=="power/control", ATTR{power/control}="on"
EOF
sudo udevadm control --reload-rules
sudo udevadm trigger
```

Unplug and replug the dongle, then start LIVI again.

**3. Only USB 3.0 ports (no USB 2.0)**

If you only have USB 3 (blue) ports and the dongle still loops after the steps above, try:

- **Kernel boot parameter** — Disable USB autosuspend for all devices at boot. Edit the kernel command line (e.g. in GRUB: `sudo nano /etc/default/grub`, add `usbcore.autosuspend=-1` to `GRUB_CMDLINE_LINUX_DEFAULT`, then `sudo update-grub` and reboot). Example:
  ```text
  GRUB_CMDLINE_LINUX_DEFAULT="quiet splash usbcore.autosuspend=-1"
  ```
  After reboot, plug in the dongle and try LIVI again.

- **USB 2.0 hub (hardware)** — Many Carlinkit-style dongles are more stable behind a **USB 2.0 hub**. Plug a cheap USB 2.0 hub into your PC, then plug the dongle into the hub. That gives the dongle a USB 2.0 bus and often stops connect/disconnect loops when USB 3 alone doesn't.

**4. Other checks**

- **Power**: If the port is underpowered, use a **powered USB hub**.
- **Cable**: Try a different USB cable (some charge-only cables cause flaky data).

### Do I need to install anything for the Carlinkit?

You don't need a special driver. The dongle is a standard USB device; LIVI uses **libusb** (usually already on the system). Install the following so the dongle is detected and your user can access it:

**Required**

- **udev rules** — So your user can open the device without root. Run once:
  ```bash
  sudo bash -c 'echo "SUBSYSTEM==\"usb\", ATTR{idVendor}==\"1314\", ATTR{idProduct}==\"152*\", MODE=\"0660\", OWNER=\"${SUDO_USER:-$USER}\"" > /etc/udev/rules.d/99-LIVI.rules; udevadm control --reload-rules; udevadm trigger'
  ```
  Then unplug and replug the dongle (or reboot).

**Useful for debugging**

- **usbutils** — For `lsusb` to see the dongle:
  ```bash
  sudo apt install usbutils
  lsusb
  ```
  Look for `ID 1314:152x`.

**Optional (only if LIVI reports missing libs)**

- **libusb-1.0-0** — Often already installed. If LIVI errors mention libusb:
  ```bash
  sudo apt install libusb-1.0-0
  ```

If the dongle appears in `lsusb` but LIVI still doesn't see it, check that your user is the one set in the udev rule (`OWNER`) and that you replugged the dongle after adding the rule.

### "[AudioOutput] spawn pw-play ENOENT" (no audio, LIVI can't find pw-play)

If LIVI logs **spawn pw-play ENOENT**, it means the system can't find the `pw-play` command (used for CarPlay audio). On the **Linux PC where LIVI runs** (not the Pi), do this once:

1. **Install PipeWire tools** (if needed):
   ```bash
   sudo apt install pipewire-audio pipewire-bin
   ```

2. **Install the pw-play wrapper** (so LIVI's audio process can run and older PipeWire gets the right format):
   ```bash
   cd ~/Downloads/sambar_hud   # or your sambar_hud path
   sudo scripts/install_pw-play_wrapper.sh
   ```

3. **Confirm** `/usr/bin/pw-play` exists and is executable:
   ```bash
   ls -la /usr/bin/pw-play
   which pw-play
   ```

4. **Start LIVI from Sambar HUD** (so it gets the right PATH), then try CarPlay again. If you still have no sound, follow the steps in **No audio from LIVI** below (pavucontrol, default sink, LIVI audio settings).

On Raspberry Pi this often works without the wrapper because the Pi's PipeWire may support `--raw` or the environment is different.

### No audio from LIVI (other sounds work)

If CarPlay/LIVI has no sound but your speaker works for the browser and other apps, LIVI is likely using a different audio output or the stream is muted.

**1. Check LIVI's audio output**

- Open **LIVI** and go to its **Settings** (gear icon or similar).
- Look for **Audio** / **Output device** / **Playback** and select your speaker or **Default** (system default output). Save and try playing music or maps voice in CarPlay again.

**2. Route LIVI to your speaker (PulseAudio/PipeWire)**

While something is playing in CarPlay (e.g. music), open the system volume or **PulseAudio Volume Control**:

```bash
# Install if needed (Ubuntu/Debian)
sudo apt install pavucontrol
pavucontrol
```

- In **pavucontrol**, open the **Playback** tab. Find **LIVI** or **Chrome** / **Electron** (LIVI is Electron-based).  
- Ensure its volume is up and the **output device** is your speaker, not a dummy or another sink.  
- In the **Output Devices** tab, set your speaker as the default (green checkmark) if it isn’t already.

**3. Set default sink from the command line**

List sinks and set the default to your speaker:

```bash
pactl info
pactl list short sinks
pactl set-default-sink <sink_name_or_index>
```

Example: `pactl set-default-sink alsa_output.usb-...` or the index number. Then restart LIVI and try again.

**4. PipeWire (if you use it)**

LIVI is designed to work with PipeWire. If you're on PipeWire (e.g. Ubuntu 22.04+ with pipewire-pulse):

```bash
# See default and available devices
pw-cli info all
```

Ensure the default playback node is your speaker. Restart LIVI after changing the default.

**5. Restart LIVI**

After changing the default output or LIVI’s audio setting, fully quit LIVI and start it again (or restart Sambar HUD so it relaunches LIVI).

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
