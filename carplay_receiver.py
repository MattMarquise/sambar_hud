"""
CarPlay Receiver Integration
Based on carplay-receiver project: https://github.com/harrylepotter/carplay-receiver
Handles connection to Carlinkit dongle and CarPlay display
"""

import subprocess
import os
import sys
from pathlib import Path

class CarPlayReceiver:
    """Manages CarPlay receiver connection and display"""
    
    def __init__(self, width=1280, height=720, x_offset=1280, y_offset=0):
        """
        Initialize CarPlay receiver
        
        Args:
            width: Display width (default: 1280 for right side)
            height: Display height (default: 720)
            x_offset: X position offset (default: 1280 to position on right side)
            y_offset: Y position offset (default: 0)
        """
        self.width = width
        self.height = height
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.process = None
        self.receiver_path = None
        self.find_receiver()
    
    def find_receiver(self):
        """Find CarPlay receiver installation"""
        # Check common installation paths
        possible_paths = [
            os.path.join(os.path.dirname(__file__), 'carplay-receiver', 'carplay.py'),
            os.path.expanduser('~/carplay-receiver/carplay.py'),
            '/opt/carplay-receiver/carplay.py',
            'carplay.py'  # In PATH
        ]
        
        for path in possible_paths:
            if os.path.exists(path) or path == 'carplay.py':
                # Check if it's in PATH
                if path == 'carplay.py':
                    result = subprocess.run(['which', 'carplay.py'], 
                                          capture_output=True)
                    if result.returncode == 0:
                        self.receiver_path = result.stdout.decode().strip()
                        break
                else:
                    self.receiver_path = path
                    break
    
    def is_available(self):
        """Check if CarPlay receiver is available"""
        return self.receiver_path is not None
    
    def start(self):
        """Start CarPlay receiver"""
        if not self.is_available():
            raise FileNotFoundError(
                "CarPlay receiver not found. See CARPLAY_SETUP.md for installation."
            )
        
        # Set up environment for window positioning
        env = os.environ.copy()
        env['CARPLAY_WIDTH'] = str(self.width)
        env['CARPLAY_HEIGHT'] = str(self.height)
        env['CARPLAY_X'] = str(self.x_offset)
        env['CARPLAY_Y'] = str(self.y_offset)
        
        # Try to use helper script first (if available)
        script_path = os.path.join(os.path.dirname(__file__), 'scripts', 'start_carplay_right.sh')
        if os.path.exists(script_path):
            try:
                self.process = subprocess.Popen(
                    ['/bin/bash', script_path],
                    env=env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
                return True
            except Exception as e:
                print(f"Error starting CarPlay receiver script: {e}")
        
        # Fallback: Start directly
        try:
            self.process = subprocess.Popen(
                ['sudo', 'python3', self.receiver_path],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            return True
        except Exception as e:
            print(f"Error starting CarPlay receiver: {e}")
            return False
    
    def stop(self):
        """Stop CarPlay receiver"""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception as e:
                print(f"Error stopping CarPlay receiver: {e}")
            finally:
                self.process = None
        
        # Also kill by process name as backup
        try:
            subprocess.Popen(['sudo', 'pkill', '-f', 'carplay.py'],
                           stdout=subprocess.DEVNULL, 
                           stderr=subprocess.DEVNULL)
        except:
            pass
    
    def is_running(self):
        """Check if CarPlay receiver is running"""
        if self.process:
            return self.process.poll() is None
        return False
