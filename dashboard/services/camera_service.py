"""
CinePi Dashboard Camera Service

This service handles camera control and integration with CinePi camera modules.
"""

import subprocess
import json
import yaml
from pathlib import Path
from datetime import datetime
from flask import Response
import cv2


class CameraService:
    """Service for camera control and integration"""
    
    def __init__(self):
        self.config_path = Path('/opt/cinepi/config/cinepi.yaml')
        self.captures_path = Path('/opt/cinepi/captures')
    
    def get_status(self):
        """
        Get current camera status
        
        Returns:
            dict: Camera status information
        """
        try:
            # Integration with existing CinePi camera module
            result = subprocess.run(
                ['python3', '-m', 'cinepi.camera', 'status'], 
                capture_output=True, 
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {
                        'status': 'connected',
                        'connected': True,
                        'message': result.stdout.strip()
                    }
            else:
                return {
                    'error': result.stderr or 'Camera status check failed',
                    'status': 'unknown',
                    'connected': False
                }
                
        except subprocess.TimeoutExpired:
            return {
                'error': 'Camera status request timed out',
                'status': 'timeout',
                'connected': False
            }
        except Exception as e:
            return {
                'error': str(e),
                'status': 'unknown',
                'connected': False
            }
    
    def get_settings(self):
        """
        Get current camera settings
        
        Returns:
            dict: Camera settings
        """
        try:
            # Load from existing CinePi config
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if config is None:
                        config = {}
                    camera_settings = config.get('camera', {})
                    
                    # Ensure all required settings are present
                    default_settings = {
                        'exposure': 'auto',
                        'iso': 400,
                        'resolution': '4056x3040',
                        'gain': 2.0
                    }
                    
                    # Merge with defaults
                    for key, value in default_settings.items():
                        if key not in camera_settings:
                            camera_settings[key] = value
                    
                    return camera_settings
            else:
                return {
                    'exposure': 'auto',
                    'iso': 400,
                    'resolution': '4056x3040',
                    'gain': 2.0
                }
        except Exception as e:
            return {
                'error': str(e),
                'exposure': 'auto',
                'iso': 400,
                'resolution': '4056x3040',
                'gain': 2.0
            }
    
    def update_settings(self, new_settings):
        """
        Update camera settings
        
        Args:
            new_settings (dict): New camera settings
        
        Returns:
            dict: Operation result
        """
        try:
            # Load current config
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    config = yaml.safe_load(f)
                    if config is None:
                        config = {}
            else:
                config = {}
            
            # Update camera settings
            if 'camera' not in config:
                config['camera'] = {}
            
            config['camera'].update(new_settings)
            
            # Save updated config
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            # Apply settings to camera
            apply_result = self._apply_camera_settings(new_settings)
            
            if apply_result.get('success', False):
                return {
                    'success': True,
                    'message': 'Settings updated successfully',
                    'settings': new_settings
                }
            else:
                return {
                    'success': False,
                    'error': apply_result.get('error', 'Failed to apply camera settings'),
                    'settings': new_settings
                }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_mjpeg_stream(self):
        """
        Get MJPEG stream response
        
        Returns:
            Response: MJPEG stream response
        """
        try:
            def generate_frames():
                """Generate MJPEG frames"""
                # Use existing CinePi camera stream or fallback to OpenCV
                try:
                    # Try to use CinePi camera stream
                    cap = cv2.VideoCapture(0)  # Or CinePi camera instance
                    
                    while True:
                        ret, frame = cap.read()
                        if not ret:
                            break
                        
                        # Convert frame to JPEG
                        ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                        if not ret:
                            continue
                        
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
                               
                except Exception as e:
                    # Fallback: return a placeholder image or error
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + b'\r\n')
            
            return Response(
                generate_frames(),
                mimetype='multipart/x-mixed-replace; boundary=frame'
            )
            
        except Exception as e:
            return Response(
                f'Error: {str(e)}',
                status=500,
                mimetype='text/plain'
            )
    
    def get_supported_parameters(self):
        """
        Get supported camera parameters and ranges
        
        Returns:
            dict: Supported parameters with ranges and options
        """
        try:
            # Query camera for supported parameters
            result = subprocess.run(
                ['python3', '-m', 'cinepi.camera', 'parameters'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    # Fallback to default parameters
                    return self._get_default_parameters()
            else:
                # Fallback to default parameters
                return self._get_default_parameters()
                
        except Exception as e:
            # Fallback to default parameters
            return self._get_default_parameters()
    
    def _get_default_parameters(self):
        """
        Get default supported parameters when camera query fails
        
        Returns:
            dict: Default supported parameters
        """
        return {
            'iso': {
                'min': 100,
                'max': 800,
                'step': 100,
                'values': [100, 200, 400, 800]
            },
            'gain': {
                'min': 1.0,
                'max': 8.0,
                'step': 0.1
            },
            'exposure_modes': ['auto', 'manual'],
            'resolutions': [
                '4056x3040',
                '2028x1520',
                '1014x760'
            ]
        }
    
    def take_snapshot(self):
        """
        Take manual snapshot
        
        Returns:
            dict: Snapshot result
        """
        try:
            # Integration with existing CinePi capture module
            result = subprocess.run(
                ['python3', '-m', 'cinepi.capture', 'manual'], 
                capture_output=True, 
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return {
                        'success': True,
                        'message': 'Manual snapshot taken successfully',
                        'output': result.stdout.strip()
                    }
            else:
                return {
                    'success': False,
                    'error': result.stderr or 'Failed to take manual snapshot'
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Snapshot request timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _apply_camera_settings(self, settings):
        """
        Apply settings to camera hardware
        
        Args:
            settings (dict): Camera settings to apply
        
        Returns:
            dict: Operation result
        """
        try:
            # Integration with existing CinePi camera control
            # Build command for camera settings update
            command = ['python3', '-m', 'cinepi.camera', 'settings']
            
            # Add settings parameters
            if 'exposure_mode' in settings:
                command.extend(['--exposure', settings['exposure_mode']])
            if 'iso' in settings:
                command.extend(['--iso', str(settings['iso'])])
            if 'gain' in settings:
                command.extend(['--gain', str(settings['gain'])])
            if 'resolution' in settings:
                command.extend(['--resolution', settings['resolution']])
            
            # Execute camera settings command
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                timeout=15
            )
            
            if result.returncode == 0:
                return {
                    'success': True,
                    'message': 'Camera settings applied successfully',
                    'output': result.stdout.strip()
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or 'Failed to apply camera settings',
                    'output': result.stdout.strip()
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Camera settings application timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error applying camera settings: {e}'
            } 