"""
Entertainment Panel - Left side
Handles Steam Link, YouTube, Netflix, and AirPlay streaming
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QStackedWidget, QButtonGroup
)
from PyQt6.QtCore import Qt, QUrl, QTimer, QProcess, QPoint
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtGui import QFont, QPixmap
import subprocess
import os

class EntertainmentPanel(QWidget):
    """Entertainment interface panel"""

    def __init__(self, width, height, parent=None, start_in_sleep=False):
        super().__init__(parent)
        self.width = width
        self.height = height
        self.current_mode = None
        self.processes = {}
        self.overlay_visible = True
        self.start_in_sleep = start_in_sleep
        self.sleep_mode_active = False
        self.create_overlay()  # before init_ui so switch_mode() can call hide_overlay()
        self.init_ui()
        self.create_sleep_mode()
        if self.start_in_sleep:
            self.enter_sleep_mode()
        
    def init_ui(self):
        """Initialize the Entertainment UI"""
        self.setFixedSize(self.width, self.height)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Header with title and Sleep button
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(10, 10, 10, 10)
        header_layout.setSpacing(0)
        header_widget.setStyleSheet("background-color: #1a1a1a; border-bottom: 2px solid #333;")
        header = QLabel("Entertainment")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("color: white; font-size: 24px; font-weight: bold; background: transparent;")
        header_layout.addWidget(header, 1)
        self.sleep_btn = QPushButton("Sleep")
        self.sleep_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.1);
                color: white;
                font-size: 14px;
                padding: 8px 16px;
                border: 1px solid rgba(255,255,255,0.2);
                border-radius: 6px;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.2); }
        """)
        self.sleep_btn.clicked.connect(self.enter_sleep_mode)
        header_layout.addWidget(self.sleep_btn)
        layout.addWidget(header_widget)
        
        # Mode selection buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        button_layout.setContentsMargins(5, 5, 5, 5)
        
        self.button_group = QButtonGroup()
        
        # Steam Link button
        self.steam_btn = QPushButton("Steam Link")
        self.steam_btn.setCheckable(True)
        self.steam_btn.setStyleSheet(self.get_button_style())
        self.steam_btn.clicked.connect(lambda: self.switch_mode('steam_link'))
        self.button_group.addButton(self.steam_btn)
        button_layout.addWidget(self.steam_btn)
        
        # YouTube button
        self.youtube_btn = QPushButton("YouTube")
        self.youtube_btn.setCheckable(True)
        self.youtube_btn.setStyleSheet(self.get_button_style())
        self.youtube_btn.clicked.connect(lambda: self.switch_mode('youtube'))
        self.button_group.addButton(self.youtube_btn)
        button_layout.addWidget(self.youtube_btn)
        
        # Netflix button
        self.netflix_btn = QPushButton("Netflix")
        self.netflix_btn.setCheckable(True)
        self.netflix_btn.setStyleSheet(self.get_button_style())
        self.netflix_btn.clicked.connect(lambda: self.switch_mode('netflix'))
        self.button_group.addButton(self.netflix_btn)
        button_layout.addWidget(self.netflix_btn)
        
        # AirPlay button
        self.airplay_btn = QPushButton("AirPlay")
        self.airplay_btn.setCheckable(True)
        self.airplay_btn.setStyleSheet(self.get_button_style())
        self.airplay_btn.clicked.connect(lambda: self.switch_mode('airplay'))
        self.button_group.addButton(self.airplay_btn)
        button_layout.addWidget(self.airplay_btn)
        
        layout.addLayout(button_layout)
        
        # Stacked widget for different modes
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        # Create views for each mode
        self.create_steam_link_view()
        self.create_youtube_view()
        self.create_netflix_view()
        self.create_airplay_view()
        
        # Set default mode
        self.switch_mode('steam_link')

    def create_sleep_mode(self):
        """Sleep mode: clock, van image, Wake button. Shown on top when active."""
        self.sleep_container = QWidget(self)
        self.sleep_container.setFixedSize(self.width, self.height)
        self.sleep_container.setStyleSheet("background-color: #000;")
        sleep_layout = QVBoxLayout(self.sleep_container)
        sleep_layout.setContentsMargins(0, 0, 0, 0)
        sleep_layout.setSpacing(0)

        # Wake button - top right
        wake_btn = QPushButton("Wake")
        wake_btn.setFixedSize(120, 50)
        wake_btn.move(self.width - 140, 20)
        wake_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255,255,255,0.15);
                color: white;
                font-size: 18px;
                font-weight: bold;
                border: 2px solid rgba(255,255,255,0.3);
                border-radius: 8px;
            }
            QPushButton:hover { background-color: rgba(255,255,255,0.25); }
        """)
        wake_btn.clicked.connect(self.leave_sleep_mode)
        wake_btn.setParent(self.sleep_container)
        wake_btn.move(self.width - 140, 20)

        # Clock
        self.sleep_clock = QLabel("00:00:00")
        self.sleep_clock.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sleep_clock.setStyleSheet("""
            QLabel {
                color: rgba(255,255,255,0.9);
                font-size: 96px;
                font-weight: 300;
                background: transparent;
            }
        """)
        sleep_layout.addSpacing(80)
        sleep_layout.addWidget(self.sleep_clock)

        # Date
        self.sleep_date = QLabel("")
        self.sleep_date.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.sleep_date.setStyleSheet("""
            QLabel {
                color: rgba(255,255,255,0.5);
                font-size: 24px;
                background: transparent;
            }
        """)
        sleep_layout.addWidget(self.sleep_date)

        # Van image
        van_label = QLabel()
        van_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        van_label.setStyleSheet("background: transparent;")
        img_dir = os.path.join(os.path.dirname(__file__), 'img')
        van_path = os.path.join(img_dir, 'van-3d.png')
        if os.path.exists(van_path):
            pix = QPixmap(van_path)
            pix = pix.scaled(500, 350, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            van_label.setPixmap(pix)
        else:
            van_label.setText("(van image)")
            van_label.setStyleSheet("color: #333; font-size: 18px; background: transparent;")
        sleep_layout.addWidget(van_label)
        sleep_layout.addStretch()

        self.sleep_container.hide()
        self.sleep_clock_timer = QTimer(self)
        self.sleep_clock_timer.timeout.connect(self._update_sleep_clock)

    def _update_sleep_clock(self):
        """Update sleep clock to Eastern time (EST/EDT), 12-hour format."""
        from datetime import datetime
        try:
            from zoneinfo import ZoneInfo
            eastern = ZoneInfo("America/New_York")
        except ImportError:
            try:
                import pytz
                eastern = pytz.timezone("America/New_York")
            except ImportError:
                eastern = None
        if eastern:
            now = datetime.now(eastern)
        else:
            now = datetime.now()
        # 12-hour, no seconds: e.g. 2:30 PM (no leading zero on hour)
        hour_12 = int(now.strftime("%I"))
        time_str = f"{hour_12}:{now.strftime('%M %p')}"
        self.sleep_clock.setText(time_str)
        self.sleep_date.setText(now.strftime("%A, %B %d") + "  ·  Eastern")

    def enter_sleep_mode(self):
        """Show sleep screen, hide entertainment content (with smooth transition)."""
        self.sleep_mode_active = True
        self.sleep_container.raise_()
        self._update_sleep_clock()
        self.sleep_clock_timer.start(60000)
        self.stop_current_mode()
        if hasattr(self, 'sleep_btn'):
            self.sleep_btn.hide()
        # Smooth fade-in: sleep container uses opacity animation via style
        self.sleep_container.setStyleSheet("background-color: #000;")
        try:
            from PyQt6.QtCore import QPropertyAnimation
            from PyQt6.QtGui import QGraphicsOpacityEffect
            eff = QGraphicsOpacityEffect(self.sleep_container)
            self.sleep_container.setGraphicsEffect(eff)
            eff.setOpacity(0.0)
            self.sleep_container.show()
            anim = QPropertyAnimation(eff, b"opacity")
            anim.setDuration(350)
            anim.setStartValue(0.0)
            anim.setEndValue(1.0)
            anim.start()
        except Exception:
            self.sleep_container.show()

    def leave_sleep_mode(self):
        """Hide sleep screen, show entertainment content (with smooth transition)."""
        self.sleep_mode_active = False
        self.sleep_clock_timer.stop()
        try:
            from PyQt6.QtCore import QPropertyAnimation
            from PyQt6.QtGui import QGraphicsOpacityEffect
            eff = self.sleep_container.graphicsEffect()
            if eff and isinstance(eff, QGraphicsOpacityEffect):
                self._sleep_fade_anim = QPropertyAnimation(eff, b"opacity")
                self._sleep_fade_anim.setDuration(350)
                self._sleep_fade_anim.setStartValue(1.0)
                self._sleep_fade_anim.setEndValue(0.0)
                self._sleep_fade_anim.finished.connect(self._hide_sleep_after_fade)
                self._sleep_fade_anim.start()
                return
        except Exception:
            pass
        self._hide_sleep_after_fade()

    def _hide_sleep_after_fade(self):
        """Called after fade-out to hide sleep container and clear effect."""
        try:
            self.sleep_container.setGraphicsEffect(None)
        except Exception:
            pass
        self.sleep_container.hide()
        if hasattr(self, 'sleep_btn'):
            self.sleep_btn.show()

    def create_overlay(self):
        """Create overlay control bar for exiting apps"""
        # Create overlay widget that floats on top
        self.overlay = QWidget(self)
        self.overlay.setFixedSize(self.width, 60)
        self.overlay.move(0, self.height - 60)  # Position at bottom
        self.overlay.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 0.85);
                border-top: 2px solid rgba(255, 255, 255, 0.3);
            }
        """)
        
        overlay_layout = QHBoxLayout(self.overlay)
        overlay_layout.setContentsMargins(20, 10, 20, 10)
        overlay_layout.setSpacing(15)
        
        # Exit/Quit button
        self.exit_btn = QPushButton("Exit App")
        self.exit_btn.setStyleSheet("""
            QPushButton {
                background-color: #E50914;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 12px 30px;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #B20710;
            }
            QPushButton:pressed {
                background-color: #8B0508;
            }
        """)
        self.exit_btn.clicked.connect(self.exit_current_app)
        overlay_layout.addWidget(self.exit_btn)
        
        # Back to menu button
        self.menu_btn = QPushButton("Back to Menu")
        self.menu_btn.setStyleSheet("""
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                font-size: 16px;
                font-weight: bold;
                padding: 12px 30px;
                border: 2px solid #444;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border-color: #555;
            }
            QPushButton:pressed {
                background-color: #1a1a1a;
            }
        """)
        self.menu_btn.clicked.connect(self.back_to_menu)
        overlay_layout.addWidget(self.menu_btn)
        
        overlay_layout.addStretch()
        
        # Hide/Show toggle button
        self.toggle_overlay_btn = QPushButton("Hide")
        self.toggle_overlay_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(255, 255, 255, 0.1);
                color: white;
                font-size: 14px;
                padding: 8px 20px;
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 6px;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.2);
            }
        """)
        self.toggle_overlay_btn.clicked.connect(self.toggle_overlay)
        overlay_layout.addWidget(self.toggle_overlay_btn)
        
        # Initially hide overlay, show when app is running
        self.overlay.hide()
        
    def toggle_overlay(self):
        """Toggle overlay visibility"""
        self.overlay_visible = not self.overlay_visible
        if self.overlay_visible:
            self.overlay.show()
            self.toggle_overlay_btn.setText("Hide")
        else:
            self.overlay.hide()
            self.toggle_overlay_btn.setText("Show")
    
    def show_overlay(self):
        """Show overlay"""
        self.overlay_visible = True
        if hasattr(self, 'overlay') and self.overlay is not None:
            self.overlay.show()
            self.toggle_overlay_btn.setText("Hide")
    
    def hide_overlay(self):
        """Hide overlay"""
        self.overlay_visible = False
        if hasattr(self, 'overlay') and self.overlay is not None:
            self.overlay.hide()
            self.toggle_overlay_btn.setText("Show")
    
    def exit_current_app(self):
        """Exit the currently running app"""
        self.stop_current_mode()
        # Switch back to menu/selection screen
        self.back_to_menu()
    
    def back_to_menu(self):
        """Return to app selection menu"""
        self.stop_current_mode()
        # Hide the stacked widget content, show selection buttons
        # The buttons are always visible, so just ensure we're not in fullscreen app mode
        self.current_mode = None
        # Reset button states
        for btn in [self.steam_btn, self.youtube_btn, self.netflix_btn, self.airplay_btn]:
            btn.setChecked(False)
        
    def get_button_style(self):
        """Get style for mode selection buttons"""
        return """
            QPushButton {
                background-color: #2a2a2a;
                color: white;
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                border: 2px solid #444;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border-color: #555;
            }
            QPushButton:checked {
                background-color: #007AFF;
                border-color: #0056CC;
            }
        """
        
    def create_steam_link_view(self):
        """Create Steam Link view"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Placeholder view - Steam Link will run as external app
        self.steam_view = QLabel("Steam Link\n\nLaunching Steam Link application...")
        self.steam_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.steam_view.setStyleSheet("""
            QLabel {
                background-color: #000;
                color: #fff;
                font-size: 18px;
                padding: 40px;
            }
        """)
        
        layout.addWidget(self.steam_view)
        
        self.stacked_widget.addWidget(widget)
        
    def create_youtube_view(self):
        """Create YouTube view"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # YouTube web view
        self.youtube_view = QWebEngineView()
        # Use YouTube TV interface for better car experience
        self.youtube_view.setUrl(QUrl("https://www.youtube.com/tv"))
        
        layout.addWidget(self.youtube_view)
        
        self.stacked_widget.addWidget(widget)
        
    def create_netflix_view(self):
        """Create Netflix view"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Netflix web view
        self.netflix_view = QWebEngineView()
        self.netflix_view.setUrl(QUrl("https://www.netflix.com"))
        
        layout.addWidget(self.netflix_view)
        
        self.stacked_widget.addWidget(widget)
        
    def create_airplay_view(self):
        """Create AirPlay receiver view"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # AirPlay receiver display
        # This will use pyatv or similar to receive AirPlay streams
        self.airplay_view = QLabel("AirPlay Receiver\n\nWaiting for iPhone connection...")
        self.airplay_view.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.airplay_view.setStyleSheet("""
            QLabel {
                background-color: #000;
                color: #fff;
                font-size: 18px;
                padding: 20px;
            }
        """)
        
        layout.addWidget(self.airplay_view)
        
        # Instructions
        instructions = QLabel("Enable AirPlay on your iPhone and select this device")
        instructions.setAlignment(Qt.AlignmentFlag.AlignCenter)
        instructions.setStyleSheet("""
            QLabel {
                background-color: #2a2a2a;
                color: #888;
                font-size: 12px;
                padding: 10px;
            }
        """)
        layout.addWidget(instructions)
        
        self.stacked_widget.addWidget(widget)
        
        # Start AirPlay receiver service
        self.start_airplay_receiver()
        
    def switch_mode(self, mode):
        """Switch between different entertainment modes"""
        if self.current_mode == mode:
            return
            
        # Stop current mode processes
        self.stop_current_mode()
        
        self.current_mode = mode
        
        # Show corresponding view
        if mode == 'steam_link':
            self.stacked_widget.setCurrentIndex(0)
            self.steam_btn.setChecked(True)
            self.start_steam_link()
        elif mode == 'youtube':
            self.stacked_widget.setCurrentIndex(1)
            self.youtube_btn.setChecked(True)
            self.show_overlay()
        elif mode == 'netflix':
            self.stacked_widget.setCurrentIndex(2)
            self.netflix_btn.setChecked(True)
            self.show_overlay()
        elif mode == 'airplay':
            self.stacked_widget.setCurrentIndex(3)
            self.airplay_btn.setChecked(True)
            self.start_airplay_receiver()
            self.show_overlay()
            
    def start_steam_link(self):
        """Start Steam Link application fullscreen on left side"""
        try:
            # Check if Steam Link app is installed
            steam_link_paths = [
                '/usr/bin/steamlink',
                '/usr/local/bin/steamlink',
                '/opt/steamlink/steamlink',
                'steamlink'  # Try PATH
            ]
            
            steam_cmd = None
            for path in steam_link_paths:
                if os.path.exists(path) or path == 'steamlink':
                    # Check if it's in PATH
                    result = subprocess.run(['which', path] if path == 'steamlink' else ['test', '-f', path],
                                           capture_output=True)
                    if result.returncode == 0 or os.path.exists(path):
                        steam_cmd = path if os.path.exists(path) else 'steamlink'
                        break
            
            if steam_cmd:
                # Try using helper script first (if available)
                script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'start_steam_link_left.sh')
                if os.path.exists(script_path):
                    process = QProcess()
                    process.start('/bin/bash', [script_path])
                    self.processes['steam_link'] = process
                else:
                    # Launch Steam Link directly
                    process = QProcess()
                    
                    # Set environment for window positioning
                    env = os.environ.copy()
                    process.setProcessEnvironment(env)
                    
                    # Start Steam Link (without fullscreen flag to allow positioning)
                    process.start(steam_cmd)
                    self.processes['steam_link'] = process
                
                # Show overlay for exit control
                self.show_overlay()
                
                # Position window on left side after delay
                QTimer.singleShot(2000, self.position_steam_link_window)
                QTimer.singleShot(3000, self.position_steam_link_window)  # Retry
                QTimer.singleShot(5000, self.position_steam_link_window)  # Final retry
                
                return
        except Exception as e:
            print(f"Could not start Steam Link app: {e}")
        
        # Fallback: show error message
        self.steam_view.setText("Steam Link not found.\n\nPlease install Steam Link:\nsudo apt-get install steamlink")
    
    def position_steam_link_window(self):
        """Position Steam Link window on left side of screen (1280x720)"""
        try:
            import subprocess
            
            # Try multiple window name patterns
            window_names = ['Steam Link', 'steamlink', 'Steam', 'steam']
            
            for window_name in window_names:
                # Try wmctrl first
                try:
                    result = subprocess.run(['wmctrl', '-l'], capture_output=True, text=True, timeout=1)
                    if result.returncode == 0:
                        for line in result.stdout.split('\n'):
                            if window_name.lower() in line.lower():
                                window_id = line.split()[0]
                                # Position: gravity, x, y, width, height
                                subprocess.Popen(['wmctrl', '-i', '-r', window_id, '-e', '0,0,0,1280,720'],
                                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                # Make it fullscreen within that area
                                subprocess.Popen(['wmctrl', '-i', '-r', window_id, '-b', 'add,fullscreen'],
                                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                print(f"Positioned Steam Link window: {window_name}")
                                return
                except:
                    pass
                
                # Fallback to xdotool
                try:
                    result = subprocess.run(['xdotool', 'search', '--name', window_name],
                                          capture_output=True, text=True, timeout=1)
                    if result.stdout.strip():
                        window_id = result.stdout.strip().split('\n')[0]
                        subprocess.Popen(['xdotool', 'windowmove', window_id, '0', '0'],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        subprocess.Popen(['xdotool', 'windowsize', window_id, '1280', '720'],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                        print(f"Positioned Steam Link window with xdotool: {window_name}")
                        return
                except:
                    pass
                    
        except Exception as e:
            print(f"Window positioning error: {e}")
            print("Install wmctrl or xdotool for automatic window positioning:")
            print("  sudo apt-get install wmctrl xdotool")
            
    def start_airplay_receiver(self):
        """Start AirPlay receiver service"""
        try:
            # Check if RPiPlay/UxPlay is installed
            airplay_paths = [
                '/usr/local/bin/RPiPlay',
                '/usr/bin/RPiPlay',
                '/usr/local/bin/uxplay',
                '/usr/bin/uxplay'
            ]
            
            airplay_cmd = None
            for path in airplay_paths:
                if os.path.exists(path):
                    airplay_cmd = path
                    break
            
            if airplay_cmd:
                # Start AirPlay receiver
                process = QProcess()
                # Run with device name and window positioning
                process.start(airplay_cmd, ['-n', 'Sambar HUD AirPlay', '-a', 'alsa'])
                self.processes['airplay'] = process
                
                # Position window on left side after delay
                QTimer.singleShot(3000, self.position_airplay_window)
            else:
                print("AirPlay receiver (RPiPlay/UxPlay) not found. See AIRPLAY_SETUP.md for installation.")
        except Exception as e:
            print(f"AirPlay receiver setup error: {e}")
    
    def position_airplay_window(self):
        """Position AirPlay window on left side of screen (1280x720)"""
        try:
            import subprocess
            # Try wmctrl first
            subprocess.Popen(['wmctrl', '-r', 'Sambar HUD AirPlay', '-e', '0,0,0,1280,720'], 
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except:
            try:
                # Fallback to xdotool
                import subprocess
                result = subprocess.run(['xdotool', 'search', '--name', 'Sambar HUD AirPlay'], 
                                      capture_output=True, text=True)
                if result.stdout.strip():
                    window_id = result.stdout.strip().split('\n')[0]
                    subprocess.Popen(['xdotool', 'windowmove', window_id, '0', '0'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    subprocess.Popen(['xdotool', 'windowsize', window_id, '1280', '720'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                print("Window positioning tools (wmctrl/xdotool) not available. Install for automatic positioning.")
            
    def stop_current_mode(self):
        """Stop processes for current mode"""
        if self.current_mode in self.processes:
            process = self.processes[self.current_mode]
            if process and process.state() == QProcess.ProcessState.Running:
                process.terminate()
                process.waitForFinished(3000)
                if process.state() == QProcess.ProcessState.Running:
                    process.kill()
            del self.processes[self.current_mode]
        
        # Also kill by process name as backup
        if self.current_mode == 'steam_link':
            try:
                subprocess.Popen(['pkill', '-f', 'steamlink'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except:
                pass
        
        # Hide overlay when no app is running
        self.hide_overlay()
            
    def closeEvent(self, event):
        """Clean up on close"""
        self.stop_current_mode()
        super().closeEvent(event)
