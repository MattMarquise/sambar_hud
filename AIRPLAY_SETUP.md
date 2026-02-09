# AirPlay Setup Guide for Raspberry Pi

This guide explains how to set up AirPlay receiver on Raspberry Pi and display content only on the left side (entertainment panel) of your 2560x720 display.

## Overview

AirPlay allows your iPhone/iPad to stream audio and video to the Raspberry Pi. We'll use **Shairport-Sync** for audio and **UxPlay** or **RPiPlay** for video/mirroring, then configure it to display only on the left half of the screen.

## Option 1: UxPlay (Recommended - Supports Video & Mirroring)

UxPlay is a modern AirPlay receiver that supports both audio and video streaming, including screen mirroring.

### Installation

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y \
    build-essential \
    cmake \
    libavahi-compat-libdnssd-dev \
    libplist-dev \
    libssl-dev \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev \
    libpulse-dev \
    libasound2-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav

# Clone and build UxPlay
cd ~
git clone https://github.com/FD-/RPiPlay.git
cd RPiPlay
mkdir build && cd build
cmake ..
make -j4
sudo make install
```

### Configuration for Left-Side Display Only

Create a startup script that launches UxPlay with window positioning:

```bash
# Create script
sudo nano /usr/local/bin/start-airplay-left.sh
```

Add this content:

```bash
#!/bin/bash
# Start UxPlay/RPiPlay on left side of screen (x=0, width=1280, height=720)
# Kill any existing instance
pkill -f RPiPlay

# Start RPiPlay in windowed mode, positioned on left side
# -a: audio backend (alsa/pulse)
# -n: device name
# -b: background
# Window positioning will be handled by window manager or xdotool

RPiPlay -n "Sambar HUD AirPlay" -a alsa &
sleep 2

# Use xdotool to position window (install: sudo apt-get install xdotool)
WINDOW_ID=$(xdotool search --name "RPiPlay" | head -1)
if [ ! -z "$WINDOW_ID" ]; then
    xdotool windowmove $WINDOW_ID 0 0
    xdotool windowsize $WINDOW_ID 1280 720
    xdotool windowactivate $WINDOW_ID
fi
```

Make it executable:
```bash
sudo chmod +x /usr/local/bin/start-airplay-left.sh
```

## Option 2: Shairport-Sync + GStreamer (Audio + Video)

For more control, you can use Shairport-Sync for audio and a custom GStreamer pipeline for video.

### Installation

```bash
# Install Shairport-Sync
sudo apt-get install -y shairport-sync

# Install GStreamer plugins
sudo apt-get install -y \
    gstreamer1.0-tools \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav
```

### Configuration

Edit Shairport-Sync config:
```bash
sudo nano /etc/shairport-sync.conf
```

Set the device name:
```
general = {
    name = "Sambar HUD";
    ...
};
```

## Option 3: RPiPlay (Simpler, Video Only)

RPiPlay is specifically designed for Raspberry Pi and handles video streaming well.

### Installation

```bash
# Install dependencies
sudo apt-get install -y \
    cmake \
    libavahi-compat-libdnssd-dev \
    libplist-dev \
    libssl-dev \
    libavcodec-dev \
    libavformat-dev \
    libavutil-dev \
    libswscale-dev

# Clone and build
cd ~
git clone https://github.com/FD-/RPiPlay.git
cd RPiPlay
mkdir build && cd build
cmake ..
make -j4
sudo make install
```

## Display Configuration for Left Side Only

To display AirPlay content only on the left side (1280x720), you have several options:

### Method 1: Window Positioning (Recommended)

Use a window manager to position the AirPlay window:

```bash
# Install window positioning tools
sudo apt-get install -y wmctrl xdotool

# Create positioning script
cat > ~/position-airplay.sh << 'EOF'
#!/bin/bash
sleep 3
WINDOW_ID=$(wmctrl -l | grep -i "airplay\|rpiplay" | awk '{print $1}')
if [ ! -z "$WINDOW_ID" ]; then
    wmctrl -i -r $WINDOW_ID -e 0,0,0,1280,720
fi
EOF

chmod +x ~/position-airplay.sh
```

### Method 2: X11 Virtual Display

Create a virtual display for the left side:

```bash
# In your application startup, create a virtual display
Xvfb :1 -screen 0 1280x720x24 &
export DISPLAY=:1
# Then start AirPlay on this display
```

### Method 3: GStreamer Pipeline with Crop

If using GStreamer, you can crop the video:

```bash
gst-launch-1.0 airplaysrc ! \
    video/x-h264 ! \
    avdec_h264 ! \
    videocrop left=0 right=1280 top=0 bottom=0 ! \
    videoscale ! \
    video/x-raw,width=1280,height=720 ! \
    xvimagesink x=0 y=0
```

## Integration with Sambar HUD

Update `entertainment_panel.py` to launch AirPlay when selected:

```python
def start_airplay_receiver(self):
    """Start AirPlay receiver service"""
    try:
        # Start RPiPlay/UxPlay in background
        process = QProcess()
        process.start('/usr/local/bin/start-airplay-left.sh')
        self.processes['airplay'] = process
        
        # Position window after a delay
        QTimer.singleShot(3000, self.position_airplay_window)
    except Exception as e:
        print(f"AirPlay receiver setup error: {e}")

def position_airplay_window(self):
    """Position AirPlay window on left side"""
    try:
        import subprocess
        subprocess.Popen(['wmctrl', '-r', 'RPiPlay', '-e', '0,0,0,1280,720'])
    except:
        pass
```

## Network Configuration

Ensure your Raspberry Pi and iPhone are on the same WiFi network:

```bash
# Check WiFi connection
iwconfig

# Ensure mDNS/Bonjour is working
sudo apt-get install -y avahi-daemon
sudo systemctl enable avahi-daemon
sudo systemctl start avahi-daemon
```

## Testing

1. **Start AirPlay receiver**:
   ```bash
   RPiPlay -n "Sambar HUD"
   ```

2. **On iPhone**: 
   - Open Control Center
   - Tap Screen Mirroring
   - Select "Sambar HUD"

3. **Verify positioning**: The content should appear only on the left side

## Troubleshooting

### AirPlay not showing on iPhone
- Ensure both devices are on same WiFi
- Check firewall: `sudo ufw allow 5000/tcp`
- Restart avahi-daemon: `sudo systemctl restart avahi-daemon`

### Window not positioning correctly
- Install window manager: `sudo apt-get install openbox`
- Use `wmctrl -l` to list windows
- Manually position: `wmctrl -r "Window Name" -e 0,0,0,1280,720`

### Audio issues
- Check ALSA: `aplay -l`
- Test audio: `speaker-test -t sine -f 1000`
- Configure in `/etc/asound.conf` if needed

## Performance Optimization

For better performance on Raspberry Pi:

1. **Overclock** (optional):
   ```bash
   # Edit /boot/config.txt
   arm_freq=2000
   gpu_freq=750
   ```

2. **Increase GPU memory**:
   ```bash
   # Edit /boot/config.txt
   gpu_mem=128
   ```

3. **Use hardware acceleration**:
   - Ensure `gpu_mem` is set appropriately
   - Use `omxplayer` or hardware-accelerated GStreamer plugins

## Security Considerations

- AirPlay uses encryption by default
- Consider setting a password if your network is public
- UxPlay/RPiPlay don't require authentication by default (fine for private network)

## Resources

- RPiPlay: https://github.com/FD-/RPiPlay
- UxPlay: https://github.com/FD-/UxPlay
- Shairport-Sync: https://github.com/mikebrady/shairport-sync
