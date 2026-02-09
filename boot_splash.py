"""
Boot splash screen - full screen (2560x720) shown on startup.
Plays sound/bootintro.mp3 and shows Subaru logo for 3 seconds, then fades to main.
"""

import os
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap

try:
    import pygame
    _PYGAME_AVAILABLE = True
except ImportError:
    _PYGAME_AVAILABLE = False


def _play_boot_sound() -> None:
    """Play sound/bootintro.mp3 if present. No-op if pygame or file missing."""
    if not _PYGAME_AVAILABLE:
        return
    sound_dir = os.path.join(os.path.dirname(__file__), "sound")
    path = os.path.join(sound_dir, "bootintro.mp3")
    if not os.path.isfile(path):
        return
    try:
        pygame.mixer.init()
        s = pygame.mixer.Sound(path)
        s.play()
    except Exception:
        pass


class BootSplash(QWidget):
    """Full-screen boot animation with Subaru logo and optional boot sound."""

    def __init__(self, width=2560, height=720, duration_ms=3000, parent=None):
        super().__init__(parent)
        self.width = width
        self.height = height
        self.duration_ms = duration_ms
        self.on_finished = None
        self.setup_ui()

    def setup_ui(self):
        self.setFixedSize(self.width, self.height)
        self.setStyleSheet("background-color: #222222;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Subaru logo scaled to fit within screen (width x height)
        img_dir = os.path.join(os.path.dirname(__file__), "img")
        logo_path = os.path.join(img_dir, "subaru-logo.png")
        if not os.path.exists(logo_path):
            logo_path = os.path.join(img_dir, "car-logo.png")
        if os.path.exists(logo_path):
            logo = QLabel()
            logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
            pix = QPixmap(logo_path)
            if not pix.isNull():
                # Scale to fit within splash pixel bounds (width x height), keep aspect ratio
                rw = self.width / pix.width()
                rh = self.height / pix.height()
                r = min(rw, rh)
                w = max(1, int(pix.width() * r))
                h = max(1, int(pix.height() * r))
                pix = pix.scaled(w, h, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            logo.setPixmap(pix)
            logo.setStyleSheet("background: transparent;")
            layout.addWidget(logo, alignment=Qt.AlignmentFlag.AlignCenter)
        else:
            title = QLabel("Sambar HUD")
            title.setAlignment(Qt.AlignmentFlag.AlignCenter)
            title.setStyleSheet("color: #fff; font-size: 72px; font-weight: 600; background: transparent;")
            layout.addWidget(title, alignment=Qt.AlignmentFlag.AlignCenter)

    def show_and_finish(self, callback):
        """Show splash, play boot sound, call callback after duration (e.g. 3s)."""
        self.on_finished = callback
        self.showFullScreen()
        _play_boot_sound()
        QTimer.singleShot(self.duration_ms, self._finish)

    def _finish(self):
        if self.on_finished:
            self.on_finished()
        self.close()
