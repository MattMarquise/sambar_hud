#!/bin/bash
# Setup script for Raspberry Pi kiosk mode
# Run this script on your Raspberry Pi after installing the application

set -e

echo "Setting up Sambar HUD in kiosk mode..."

# Install required system packages
echo "Installing system dependencies..."
sudo apt-get update
sudo apt-get install -y \
    xorg \
    xserver-xorg-video-fbdev \
    xserver-xorg-input-evdev \
    x11-xserver-utils \
    xinit \
    openbox \
    unclutter \
    matchbox-window-manager \
    chromium \
    python3-pip \
    python3-dev \
    build-essential \
    python3-pyqt6 \
    python3-pyqt6.qtwebengine \
    python3-pygame \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    pulseaudio \
    alsa-utils \
    vlc \
    ffmpeg \
    wmctrl \
    xdotool

# Install Python dependencies (PyQt6 from apt above; UTF-8 avoids UnicodeEncodeError on tar extract)
echo "Installing remaining Python dependencies..."
export LANG=C.UTF-8
export LC_ALL=C.UTF-8
export PYTHONUTF8=1
pip3 install --break-system-packages -r requirements-pi.txt

# Create systemd service for auto-start (kiosk / fullscreen – single launcher)
echo "Creating systemd service..."
SAMBAR_DIR="$(pwd)"
sudo tee /etc/systemd/system/sambar-hud.service > /dev/null <<EOF
[Unit]
Description=Sambar HUD CarPlay and Entertainment System (kiosk fullscreen)
After=graphical.target
# Give display manager time to create :0
After=lightdm.service

[Service]
Type=simple
User=pi
Environment=DISPLAY=:0
Environment=XAUTHORITY=/home/pi/.Xauthority
Environment=LANG=C.UTF-8
Environment=LC_ALL=C.UTF-8
Environment=QT_QPA_PLATFORM=xcb
WorkingDirectory=$SAMBAR_DIR
# Short delay so DISPLAY=:0 is ready
ExecStartPre=/bin/sleep 3
ExecStart=/usr/bin/python3 $SAMBAR_DIR/main.py
Restart=always
RestartSec=10

[Install]
WantedBy=graphical.target
EOF

# Optional: openbox autostart only for screen blanking / cursor hide (app is started by systemd)
echo "Creating openbox autostart (screen blanking, cursor hide only)..."
mkdir -p ~/.config/openbox
cat > ~/.config/openbox/autostart <<EOF
# Disable screen blanking for kiosk
xset s off
xset -dpms
xset s noblank

# Hide cursor when idle
unclutter -idle 0.5 -root &
EOF

# .xinitrc only used if you start X with startx (e.g. no desktop)
if [ ! -f ~/.xinitrc ]; then
    echo "Creating .xinitrc..."
    cat > ~/.xinitrc <<EOF
#!/bin/sh
exec openbox-session
EOF
    chmod +x ~/.xinitrc
fi

# Enable auto-login so kiosk starts without user at keyboard (username: pi)
echo "Configuring auto-login..."
if [ -f /etc/lightdm/lightdm.conf ]; then
  if ! grep -q "^autologin-user=" /etc/lightdm/lightdm.conf 2>/dev/null; then
    sudo sed -i 's/#autologin-user=/autologin-user=pi/' /etc/lightdm/lightdm.conf 2>/dev/null || true
    sudo sed -i 's/#autologin-user-timeout=0/autologin-user-timeout=0/' /etc/lightdm/lightdm.conf 2>/dev/null || true
  fi
fi

# Enable systemd service
echo "Enabling Sambar HUD service..."
sudo systemctl enable sambar-hud.service

# Configure GPU memory split for better performance
echo "Configuring GPU memory..."
if ! grep -q "^gpu_mem=" /boot/config.txt; then
    echo "gpu_mem=128" | sudo tee -a /boot/config.txt
fi

# Set display resolution (adjust for your specific display)
echo "Configuring display resolution..."
if ! grep -q "^hdmi_group=" /boot/config.txt; then
    echo "hdmi_group=2" | sudo tee -a /boot/config.txt
    echo "hdmi_mode=87" | sudo tee -a /boot/config.txt
    echo "hdmi_cvt=2560 720 60 6 0 0 0" | sudo tee -a /boot/config.txt
fi

echo ""
echo "Setup complete!"
echo ""
echo "To start the application manually, run:"
echo "  python3 main.py"
echo ""
echo "To enable auto-start on boot:"
echo "  sudo systemctl enable sambar-hud.service"
echo ""
echo "To start the service now:"
echo "  sudo systemctl start sambar-hud.service"
echo ""
echo "After rebooting, the application will start automatically."
