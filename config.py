"""
Configuration management for Sambar HUD
"""

import os
import yaml
from pathlib import Path

class Config:
    """Configuration manager"""
    
    def __init__(self, config_file=None):
        if config_file is None:
            config_file = Path(__file__).parent / "config.yaml"
        
        self.config_file = Path(config_file)
        self.config = self.load_config()
        
    def load_config(self):
        """Load configuration from YAML file or use defaults"""
        default_config = {
            'screen_width': 2560,
            'screen_height': 720,
            'carplay': {
                'enabled': True,
                'port': 8080,
                'auto_connect': True,
                'livi_auto_launch': True,  # Auto-open LIVI on startup and position on right half (Pi)
                'livi_use_xephyr': True,   # Run LIVI in a Xephyr frame (right-half size); no floating window
            },
            'entertainment': {
                'steam_link_enabled': True,
                'youtube_enabled': True,
                'netflix_enabled': True,
                'airplay_enabled': True,
                'default_mode': 'steam_link'  # steam_link, youtube, netflix, airplay
            },
            'kiosk_mode': {
                'enabled': True,
                'auto_start': True
            },
            'performance': {
                'low_power_mode': False,
                'gpu_mem': 128  # MB for Raspberry Pi GPU memory split
            }
        }
        
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    user_config = yaml.safe_load(f) or {}
                # Merge with defaults
                default_config.update(user_config)
            except Exception as e:
                print(f"Warning: Could not load config file: {e}")
                print("Using default configuration")
        
        return default_config
    
    def get(self, key, default=None):
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value if value is not None else default
    
    def set(self, key, value):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
    
    def save(self):
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
        except Exception as e:
            print(f"Error saving config: {e}")
