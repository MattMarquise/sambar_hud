"""
CarPlay Feed - Display Carlinkit video on the right half of the screen

The Carlinkit dongle already provides wireless CarPlay. We only need to:
1. Receive the video feed from the Carlinkit (HDMI→USB capture, or USB video)
2. Display that feed in the right panel (1280x720)

Video source is typically:
- USB HDMI capture device (Carlinkit HDMI out → capture dongle → Pi USB) → /dev/video0
- Or Carlinkit with USB video out → /dev/videoX
"""

import os
import subprocess

def get_video_device():
    """Get the video capture device for CarPlay feed (e.g. from USB HDMI capture)."""
    # Default: first V4L2 device; override via env for multiple cameras
    return os.environ.get('CARPLAY_VIDEO_DEVICE', '/dev/video0')

def is_video_device_available(device=None):
    """Check if video capture device exists and is readable."""
    device = device or get_video_device()
    return os.path.exists(device) and os.access(device, os.R_OK)
