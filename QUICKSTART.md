# Quick Start Guide

## Development on Mac

### Option 1: Using Docker (Recommended for Raspberry Pi simulation)

1. **Start the application**:
   ```bash
   make docker-build
   make docker-run
   ```

   Or directly:
   ```bash
   docker-compose up --build
   ```

2. **View the application**:
   - The application runs in a virtual display inside the container
   - To view it, you can use VNC or X11 forwarding (see README for details)

### Option 2: Local Development with Virtual Display

1. **Set up development environment**:
   ```bash
   make dev
   ```

2. **Start virtual display**:
   ```bash
   make start-vfb
   # Or: ./start_virtual_display.sh
   ```

3. **Run the application**:
   ```bash
   export DISPLAY=:99
   make run
   # Or: python3 main.py
   ```

4. **Stop virtual display when done**:
   ```bash
   make stop-vfb
   # Or: ./stop_virtual_display.sh
   ```

### Option 3: Direct Local Run (if you have X11)

If you have XQuartz installed and configured:

```bash
pip3 install -r requirements.txt
python3 main.py
```

## Testing the Application

The application will start with:
- **Left side**: Entertainment panel (Steam Link, YouTube, Netflix, AirPlay)
- **Right side**: CarPlay panel

You can switch between entertainment modes using the buttons at the top of the left panel.

## Configuration

Edit `config.yaml` to customize:
- Screen resolution (default: 2560x720)
- Default entertainment mode
- CarPlay settings
- Performance options

## Next Steps

1. **CarPlay Integration**: 
   - Install carplay-ai: https://github.com/electric-monk/carplay-ai
   - Update `carplay_panel.py` with actual connection code

2. **Steam Link**:
   - Install Steam Link app on Raspberry Pi
   - Or configure Steam Link web interface

3. **AirPlay**:
   - Configure pyatv for AirPlay receiver
   - Ensure network connectivity

## Deployment to Raspberry Pi

1. **Transfer files to Raspberry Pi**:
   ```bash
   scp -r . pi@raspberrypi.local:~/sambar_hud
   ```

2. **SSH into Raspberry Pi**:
   ```bash
   ssh pi@raspberrypi.local
   ```

3. **Run setup script**:
   ```bash
   cd ~/sambar_hud
   chmod +x setup_kiosk.sh
   ./setup_kiosk.sh
   ```

4. **Reboot**:
   ```bash
   sudo reboot
   ```

The application will start automatically on boot.

## Troubleshooting

### "Cannot connect to X server"
- Make sure virtual display is running: `make start-vfb`
- Or use Docker: `make docker-run`

### "Module not found" errors
- Install dependencies: `pip3 install -r requirements.txt`
- Or use Docker which has everything pre-installed

### Application doesn't fit screen
- Check `config.yaml` for correct screen dimensions
- Default is 2560x720, adjust if needed

### Performance issues
- On Mac: Should run fine
- On Raspberry Pi: See performance optimization in README
