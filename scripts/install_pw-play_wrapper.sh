#!/bin/bash
# Install pw-play wrapper so LIVI works with PipeWire that doesn't support --raw.
# Run once with: sudo scripts/install_pw-play_wrapper.sh
# This renames /usr/bin/pw-play to /usr/bin/pw-play.real and installs our
# wrapper as /usr/bin/pw-play. Reversible by: sudo mv /usr/bin/pw-play.real /usr/bin/pw-play
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REAL=/usr/bin/pw-play
WRAPPER="$SCRIPT_DIR/pw-play"
if [[ ! -f "$REAL" ]]; then
  echo "Error: $REAL not found (install pipewire-bin first)."
  exit 1
fi
if [[ ! -f "$WRAPPER" ]]; then
  echo "Error: Wrapper not found at $WRAPPER"
  exit 1
fi
if [[ -x /usr/bin/pw-play.real ]]; then
  echo "Already installed (pw-play.real exists). Overwriting wrapper."
else
  echo "Moving $REAL to ${REAL}.real"
  mv "$REAL" "${REAL}.real"
fi
echo "Installing wrapper as $REAL"
cp "$WRAPPER" "$REAL"
chmod +x "$REAL"
echo "Done. LIVI should now get audio. To undo: sudo mv /usr/bin/pw-play.real /usr/bin/pw-play"
echo "Then remove the wrapper: sudo rm /usr/bin/pw-play (and restore from package if needed)."
