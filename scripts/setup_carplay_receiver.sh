#!/bin/bash
# Setup script for CarPlay Receiver
# Based on: https://github.com/harrylepotter/carplay-receiver

set -e

echo "Setting up CarPlay Receiver for Sambar HUD..."

# Install dependencies
echo "Installing dependencies..."
sudo apt-get update
sudo apt-get install -y \
    python3-pip \
    python3-dev \
    ffmpeg \
    mpv \
    libmpv-dev \
    libusb-1.0-0-dev \
    git

# Install Python packages
echo "Installing Python packages..."
pip3 install pyusb

# Clone carplay-receiver repository
CARPLAY_DIR="$HOME/carplay-receiver"
if [ ! -d "$CARPLAY_DIR" ]; then
    echo "Cloning carplay-receiver repository..."
    git clone https://github.com/harrylepotter/carplay-receiver.git "$CARPLAY_DIR"
    cd "$CARPLAY_DIR"
else
    echo "CarPlay receiver directory exists, updating..."
    cd "$CARPLAY_DIR"
    git pull
fi

# Download assets from APK
echo "Downloading assets from APK..."
if [ -f "downloadassets.sh" ]; then
    chmod +x downloadassets.sh
    ./downloadassets.sh
else
    echo "Warning: downloadassets.sh not found. You may need to download assets manually."
fi

# Create symlink for easy access
if [ ! -f "/usr/local/bin/carplay.py" ]; then
    echo "Creating symlink..."
    sudo ln -s "$CARPLAY_DIR/carplay.py" /usr/local/bin/carplay.py
fi

# Configure USB permissions
echo "Configuring USB permissions..."
if ! grep -q "SUBSYSTEM==\"usb\"" /etc/udev/rules.d/99-carplay.rules 2>/dev/null; then
    sudo tee /etc/udev/rules.d/99-carplay.rules > /dev/null <<EOF
# CarPlay USB device permissions
SUBSYSTEM=="usb", ATTRS{idVendor}=="05ac", MODE="0666"
SUBSYSTEM=="usb", ATTRS{idVendor}=="0e8d", MODE="0666"
EOF
    sudo udevadm control --reload-rules
    sudo udevadm trigger
fi

# Add user to plugdev group (if exists)
if getent group plugdev > /dev/null 2>&1; then
    sudo usermod -a -G plugdev $USER
    echo "Added user to plugdev group. You may need to log out and back in."
fi

echo ""
echo "CarPlay Receiver setup complete!"
echo ""
echo "Next steps:"
echo "1. Connect your Carlinkit dongle to a USB port"
echo "2. Connect your iPhone to the dongle"
echo "3. Run: sudo python3 $CARPLAY_DIR/carplay.py"
echo ""
echo "For Sambar HUD integration, the application will handle this automatically."
