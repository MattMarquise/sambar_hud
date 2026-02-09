"""
CarPlay Panel - Right side (driver side for RHD vehicle)
Displays the Carlinkit CarPlay video feed on the right half of the screen.

The Carlinkit dongle already provides wireless CarPlay. We only direct its
video feed to the right half (1280x720) of the app.
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import Qt, QUrl, QTimer, QProcess
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QFont, QPixmap
import subprocess
import os

try:
    from carplay_feed import get_video_device, is_video_device_available
except ImportError:
    def get_video_device():
        return os.environ.get('CARPLAY_VIDEO_DEVICE', '/dev/video0')
    def is_video_device_available(device=None):
        d = device or get_video_device()
        return os.path.exists(d) and os.access(d, os.R_OK)


class CarPlayPanel(QWidget):
    """CarPlay panel - displays Carlinkit feed on the right half."""

    def __init__(self, width, height, parent=None):
        super().__init__(parent)
        self.width = width
        self.height = height
        self.feed_process = None
        self.init_ui()

    def init_ui(self):
        """Initialize the CarPlay UI — super basic: car logo, Show/Hide CarPlay."""
        self.setFixedSize(self.width, self.height)
        self.setStyleSheet("background-color: #fff;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(20)

        # Car logo
        img_dir = os.path.join(os.path.dirname(__file__), 'img')
        logo_path = os.path.join(img_dir, 'car-logo.png')
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setStyleSheet("background: transparent;")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path)
            pix = pix.scaled(320, 320, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.logo_label.setPixmap(pix)
        else:
            self.logo_label.setText("Car")
            self.logo_label.setStyleSheet("color: #333; font-size: 48px; background: transparent;")
        layout.addWidget(self.logo_label, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addStretch()

        # Content area when feed is off (minimal; feed runs in its own window)
        self.carplay_view = QWebEngineView()
        self.carplay_view.setUrl(QUrl("about:blank"))
        self.carplay_view.setFixedHeight(0)
        self.carplay_view.hide()
        layout.addWidget(self.carplay_view)

        # Status
        self.status_label = QLabel("Ready — Connect iPhone to Carlinkit")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status_label.setStyleSheet("""
            QLabel {
                background: transparent;
                color: rgba(255,255,255,0.6);
                font-size: 14px;
                padding: 4px;
            }
        """)
        layout.addWidget(self.status_label)

        # Show CarPlay
        show_btn = QPushButton("Show CarPlay")
        show_btn.setStyleSheet("""
            QPushButton {
                background-color: #007AFF;
                color: white;
                font-size: 18px;
                font-weight: bold;
                padding: 14px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover { background-color: #0056CC; }
            QPushButton:pressed { background-color: #003D99; }
        """)
        show_btn.clicked.connect(self.show_carplay_feed)
        layout.addWidget(show_btn)

        # Hide CarPlay
        hide_btn = QPushButton("Hide CarPlay")
        hide_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #555;
                font-size: 14px;
                padding: 10px;
                border: 1px solid #ccc;
                border-radius: 6px;
            }
            QPushButton:hover { background-color: #f0f0f0; }
        """)
        hide_btn.clicked.connect(self.hide_carplay_feed)
        layout.addWidget(hide_btn)

        self.show_idle_message()

    def show_idle_message(self):
        """Idle state: status text only (logo and buttons stay visible)."""
        self.status_label.setText("Ready — Connect iPhone to Carlinkit")
        self.status_label.setStyleSheet("""
            QLabel {
                background: transparent;
                color: rgba(255,255,255,0.6);
                font-size: 14px;
                padding: 4px;
            }
        """)

    def show_carplay_feed(self):
        """Start displaying the Carlinkit video feed on the right half."""
        self.status_label.setText("Starting CarPlay feed...")
        self.status_label.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                color: #ff0;
                font-size: 14px;
                padding: 5px;
            }
        """)

        device = get_video_device()

        if not is_video_device_available(device):
            self.status_label.setText(f"No video device: {device}")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #2a2a2a;
                    color: #f00;
                    font-size: 14px;
                    padding: 5px;
                }
            """)
            self.carplay_view.setHtml(f"""
                <html>
                <body style="background:#000;color:#fff;font-family:sans-serif;padding:40px;text-align:center;">
                    <h1>No video feed</h1>
                    <p>Device not found: {device}</p>
                    <p style="color:#888;">If using Carlinkit HDMI out, connect a USB HDMI capture dongle to the Pi and plug Carlinkit HDMI into it. Then set CARPLAY_VIDEO_DEVICE if needed (e.g. /dev/video0).</p>
                </body>
                </html>
            """)
            return

        # Start video in a window; we'll position it on the right half (1280, 0, 1280x720)
        # Use ffplay or GStreamer for low-latency display
        try:
            # Prefer GStreamer on Pi (hardware decode); fallback to ffplay
            if self._start_gstreamer_feed(device):
                pass
            elif self._start_ffplay_feed(device):
                pass
            else:
                self.status_label.setText("Install ffmpeg or GStreamer to show feed")
                self.status_label.setStyleSheet("""
                    QLabel {
                        background-color: #2a2a2a;
                        color: #f00;
                        font-size: 14px;
                        padding: 5px;
                    }
                """)
                return

            self.carplay_view.hide()
            self.status_label.setText("CarPlay feed on right half — Connect iPhone to Carlinkit")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #2a2a2a;
                    color: #0f0;
                    font-size: 14px;
                    padding: 5px;
                }
            """)

            # Position the video window on the right half
            QTimer.singleShot(1500, self._position_feed_window)
            QTimer.singleShot(3000, self._position_feed_window)
            QTimer.singleShot(5000, self._position_feed_window)

        except Exception as e:
            self.status_label.setText(f"Error: {str(e)}")
            self.status_label.setStyleSheet("""
                QLabel {
                    background-color: #2a2a2a;
                    color: #f00;
                    font-size: 14px;
                    padding: 5px;
                }
            """)

    def _start_gstreamer_feed(self, device):
        """Start video feed using GStreamer (good on Pi)."""
        try:
            # gst-launch-1.0 v4l2src device=/dev/video0 ! ... xvimagesink
            cmd = [
                'gst-launch-1.0', '-e',
                'v4l2src', f'device={device}', '!',
                'video/x-raw,width=1280,height=720', '!',
                'videoconvert', '!',
                'xvimagesink', 'sync=false'
            ]
            self.feed_process = subprocess.Popen(
                ' '.join(cmd),
                shell=True,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except FileNotFoundError:
            return False

    def _start_ffplay_feed(self, device):
        """Start video feed using ffplay. Window is positioned by wmctrl/xdotool."""
        try:
            cmd = [
                'ffplay', '-f', 'v4l2', '-video_size', '1280x720',
                '-window_title', 'CarPlay',
                '-noborder',
                device
            ]
            self.feed_process = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            return True
        except FileNotFoundError:
            return False

    def _position_feed_window(self):
        """Position the video window on the right half (1280, 0, 1280x720)."""
        try:
            for name in ['CarPlay', 'ffplay', 'GStreamer', 'xvimagesink']:
                try:
                    r = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True, timeout=1)
                    if r.returncode != 0:
                        continue
                    for line in r.stdout.split('\n'):
                        if name.lower() in line.lower():
                            wid = line.split()[0]
                            subprocess.Popen(
                                ['wmctrl', '-i', '-r', wid, '-e', '0,1280,0,1280,720'],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                            )
                            return
                except Exception:
                    pass
                try:
                    r = subprocess.run(['xdotool', 'search', '--name', name],
                                      capture_output=True, text=True, timeout=1)
                    if r.stdout.strip():
                        wid = r.stdout.strip().split('\n')[0]
                        subprocess.Popen(['xdotool', 'windowmove', wid, '1280', '0'],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        subprocess.Popen(['xdotool', 'windowsize', wid, '1280', '720'],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        return
                except Exception:
                    pass
        except Exception as e:
            print("Feed window positioning:", e)

    def hide_carplay_feed(self):
        """Stop and hide the CarPlay feed."""
        if self.feed_process and self.feed_process.poll() is None:
            self.feed_process.terminate()
            try:
                self.feed_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.feed_process.kill()
            self.feed_process = None

        try:
            subprocess.Popen(['pkill', '-f', 'ffplay'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.Popen(['pkill', '-f', 'gst-launch-1.0'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

        self.status_label.setText("Ready — Connect iPhone to Carlinkit")
        self.status_label.setStyleSheet("""
            QLabel {
                background: transparent;
                color: #555;
                font-size: 14px;
                padding: 4px;
            }
        """)
        self.show_idle_message()

    def disconnect_carplay(self):
        """Alias for hide_carplay_feed for compatibility."""
        self.hide_carplay_feed()

    def closeEvent(self, event):
        self.hide_carplay_feed()
        super().closeEvent(event)
