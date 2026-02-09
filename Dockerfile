# Dockerfile for Raspberry Pi development environment
# Based on Raspberry Pi OS (Debian-based)
FROM arm32v7/python:3.11-slim-bullseye

# Set display dimensions for ultrawide screen
ENV DISPLAY=:0
ENV SCREEN_WIDTH=2560
ENV SCREEN_HEIGHT=720

# Install system dependencies
RUN apt-get update && apt-get install -y \
    xorg \
    xserver-xorg-video-fbdev \
    xserver-xorg-input-evdev \
    x11-xserver-utils \
    xinit \
    openbox \
    chromium-browser \
    python3-pip \
    python3-dev \
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    pulseaudio \
    alsa-utils \
    vlc \
    ffmpeg \
    git \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libxkbcommon-x11-0 \
    libxcb-xinerama0 \
    libxcb-cursor0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libatspi2.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxkbcommon0 \
    libxrandr2 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create startup script
RUN echo '#!/bin/bash\n\
Xvfb :0 -screen 0 ${SCREEN_WIDTH}x${SCREEN_HEIGHT}x24 &\n\
export DISPLAY=:0\n\
python3 main.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose display
EXPOSE 5900

CMD ["/app/start.sh"]
