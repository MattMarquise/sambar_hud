#!/bin/bash
# Install pw-play wrapper so LIVI works with PipeWire that doesn't support --raw.
# Run once with: sudo scripts/install_pw-play_wrapper.sh
# Installs wrapper to /usr/bin/pw-play (if real is there) or /usr/local/bin/pw-play (else).
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WRAPPER="$SCRIPT_DIR/pw-play"
if [[ ! -f "$WRAPPER" ]]; then
  echo "Error: Wrapper not found at $WRAPPER"
  exit 1
fi

# Find the real pw-play (often in /usr/bin; on some distros elsewhere)
REAL=""
if [[ -f /usr/bin/pw-play ]] && [[ ! -L /usr/bin/pw-play ]]; then
  REAL=/usr/bin/pw-play
elif [[ -f /usr/bin/pw-play.real ]]; then
  REAL=/usr/bin/pw-play.real
else
  REAL=$(find /usr -name 'pw-play' -type f -executable 2>/dev/null | head -1)
fi
if [[ -z "$REAL" ]]; then
  echo "Error: pw-play not found on this system."
  echo ""
  echo "Install the PipeWire package that provides pw-play, then run this script again:"
  echo ""
  if command -v apt-get &>/dev/null; then
    echo "  Debian/Ubuntu:"
    echo "    sudo apt update"
    echo "    sudo apt install pipewire pipewire-bin pipewire-audio"
    echo ""
    echo "  If that doesn't provide pw-play, search for it:"
    echo "    apt search pipewire   # then install the package that has 'bin' or 'tools'"
  elif command -v dnf &>/dev/null; then
    echo "  Fedora:  sudo dnf install pipewire-utils"
  elif command -v pacman &>/dev/null; then
    echo "  Arch:    sudo pacman -S pipewire"
  else
    echo "  Debian/Ubuntu: sudo apt install pipewire pipewire-bin pipewire-audio"
    echo "  Fedora:        sudo dnf install pipewire-utils"
    echo "  Arch:          sudo pacman -S pipewire"
  fi
  echo ""
  echo "After installing, run:  sudo $0"
  exit 1
fi

if [[ "$REAL" == /usr/bin/pw-play ]]; then
  # Standard: real is /usr/bin/pw-play; replace with wrapper, keep real as .real
  INSTALL_TO=/usr/bin/pw-play
  if [[ -x /usr/bin/pw-play.real ]]; then
    echo "Already have pw-play.real in /usr/bin. Overwriting wrapper."
  else
    echo "Moving /usr/bin/pw-play to /usr/bin/pw-play.real"
    mv /usr/bin/pw-play /usr/bin/pw-play.real
  fi
  cp "$WRAPPER" /usr/bin/pw-play
  chmod +x /usr/bin/pw-play
  echo "Done. Wrapper installed at /usr/bin/pw-play"
else
  # Real is elsewhere (or .real): install wrapper and real into /usr/local/bin so 'pw-play' is findable
  echo "Found real pw-play at: $REAL"
  echo "Installing wrapper to /usr/local/bin/pw-play (real as /usr/local/bin/pw-play.real)"
  mkdir -p /usr/local/bin
  cp "$REAL" /usr/local/bin/pw-play.real
  chmod +x /usr/local/bin/pw-play.real
  cp "$WRAPPER" /usr/local/bin/pw-play
  chmod +x /usr/local/bin/pw-play
  echo "Done. Ensure /usr/local/bin is in your PATH (it usually is). Check: which pw-play"
fi
echo "LIVI should now get audio. To undo: remove the wrapper and restore the real binary (see script comments)."
