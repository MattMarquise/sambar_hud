# Sambar HUD - Ultrawide CarPlay and Entertainment System

A split-screen entertainment system designed for Raspberry Pi, featuring CarPlay integration and media streaming capabilities. Optimized for a 2560x720 ultrawide touchscreen display.

## Features

- **Split-Screen Interface**: 
  - **Right Side (Driver)**: CarPlay integration for maps, music, and phone
  - **Left Side**: Entertainment options including Steam Link, YouTube, Netflix, and AirPlay

- **Apple-Only Connectivity**: Designed exclusively for Apple devices (iPhone, iPad)

- **Kiosk Mode**: Auto-boots on power-up, runs in fullscreen kiosk mode

- **Raspberry Pi Optimized**: Built for efficient performance on Raspberry Pi hardware

## Hardware Requirements

- Raspberry Pi 4 (recommended) or Raspberry Pi 5
- 2560x720 ultrawide touchscreen display
- USB connection for iPhone/iPad
- Network connection (WiFi or Ethernet) for streaming services

## Development Setup (Mac)

### Prerequisites

- Docker Desktop for Mac
- Python 3.11+ (for local development without Docker)

### Using Docker (Recommended)

1. **Build the Docker image**:
   ```bash
   docker-compose build
   ```

2. **Run the application**:
   ```bash
   docker-compose up
   ```

3. **For development with X11 forwarding** (to see GUI on Mac):
   ```bash
   # Install XQuartz for X11 support on Mac
   brew install --cask xquartz
   
   # Start XQuartz and allow network connections
   # Then run:
   docker-compose up
   ```

### Local Development (Without Docker)

1. **Install dependencies**:
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Run the application**:
   ```bash
   python3 main.py
   ```

   Note: You may need to set up a virtual display for testing:
   ```bash
   # Install Xvfb for virtual display
   brew install xvfb
   
   # Run with virtual display
   Xvfb :99 -screen 0 2560x720x24 &
   export DISPLAY=:99
   python3 main.py
   ```

## Raspberry Pi Deployment (kiosk / fullscreen)

The app runs in **fullscreen kiosk mode** on the Pi (frameless, no window chrome). See **[PI_KIOSK.md](PI_KIOSK.md)** for full instructions.

### Quick setup

1. **Install Raspberry Pi OS** (64-bit recommended).

2. **Clone or copy the repo** and go into the project:
   ```bash
   cd sambar_hud
   ```

3. **Run the kiosk setup script**:
   ```bash
   chmod +x setup_kiosk.sh
   ./setup_kiosk.sh
   ```

4. **Reboot**:
   ```bash
   sudo reboot
   ```

The application starts automatically on boot in fullscreen. To run once without auto-start: `python3 main.py`.

### Manual Configuration

If you prefer manual setup:

1. **Install dependencies**:
   ```bash
   sudo apt-get update
   sudo apt-get install -y python3-pip python3-pyqt6 python3-pyqt6.qtwebengine
   pip3 install -r requirements.txt
   ```

2. **Configure display** in `/boot/config.txt`:
   ```
   hdmi_group=2
   hdmi_mode=87
   hdmi_cvt=2560 720 60 6 0 0 0
   gpu_mem=128
   ```

3. **Set up auto-start** (see `setup_kiosk.sh` for details)

## Configuration

Edit `config.yaml` to customize settings:

- Display resolution
- CarPlay settings
- Entertainment mode preferences
- Performance optimizations

## CarPlay Integration

CarPlay integration uses a Carlinkit dongle and the carplay-receiver project. See `CARPLAY_SETUP.md` for:
- Hardware setup (Carlinkit dongle)
- Software installation
- USB permissions configuration
- Window positioning (right side only)
- Troubleshooting

## AirPlay Integration

AirPlay setup for streaming from iPhone/iPad. See `AIRPLAY_SETUP.md` for:
- Software installation (RPiPlay/UxPlay)
- Hardware requirements
- Display positioning (left side only)
- Integration with Sambar HUD

## Entertainment Features

On the **Raspberry Pi**, Netflix, YouTube, Steam, and AirPlay run in the **left half of the screen** using Qt WebEngine (`QWebEngineView`). Each app loads as the main document (not in an iframe), so Netflix and YouTube work normally. The browser preview (`index.html`) can’t embed those sites due to iframe restrictions; the Pi app does not have that limitation.

### Steam Link
- Requires Steam Link app installed on Raspberry Pi
- Or use Steam Link web interface (limited functionality)

### YouTube
- Uses YouTube TV interface for better car experience
- Requires internet connection

### Netflix
- Uses Netflix web interface
- Requires Netflix account and internet connection

### AirPlay
- Uses pyatv library for AirPlay receiver functionality
- iPhone can stream directly to the system
- Requires network connection (WiFi recommended)

## Performance Optimization

For better performance on Raspberry Pi:

1. **Increase GPU memory** in `config.yaml`:
   ```yaml
   performance:
     gpu_mem: 128  # Increase if needed (up to 256)
   ```

2. **Enable low power mode** if needed:
   ```yaml
   performance:
     low_power_mode: true
   ```

3. **Overclock** (optional, at your own risk):
   Edit `/boot/config.txt`:
   ```
   arm_freq=2000
   gpu_freq=750
   ```

## Troubleshooting

### Display Issues
- Check `/boot/config.txt` for correct resolution settings
- Verify HDMI connection and display compatibility

### CarPlay Not Connecting
- Ensure USB connection is properly configured
- Check carplay-ai service status
- Verify iPhone is unlocked and CarPlay is enabled

### Performance Issues
- Close unnecessary applications
- Increase GPU memory split
- Consider using Raspberry Pi 5 for better performance

### Application Won't Start
- Check logs: `journalctl -u sambar-hud.service`
- Verify all dependencies are installed
- Check display permissions

## Development

### Project Structure

```
sambar_hud/
├── main.py                 # Main application entry point
├── config.py               # Configuration management
├── config.yaml             # Configuration file
├── carplay_panel.py        # CarPlay interface panel
├── entertainment_panel.py  # Entertainment panel
├── requirements.txt        # Python dependencies
├── Dockerfile             # Docker build configuration
├── docker-compose.yml     # Docker Compose configuration
├── setup_kiosk.sh        # Raspberry Pi setup script
└── README.md             # This file
```

### Adding New Features

1. Create new panel/widget in separate file
2. Import and integrate in `main.py`
3. Update configuration in `config.yaml`
4. Test on Raspberry Pi hardware

## License

[Add your license here]

## Contributing

[Add contribution guidelines if needed]

## Support

For issues and questions, please open an issue on the repository.
