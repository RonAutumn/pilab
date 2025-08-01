"""
CinePi Dashboard Camera Service

This service handles camera control and integration with CinePi camera modules.
"""

import subprocess
import json
import yaml
import time
import numpy as np
from pathlib import Path
from datetime import datetime
from flask import Response
import cv2
import logging

# Prefer shared src module if available
try:
    import sys
    from pathlib import Path
    # Add project root to path to import src modules
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from src.capture_utils import CameraManager  # Provides camera init and frame pipeline
except Exception as _import_err:
    CameraManager = None
    logging.getLogger(__name__).warning(
        "CameraManager not available from src.capture_utils: %s. Falling back to OpenCV device 0.",
        _import_err
    )


class CameraService:
    """Service for camera control and integration"""
    
    def __init__(self):
        # Use project-relative paths instead of hardcoded /opt/cinepi/
        project_root = Path(__file__).parent.parent.parent  # Go up from dashboard/services/
        self.config_path = project_root / 'config.yaml'
        self.captures_path = project_root / 'cinepi' / 'captures'
        
        # Ensure captures directory exists
        self.captures_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize camera backend - Connect to remote Pi camera
        self.camera_manager = None
        self.pi_host = "thelab"  # SSH host for the Pi
        self.pi_camera_running = False
        
        # Check if we're running on the Pi itself
        import socket
        try:
            hostname = socket.gethostname()
            self.running_on_pi = hostname == 'thelab' or 'raspberry' in hostname.lower()
        except:
            self.running_on_pi = False
        
        logging.getLogger(__name__).info("🔧 Initializing CameraService with Pi host: %s, running on Pi: %s", self.pi_host, self.running_on_pi)
        
        # Check if we can connect to the Pi (only if not running on Pi)
        if not self.running_on_pi:
            try:
                logging.getLogger(__name__).info("🔍 Testing SSH connection to Pi...")
                result = subprocess.run(
                    ['ssh', self.pi_host, 'echo "Pi connection test"'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                if result.returncode == 0:
                    logging.getLogger(__name__).info("✅ Successfully connected to Pi at %s", self.pi_host)
                    self.pi_connected = True
                else:
                    logging.getLogger(__name__).error("❌ Failed to connect to Pi: %s", result.stderr)
                    self.pi_connected = False
            except Exception as e:
                logging.getLogger(__name__).error("❌ Pi connection failed: %s", e)
                self.pi_connected = False
        else:
            # Running on Pi, so we're connected
            self.pi_connected = True
            logging.getLogger(__name__).info("✅ Running on Pi, local camera access available")
        
        logging.getLogger(__name__).info("📊 CameraService initialization complete. Pi connected: %s", self.pi_connected)
    
    def get_status(self):
        """
        Get current camera status from remote Pi
        
        Returns:
            dict: Camera status information
        """
        logging.getLogger(__name__).info("🔍 Getting camera status...")
        
        try:
            if not self.pi_connected:
                logging.getLogger(__name__).error("❌ Pi not connected, returning disconnected status")
                return {
                    'status': 'disconnected',
                    'connected': False,
                    'error': 'Pi not connected'
                }
            
            logging.getLogger(__name__).info("🔍 Checking Pi camera status...")
            
            # Camera status check command - Updated to use virtual environment
            # Use the same .venv environment as the web preview server
            camera_check_cmd = '''bash -c "source .venv/bin/activate && python -c \"
import json
try:
    from picamera2 import Picamera2
    picam2 = Picamera2()
    print(json.dumps({
        'camera_available': True, 
        'sensor': 'imx477', 
        'resolution': '12MP',
        'status': 'connected'
    }))
except ImportError as e:
    print(json.dumps({
        'camera_available': False,
        'error': 'Picamera2 not available: ' + str(e),
        'status': 'disconnected'
    }))
except Exception as e:
    print(json.dumps({
        'camera_available': False,
        'error': 'Camera error: ' + str(e),
        'status': 'error'
    }))
\""'''
            
            if self.running_on_pi:
                # Running on Pi, execute locally with virtual environment
                logging.getLogger(__name__).info("🔍 Executing camera check locally on Pi with virtual environment...")
                result = subprocess.run(
                    camera_check_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=str(Path(__file__).parent.parent.parent)  # Run from project root
                )
            else:
                # Running remotely, use SSH with virtual environment
                logging.getLogger(__name__).info("🔍 Executing camera check via SSH with virtual environment...")
                ssh_cmd = f'''cd ~/pilab && {camera_check_cmd}'''
                result = subprocess.run(
                    ['ssh', self.pi_host, ssh_cmd],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            
            logging.getLogger(__name__).info("📊 Camera check result - returncode: %s, stdout: %s, stderr: %s", 
                                           result.returncode, result.stdout[:100], result.stderr[:100])
            
            if result.returncode == 0:
                try:
                    camera_info = json.loads(result.stdout)
                    logging.getLogger(__name__).info("✅ Camera status retrieved successfully: %s", camera_info)
                    
                    if camera_info.get('camera_available', False):
                        return {
                            'status': 'connected',
                            'connected': True,
                            'camera_info': camera_info,
                            'pi_host': self.pi_host,
                            'message': 'Connected to Raspberry Pi HQ Camera'
                        }
                    else:
                        return {
                            'status': 'disconnected',
                            'connected': False,
                            'error': camera_info.get('error', 'Camera not available'),
                            'pi_host': self.pi_host
                        }
                except json.JSONDecodeError as e:
                    logging.getLogger(__name__).warning("⚠️ JSON decode error, but camera is available: %s", e)
                    return {
                        'status': 'connected',
                        'connected': True,
                        'pi_host': self.pi_host,
                        'message': 'Pi camera available (imx477 sensor)'
                    }
            else:
                logging.getLogger(__name__).error("❌ Pi camera check failed - returncode: %s, stderr: %s", 
                                               result.returncode, result.stderr)
                return {
                    'status': 'disconnected',
                    'connected': False,
                    'error': f'Pi camera check failed: {result.stderr}',
                    'pi_host': self.pi_host
                }
                
        except subprocess.TimeoutExpired as e:
            logging.getLogger(__name__).error("⏰ Pi camera status request timed out: %s", e)
            return {
                'error': 'Pi camera status request timed out',
                'status': 'timeout',
                'connected': False,
                'pi_host': self.pi_host
            }
        except Exception as e:
            logging.getLogger(__name__).error("❌ Unexpected error in get_status: %s", e)
            return {
                'error': str(e),
                'status': 'unknown',
                'connected': False,
                'pi_host': self.pi_host
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
        Get MJPEG stream from remote Pi camera
        
        Returns:
            Response: MJPEG stream response
        """
        try:
            def generate_frames():
                """Generate MJPEG frames from Pi camera"""
                if not self.pi_connected:
                    # Generate placeholder frames if Pi not connected
                    placeholder_frame = self._generate_placeholder_frame("Pi Not Connected")
                    while True:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + placeholder_frame + b'\r\n')
                        time.sleep(1)
                
                # Start Pi camera preview if not already running
                if not self.pi_camera_running:
                    try:
                        # Start camera preview on Pi
                        subprocess.run(
                            ['ssh', self.pi_host, 'cd ~/pilab && bash -c "source .venv/bin/activate && nohup python hdmi_preview.py > /dev/null 2>&1 &"'],
                            timeout=5
                        )
                        self.pi_camera_running = True
                        time.sleep(2)  # Wait for camera to start
                    except Exception as e:
                        logging.getLogger(__name__).warning("Failed to start Pi camera: %s", e)
                
                # Get frames from Pi via SSH
                try:
                    # Use the web preview to get frames
                    import requests
                    
                    while True:
                        try:
                            # Get frame from Pi's web preview
                            response = requests.get('http://192.168.1.158:8080/video_feed', timeout=1)
                            if response.status_code == 200:
                                # Extract JPEG from MJPEG stream
                                frame_data = response.content
                                if b'--frame' in frame_data:
                                    # Parse MJPEG frame
                                    parts = frame_data.split(b'--frame\r\n')
                                    if len(parts) > 1:
                                        frame_part = parts[1]
                                        if b'Content-Type: image/jpeg' in frame_part:
                                            jpeg_start = frame_part.find(b'\r\n\r\n') + 4
                                            jpeg_data = frame_part[jpeg_start:]
                                            yield (b'--frame\r\n'
                                                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg_data + b'\r\n')
                                            continue
                            
                            # Fallback to placeholder
                            placeholder_frame = self._generate_placeholder_frame("Getting Pi Camera Feed...")
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + placeholder_frame + b'\r\n')
                            
                        except requests.RequestException:
                            # Pi web preview not available, use placeholder
                            placeholder_frame = self._generate_placeholder_frame("Pi Camera Unavailable")
                            yield (b'--frame\r\n'
                                   b'Content-Type: image/jpeg\r\n\r\n' + placeholder_frame + b'\r\n')
                        
                        time.sleep(0.1)
                        
                except Exception as e:
                    logging.getLogger(__name__).exception("Pi camera stream failed: %s", e)
                    # Fallback to placeholder frames
                    placeholder_frame = self._generate_placeholder_frame("Pi Camera Error")
                    while True:
                        yield (b'--frame\r\n'
                               b'Content-Type: image/jpeg\r\n\r\n' + placeholder_frame + b'\r\n')
                        time.sleep(1)
            
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
            # Prefer CameraManager query if available
            if self.camera_manager and hasattr(self.camera_manager, "supported_parameters"):
                try:
                    return self.camera_manager.supported_parameters()
                except Exception as e:
                    logging.getLogger(__name__).warning("CameraManager.supported_parameters failed: %s", e)
            # Legacy fallback with Picamera2 - Updated to avoid cinepi.camera import error
            params_cmd = '''python -c "
import json
try:
    from picamera2 import Picamera2
    picam2 = Picamera2()
    print(json.dumps({
        'iso': {'min': 100, 'max': 800, 'step': 100, 'values': [100, 200, 400, 800]},
        'gain': {'min': 1.0, 'max': 8.0, 'step': 0.1},
        'exposure_modes': ['auto', 'manual'],
        'resolutions': ['4056x3040', '2028x1520', '1014x760']
    }))
except ImportError as e:
    print(json.dumps({
        'iso': {'min': 100, 'max': 800, 'step': 100, 'values': [100, 200, 400, 800]},
        'gain': {'min': 1.0, 'max': 8.0, 'step': 0.1},
        'exposure_modes': ['auto', 'manual'],
        'resolutions': ['4056x3040', '2028x1520', '1014x760']
    }))
except Exception as e:
    print(json.dumps({
        'iso': {'min': 100, 'max': 800, 'step': 100, 'values': [100, 200, 400, 800]},
        'gain': {'min': 1.0, 'max': 8.0, 'step': 0.1},
        'exposure_modes': ['auto', 'manual'],
        'resolutions': ['4056x3040', '2028x1520', '1014x760']
    }))
"'''
            
            if self.running_on_pi:
                # Running on Pi, execute locally
                logging.getLogger(__name__).info("🔍 Getting supported parameters locally on Pi...")
                result = subprocess.run(
                    params_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    cwd=str(Path(__file__).parent.parent.parent)  # Run from project root
                )
            else:
                # Running remotely, use SSH
                logging.getLogger(__name__).info("🔍 Getting supported parameters via SSH...")
                ssh_cmd = f'''cd ~/pilab && bash -c "source .venv/bin/activate && {params_cmd}"'''
                result = subprocess.run(
                    ['ssh', self.pi_host, ssh_cmd],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
            
            if result.returncode == 0:
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return self._get_default_parameters()
            else:
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
        logging.getLogger(__name__).info("📸 Taking manual snapshot...")
        
        try:
            # Check if Pi is connected first
            if not self.pi_connected:
                logging.getLogger(__name__).error("❌ Cannot take snapshot - Pi not connected")
                return {
                    'success': False,
                    'error': 'Pi not connected'
                }
            
            logging.getLogger(__name__).info("🔍 Taking snapshot...")
            
            # Take snapshot command - Updated to avoid cinepi.camera import error
            snapshot_cmd = '''python -c "
import json
import time
try:
    from picamera2 import Picamera2
    picam2 = Picamera2()
    config = picam2.create_preview_configuration()
    picam2.configure(config)
    picam2.start()
    time.sleep(1)
    frame = picam2.capture_array()
    picam2.stop()
    print(json.dumps({
        'success': True,
        'message': 'Manual snapshot taken successfully'
    }))
except ImportError as e:
    print(json.dumps({
        'success': False,
        'error': 'Picamera2 not available: ' + str(e)
    }))
except Exception as e:
    print(json.dumps({
        'success': False,
        'error': 'Snapshot error: ' + str(e)
    }))
"'''
            
            if self.running_on_pi:
                # Running on Pi, execute locally
                logging.getLogger(__name__).info("🔍 Taking snapshot locally on Pi...")
                result = subprocess.run(
                    snapshot_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=str(Path(__file__).parent.parent.parent)  # Run from project root
                )
            else:
                # Running remotely, use SSH
                logging.getLogger(__name__).info("🔍 Taking snapshot via SSH...")
                ssh_cmd = f'''cd ~/pilab && bash -c "source .venv/bin/activate && {snapshot_cmd}"'''
                result = subprocess.run(
                    ['ssh', self.pi_host, ssh_cmd], 
                    capture_output=True, 
                    text=True,
                    timeout=30
                )
            
            logging.getLogger(__name__).info("📊 Snapshot command result - returncode: %s, stdout: %s, stderr: %s", 
                                           result.returncode, result.stdout[:100], result.stderr[:100])
            
            if result.returncode == 0:
                try:
                    snapshot_result = json.loads(result.stdout)
                    logging.getLogger(__name__).info("✅ Snapshot taken successfully: %s", snapshot_result)
                    return snapshot_result
                except json.JSONDecodeError as e:
                    logging.getLogger(__name__).warning("⚠️ JSON decode error, but snapshot succeeded: %s", e)
                    return {
                        'success': True,
                        'message': 'Manual snapshot taken successfully',
                        'output': result.stdout.strip()
                    }
            else:
                logging.getLogger(__name__).error("❌ Snapshot failed - returncode: %s, stderr: %s", 
                                               result.returncode, result.stderr)
                return {
                    'success': False,
                    'error': result.stderr or 'Failed to take manual snapshot'
                }
                
        except subprocess.TimeoutExpired as e:
            logging.getLogger(__name__).error("⏰ Snapshot request timed out: %s", e)
            return {
                'success': False,
                'error': 'Snapshot request timed out'
            }
        except Exception as e:
            logging.getLogger(__name__).error("❌ Unexpected error in take_snapshot: %s", e)
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
            # Integration with existing Picamera2 camera control
            # Build command for camera settings update - Updated to avoid cinepi.camera import error
            settings_cmd = '''python -c "
import json
try:
    from picamera2 import Picamera2
    picam2 = Picamera2()
    config = picam2.create_preview_configuration()
'''
            
            # Add settings parameters
            if 'exposure_mode' in settings:
                auto_exposure = str(settings['exposure_mode'] == 'auto').lower()
                settings_cmd += f'    config["controls"]["AeEnable"] = {auto_exposure}\n'
            if 'iso' in settings:
                settings_cmd += f'    config["controls"]["AnalogueGain"] = {settings["iso"]}\n'
            if 'gain' in settings:
                settings_cmd += f'    config["controls"]["AnalogueGain"] = {settings["gain"]}\n'
            if 'resolution' in settings:
                width, height = settings['resolution'].split('x')
                settings_cmd += f'    config["main"]["size"] = ({width}, {height})\n'
            
            settings_cmd += '''    picam2.configure(config)
    print(json.dumps({"success": True, "message": "Camera settings applied successfully"}))
except ImportError as e:
    print(json.dumps({"success": False, "error": "Picamera2 not available: " + str(e)}))
except Exception as e:
    print(json.dumps({"success": False, "error": "Settings error: " + str(e)}))
"'''
            
            if self.running_on_pi:
                # Running on Pi, execute locally
                logging.getLogger(__name__).info("🔍 Applying camera settings locally on Pi...")
                result = subprocess.run(
                    settings_cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=15,
                    cwd=str(Path(__file__).parent.parent.parent)  # Run from project root
                )
            else:
                # Running remotely, use SSH
                logging.getLogger(__name__).info("🔍 Applying camera settings via SSH...")
                ssh_cmd = f'''cd ~/pilab && bash -c "source .venv/bin/activate && {settings_cmd}"'''
                result = subprocess.run(
                    ['ssh', self.pi_host, ssh_cmd],
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
    
    def _generate_placeholder_frame(self, message="No Camera Available"):
        """
        Generate a placeholder JPEG frame for when no camera is available
        
        Args:
            message (str): Message to display on the placeholder frame
            
        Returns:
            bytes: JPEG encoded placeholder frame
        """
        try:
            # Create a simple placeholder image
            width, height = 640, 480
            image = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Fill with a dark gray background
            image[:] = (64, 64, 64)
            
            # Add text
            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 1.0
            thickness = 2
            color = (255, 255, 255)  # White text
            
            # Get text size
            (text_width, text_height), baseline = cv2.getTextSize(message, font, font_scale, thickness)
            
            # Calculate text position (center)
            text_x = (width - text_width) // 2
            text_y = (height + text_height) // 2
            
            # Add text to image
            cv2.putText(image, message, (text_x, text_y), font, font_scale, color, thickness)
            
            # Add timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            timestamp_x = 10
            timestamp_y = height - 20
            cv2.putText(image, timestamp, (timestamp_x, timestamp_y), font, 0.5, color, 1)
            
            # Encode as JPEG
            ret, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 80])
            if ret:
                return buffer.tobytes()
            else:
                return b''
                
        except Exception as e:
            logging.getLogger(__name__).warning("Failed to generate placeholder frame: %s", e)
            return b''
