# Images Directory

Place your images here for the Sambar HUD entertainment system.

## Required Images

### Boot splash
- **subaru-logo.png** – Logo shown on boot (only thing on screen during startup)
  - Recommended size: 400x400px or larger (will be scaled to fit)
  - Format: PNG with transparency preferred
  - If missing, **car-logo.png** is used as fallback

### Car / Right Side (CarPlay panel)
- **car-logo.png** – Car or brand logo shown on the right (CarPlay) side when CarPlay feed is off
  - Recommended size: 400x400px or larger (will be scaled to fit)
  - Format: PNG with transparency preferred
  - Also used as boot splash fallback when subaru-logo.png is missing

### Sleep Mode (Left side)
- **van-3d.png** - 3D image/model of your van for sleep mode display
  - Recommended size: 600x400px or larger (will be scaled to fit)
  - Format: PNG with transparency preferred
  - The image will be displayed in sleep mode with the clock

### Left panel (single “sleep” page)
The left side shows one screen only: clock, van image, and corner buttons (Steam Link icon, Light).
- **van-3d.png** – 3D van image (see Sleep Mode above)
- No banners or posters; Steam Link is launched via the Steam icon (mdi:steam) in the corner.

## Usage

- The sleep mode will automatically look for `van-3d.png` in this directory. If the image is not found, a placeholder will be displayed instead.
- Banner and poster images will replace the CSS-generated backgrounds when added to this folder.
- All images should be optimized for web to ensure fast loading on Raspberry Pi.
