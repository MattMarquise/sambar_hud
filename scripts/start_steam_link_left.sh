#!/bin/bash
# Launch Steam Link and keep it on the LEFT half only (0,0 1280x720).
# Requires: Steam Link app installed, and wmctrl for window positioning.

set -e

# Install wmctrl if missing (optional; Python also runs positioning)
command -v wmctrl &>/dev/null || true

# Kill existing Steam Link so we get one window
pkill -f steamlink 2>/dev/null || true
pkill -f "Steam Link" 2>/dev/null || true
sleep 1

# Try common Steam Link commands (Pi / Steam Deck)
if command -v steamlink &>/dev/null; then
    steamlink &
elif command -v steam-link &>/dev/null; then
    steam-link &
else
    echo "Steam Link not found. Install it on the Pi (e.g. from Raspberry Pi OS Add/Remove Software, or: sudo apt install steamlink)"
    exit 1
fi

STEAM_PID=$!
sleep 2

# Position window on left half: remove fullscreen first, then set 1280x720 at 0,0
for i in 1 2 3 4 5 6 7 8 9 10; do
    sleep 1
    if ! command -v wmctrl &>/dev/null; then
        break
    fi
    WINDOW_ID=$(wmctrl -l 2>/dev/null | grep -i "steam.*link\|steamlink" | awk '{print $1}' | head -1)
    if [ -n "$WINDOW_ID" ]; then
        wmctrl -i -r "$WINDOW_ID" -b remove,maximized_vert,maximized_horz,fullscreen 2>/dev/null || true
        wmctrl -i -r "$WINDOW_ID" -e 0,0,0,1280,720 2>/dev/null || true
        break
    fi
done

wait $STEAM_PID 2>/dev/null || true
