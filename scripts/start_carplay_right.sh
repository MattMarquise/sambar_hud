#!/bin/bash
# Launch CarPlay receiver positioned on right side of screen (1280x720)
# Position: x=1280, y=0, width=1280, height=720

CARPLAY_DIR="$HOME/carplay-receiver"

# Check if carplay-receiver exists
if [ ! -d "$CARPLAY_DIR" ]; then
    echo "Error: CarPlay receiver not found at $CARPLAY_DIR"
    echo "Run: ./scripts/setup_carplay_receiver.sh"
    exit 1
fi

# Kill any existing CarPlay/mpv instances
pkill -f "carplay.py" 2>/dev/null
pkill -f "mpv.*carplay" 2>/dev/null
sleep 1

# Change to carplay-receiver directory
cd "$CARPLAY_DIR"

# Set environment variables for window positioning
export CARPLAY_WIDTH=1280
export CARPLAY_HEIGHT=720
export CARPLAY_X=1280
export CARPLAY_Y=0

# Start CarPlay receiver
echo "Starting CarPlay receiver..."
sudo python3 carplay.py &
CARPLAY_PID=$!

echo "CarPlay started with PID: $CARPLAY_PID"

# Wait for mpv window to appear
sleep 5

# Position the mpv window on right side
if command -v wmctrl &> /dev/null; then
    # Find mpv window
    WINDOW_ID=$(wmctrl -l | grep -i "mpv\|carplay" | awk '{print $1}' | head -1)
    
    if [ ! -z "$WINDOW_ID" ]; then
        echo "Positioning window $WINDOW_ID"
        # Position: gravity, x, y, width, height
        wmctrl -i -r $WINDOW_ID -e 0,1280,0,1280,720
        # Remove fullscreen if set
        wmctrl -i -r $WINDOW_ID -b remove,maximized_vert,maximized_horz,fullscreen
        # Ensure size
        wmctrl -i -r $WINDOW_ID -e 0,1280,0,1280,720
        echo "Window positioned successfully"
    else
        echo "mpv window not found with wmctrl, will retry..."
        # Retry after more delay
        sleep 3
        WINDOW_ID=$(wmctrl -l | grep -i "mpv\|carplay" | awk '{print $1}' | head -1)
        if [ ! -z "$WINDOW_ID" ]; then
            wmctrl -i -r $WINDOW_ID -e 0,1280,0,1280,720
            echo "Window positioned on retry"
        fi
    fi
elif command -v xdotool &> /dev/null; then
    # Fallback to xdotool
    sleep 2
    WINDOW_ID=$(xdotool search --name "mpv" | head -1)
    
    if [ ! -z "$WINDOW_ID" ]; then
        echo "Positioning window $WINDOW_ID with xdotool"
        xdotool windowmove $WINDOW_ID 1280 0
        xdotool windowsize $WINDOW_ID 1280 720
        echo "Window positioned successfully"
    else
        echo "mpv window not found with xdotool"
    fi
else
    echo "Warning: Neither wmctrl nor xdotool is installed."
    echo "Install one for automatic window positioning:"
    echo "  sudo apt-get install wmctrl xdotool"
fi

# Wait for CarPlay process
wait $CARPLAY_PID
