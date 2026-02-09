#!/bin/bash
# Development setup script for Mac
# Sets up a virtual display environment for testing

set -e

echo "Setting up development environment for Mac..."

# Check if XQuartz is installed
if ! command -v xquartz &> /dev/null; then
    echo "XQuartz not found. Installing..."
    brew install --cask xquartz
    echo "Please restart your Mac after XQuartz installation, then run this script again."
    exit 1
fi

# Check if Xvfb is installed (for headless testing)
if ! command -v Xvfb &> /dev/null; then
    echo "Xvfb not found. Installing..."
    brew install xvfb
fi

# Create virtual display script
cat > start_virtual_display.sh <<'EOF'
#!/bin/bash
# Start virtual display for testing

SCREEN_WIDTH=2560
SCREEN_HEIGHT=720

echo "Starting virtual display: ${SCREEN_WIDTH}x${SCREEN_HEIGHT}"

# Kill any existing Xvfb processes
pkill Xvfb 2>/dev/null || true

# Start Xvfb
Xvfb :99 -screen 0 ${SCREEN_WIDTH}x${SCREEN_HEIGHT}x24 -ac +extension GLX +render -noreset &
XVFB_PID=$!

echo "Xvfb started with PID: $XVFB_PID"
echo "Display: :99"
echo ""
echo "To use this display, run:"
echo "  export DISPLAY=:99"
echo "  python3 main.py"
echo ""
echo "To stop the virtual display, run:"
echo "  kill $XVFB_PID"
echo ""
echo "Or save the PID:"
echo "  echo $XVFB_PID > .xvfb.pid"

echo $XVFB_PID > .xvfb.pid
EOF

chmod +x start_virtual_display.sh

# Create stop script
cat > stop_virtual_display.sh <<'EOF'
#!/bin/bash
# Stop virtual display

if [ -f .xvfb.pid ]; then
    PID=$(cat .xvfb.pid)
    echo "Stopping Xvfb (PID: $PID)..."
    kill $PID 2>/dev/null && rm .xvfb.pid && echo "Stopped" || echo "Process not found"
else
    echo "No virtual display running (no .xvfb.pid file)"
    pkill Xvfb 2>/dev/null && echo "Killed any remaining Xvfb processes" || echo "No Xvfb processes found"
fi
EOF

chmod +x stop_virtual_display.sh

echo ""
echo "Development environment setup complete!"
echo ""
echo "To start a virtual display for testing:"
echo "  ./start_virtual_display.sh"
echo ""
echo "Then run the application:"
echo "  export DISPLAY=:99"
echo "  python3 main.py"
echo ""
echo "To stop the virtual display:"
echo "  ./stop_virtual_display.sh"
echo ""
echo "Alternatively, use Docker for a more complete Raspberry Pi simulation:"
echo "  docker-compose up"
