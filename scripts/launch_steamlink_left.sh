#!/bin/bash
# Launch Steam Link positioned on left side of screen (1280x720)

# Kill any existing Steam Link instances
pkill -f steamlink 2>/dev/null
sleep 1

# Launch Steam Link
# Note: Steam Link may need to be run in windowed mode for positioning
steamlink &

# Wait for window to appear
sleep 3

# Position window on left side using wmctrl or xdotool
WINDOW_FOUND=false

# Try wmctrl first
if command -v wmctrl &> /dev/null; then
    # Find Steam Link window
    WINDOW_ID=$(wmctrl -l | grep -i "steam\|steamlink" | awk '{print $1}' | head -1)
    
    if [ ! -z "$WINDOW_ID" ]; then
        # Position: gravity, x, y, width, height
        wmctrl -i -r $WINDOW_ID -e 0,0,0,1280,720
        # Remove decorations for cleaner look (optional)
        wmctrl -i -r $WINDOW_ID -b add,fullscreen
        WINDOW_FOUND=true
        echo "Positioned Steam Link window with wmctrl"
    fi
fi

# Fallback to xdotool
if [ "$WINDOW_FOUND" = false ] && command -v xdotool &> /dev/null; then
    WINDOW_ID=$(xdotool search --name "Steam" | head -1)
    
    if [ ! -z "$WINDOW_ID" ]; then
        xdotool windowmove $WINDOW_ID 0 0
        xdotool windowsize $WINDOW_ID 1280 720
        xdotool windowactivate $WINDOW_ID
        WINDOW_FOUND=true
        echo "Positioned Steam Link window with xdotool"
    fi
fi

if [ "$WINDOW_FOUND" = false ]; then
    echo "Warning: Could not position Steam Link window automatically"
    echo "Install wmctrl or xdotool: sudo apt-get install wmctrl xdotool"
fi
