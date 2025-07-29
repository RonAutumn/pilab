"""
Configuration management for CinePi timelapse system.
Handles YAML configuration files, validation, and runtime settings.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)


class ConfigValidationError(Exception):
    """Custom exception for configuration validation errors."""
    pass


class ConfigManager:
    """Manages configuration settings for the timelapse system."""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize configuration manager."""
        self.config_path = Path(config_path)
        self.config = {}
        self.load_config()
    
    def load_config(self) -> bool:
        """Load configuration from YAML file."""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as file:
                    self.config = yaml.safe_load(file) or {}
                logger.info(f"Configuration loaded from {self.config_path}")
                return True
            else:
                logger.warning(f"Configuration file {self.config_path} not found")
                return self.create_default_config()
        except Exception as e:
            logger.error(f"Error loading configuration: {e}")
            return False
    
    def create_default_config(self) -> bool:
        """Create default configuration file."""
        default_config = {
            'camera': {
                'resolution': [4056, 3040],
                'quality': 95,
                'exposure_mode': 'auto',
                'iso': 100,
                'shutter_speed': 0,
                'awb_mode': 'auto'
            },
            'timelapse': {
                'interval_seconds': 30,
                'duration_hours': 24,
                'output_dir': 'output/images',
                'filename_prefix': 'timelapse',
                'image_format': 'jpg',
                'add_timestamp': True,
                'create_daily_dirs': True
            },
            'logging': {
                'log_dir': 'logs',
                'log_level': 'INFO',
                'csv_filename': 'timelapse_metadata.csv'
            }
        }
        
        try:
            with open(self.config_path, 'w') as file:
                yaml.dump(default_config, file, default_flow_style=False)
            self.config = default_config
            logger.info(f"Default configuration created at {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error creating default configuration: {e}")
            return False
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key (supports dot notation)."""
        keys = key.split('.')
        value = self.config
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value by key (supports dot notation)."""
        keys = key.split('.')
        config = self.config
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
        return True
    
    def validate_config(self) -> bool:
        """Validate configuration settings with comprehensive checks."""
        try:
            errors = []
            
            # Validate camera settings
            errors.extend(self._validate_camera_settings())
            
            # Validate timelapse settings
            errors.extend(self._validate_timelapse_settings())
            
            # Validate logging settings
            errors.extend(self._validate_logging_settings())
            
            # If there are errors, log them and return False
            if errors:
                for error in errors:
                    logger.error(f"Configuration validation error: {error}")
                return False
            
            logger.info("Configuration validation passed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error during configuration validation: {e}")
            return False
    
    def _validate_camera_settings(self) -> List[str]:
        """Validate camera configuration settings."""
        errors = []
        
        # Validate resolution
        resolution = self.get('camera.resolution')
        if not self._validate_resolution(resolution):
            errors.append("camera.resolution must be a list of two positive integers [width, height]")
        
        # Validate quality
        quality = self.get('camera.quality', 95)
        if not isinstance(quality, int) or quality < 1 or quality > 100:
            errors.append("camera.quality must be an integer between 1 and 100")
        
        # Validate ISO
        iso = self.get('camera.iso', 100)
        valid_iso_values = [100, 200, 400, 800, 1600, 3200]
        if not isinstance(iso, int) or iso not in valid_iso_values:
            errors.append(f"camera.iso must be one of: {valid_iso_values}")
        
        # Validate shutter speed
        shutter_speed = self.get('camera.shutter_speed', 0)
        if not isinstance(shutter_speed, int) or shutter_speed < 0:
            errors.append("camera.shutter_speed must be a non-negative integer (microseconds)")
        
        # Validate exposure mode
        exposure_mode = self.get('camera.exposure_mode', 'auto')
        valid_exposure_modes = [
            'auto', 'night', 'backlight', 'spotlight', 'sports', 
            'snow', 'beach', 'verylong', 'fixedfps', 'antishake', 'fireworks'
        ]
        if not isinstance(exposure_mode, str) or exposure_mode not in valid_exposure_modes:
            errors.append(f"camera.exposure_mode must be one of: {valid_exposure_modes}")
        
        # Validate AWB mode
        awb_mode = self.get('camera.awb_mode', 'auto')
        valid_awb_modes = [
            'auto', 'sunlight', 'cloudy', 'shade', 'tungsten', 
            'fluorescent', 'incandescent', 'flash', 'horizon'
        ]
        if not isinstance(awb_mode, str) or awb_mode not in valid_awb_modes:
            errors.append(f"camera.awb_mode must be one of: {valid_awb_modes}")
        
        return errors
    
    def _validate_timelapse_settings(self) -> List[str]:
        """Validate timelapse configuration settings."""
        errors = []
        
        # Validate interval_seconds
        interval = self.get('timelapse.interval_seconds', 30)
        if not isinstance(interval, int) or interval < 1:
            errors.append("timelapse.interval_seconds must be a positive integer >= 1")
        
        # Validate duration_hours
        duration = self.get('timelapse.duration_hours', 24)
        if not isinstance(duration, (int, float)) or duration < 0:
            errors.append("timelapse.duration_hours must be a non-negative number (0 = indefinite)")
        
        # Validate output_dir
        output_dir = self.get('timelapse.output_dir', 'output/images')
        if not isinstance(output_dir, str) or not output_dir.strip():
            errors.append("timelapse.output_dir must be a non-empty string")
        
        # Validate filename_prefix
        filename_prefix = self.get('timelapse.filename_prefix', 'timelapse')
        if not isinstance(filename_prefix, str) or not filename_prefix.strip():
            errors.append("timelapse.filename_prefix must be a non-empty string")
        
        # Validate image_format
        image_format = self.get('timelapse.image_format', 'jpg')
        valid_formats = ['jpg', 'jpeg', 'png', 'bmp']
        if not isinstance(image_format, str) or image_format.lower() not in valid_formats:
            errors.append(f"timelapse.image_format must be one of: {valid_formats}")
        
        # Validate add_timestamp
        add_timestamp = self.get('timelapse.add_timestamp', True)
        if not isinstance(add_timestamp, bool):
            errors.append("timelapse.add_timestamp must be a boolean (true/false)")
        
        # Validate create_daily_dirs
        create_daily_dirs = self.get('timelapse.create_daily_dirs', True)
        if not isinstance(create_daily_dirs, bool):
            errors.append("timelapse.create_daily_dirs must be a boolean (true/false)")
        
        return errors
    
    def _validate_logging_settings(self) -> List[str]:
        """Validate logging configuration settings."""
        errors = []
        
        # Validate log_level
        log_level = self.get('logging.log_level', 'INFO')
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if not isinstance(log_level, str) or log_level.upper() not in valid_log_levels:
            errors.append(f"logging.log_level must be one of: {valid_log_levels}")
        
        # Validate log_dir
        log_dir = self.get('logging.log_dir', 'logs')
        if not isinstance(log_dir, str) or not log_dir.strip():
            errors.append("logging.log_dir must be a non-empty string")
        
        # Validate csv_filename
        csv_filename = self.get('logging.csv_filename', 'timelapse_metadata.csv')
        if not isinstance(csv_filename, str) or not csv_filename.strip():
            errors.append("logging.csv_filename must be a non-empty string")
        
        return errors
    
    def _validate_resolution(self, resolution: Any) -> bool:
        """Validate resolution setting."""
        if not isinstance(resolution, list) or len(resolution) != 2:
            return False
        
        width, height = resolution
        if not isinstance(width, int) or not isinstance(height, int):
            return False
        
        if width <= 0 or height <= 0:
            return False
        
        # Check for reasonable resolution limits
        if width > 10000 or height > 10000:
            return False
        
        return True
    
    def get_validation_errors(self) -> List[str]:
        """Get a list of all configuration validation errors."""
        errors = []
        
        # Validate camera settings
        errors.extend(self._validate_camera_settings())
        
        # Validate timelapse settings
        errors.extend(self._validate_timelapse_settings())
        
        # Validate logging settings
        errors.extend(self._validate_logging_settings())
        
        return errors
    
    def print_validation_report(self) -> None:
        """Print a detailed validation report."""
        errors = self.get_validation_errors()
        
        if not errors:
            print("✅ Configuration validation passed successfully!")
            return
        
        print("❌ Configuration validation failed with the following errors:")
        print()
        for i, error in enumerate(errors, 1):
            print(f"  {i}. {error}")
        print()
        print("Please fix these errors in your config.yaml file.")
    
    def save_config(self) -> bool:
        """Save current configuration to file."""
        try:
            with open(self.config_path, 'w') as file:
                yaml.dump(self.config, file, default_flow_style=False)
            logger.info(f"Configuration saved to {self.config_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
            return False
