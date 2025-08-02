"""
Camera capture utilities for CinePi timelapse system.
Handles camera initialization, image capture, and camera settings using Picamera2.
"""

import logging
import os
import shutil
from typing import Optional, Tuple, Dict, Any
from pathlib import Path
from datetime import datetime

try:
    from picamera2 import Picamera2
    from libcamera import controls
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False
    Picamera2 = None
    controls = None

from config_manager import ConfigManager

logger = logging.getLogger(__name__)


def _sanitize_tag(tag: Optional[str]) -> Optional[str]:
    """Sanitize a tag to allow only [A-Za-z0-9_-]; replace others with '_'."""
    if tag is None:
        return None
    import re
    sanitized = re.sub(r'[^A-Za-z0-9_-]+', '_', tag.strip())
    return sanitized or None


def _build_capture_dir(root: Path, ts: datetime, tag: Optional[str]) -> Path:
    """Build directory path as root/YYYY-MM-DD or root/YYYY-MM-DD_<tag>."""
    date_part = ts.strftime('%Y-%m-%d')
    tag_sanitized = _sanitize_tag(tag)
    folder = f"{date_part}_{tag_sanitized}" if tag_sanitized else date_part
    return root / folder


def save_capture(image, *, root: Path, tag: Optional[str], ts: datetime) -> Path:
    """
    Save an image to disk under ./captures/YYYY-MM-DD[/_tag]/HHMMSS_microsec.jpg.

    - image: either a numpy ndarray or raw bytes for an already-encoded JPEG/PNG.
    - root: base directory (default typically Path('./captures')).
    - tag: optional test name for suffixing the day folder.
    - ts: timestamp used for folder and filename.

    Returns: Path to the saved file. Raises IOError/OSError on failure.
    """
    try:
        import numpy as np
        from PIL import Image
        base_dir = _build_capture_dir(root, ts, tag)
        base_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{ts.strftime('%H%M%S_%f')}.jpg"
        out_path = base_dir / filename

        # If ndarray, encode via PIL
        if 'numpy' in str(type(image)) or isinstance(image, getattr(np, 'ndarray', tuple())):
            img = Image.fromarray(image)
            img.save(str(out_path), 'JPEG', quality=95, optimize=True)
        elif isinstance(image, (bytes, bytearray)):
            # Assume already-encoded bytes (e.g., JPEG). Write directly.
            with open(out_path, 'wb') as f:
                f.write(image)
        else:
            # Unknown type; try PIL open/save fallback if possible
            try:
                img = Image.fromarray(image)  # may raise
                img.save(str(out_path), 'JPEG', quality=95, optimize=True)
            except Exception as e:
                raise IOError(f"Unsupported image type for save_capture: {type(image)}") from e

        return out_path
    except PermissionError as e:
        raise
    except OSError as e:
        raise
    except Exception as e:
        raise IOError(f"Failed to save capture: {e}") from e


class CameraManager:
    """Manages camera operations for timelapse photography using Picamera2."""
    
    def __init__(self, config_manager: ConfigManager):
        """Initialize camera manager with configuration."""
        self.config = config_manager
        self.camera: Optional[Picamera2] = None
        self.is_initialized = False
        self.current_config = {}
        
    def initialize_camera(self) -> bool:
        """Initialize the camera with optimal settings for timelapse."""
        if not PICAMERA_AVAILABLE:
            logger.warning("Picamera2 library not available - using mock camera for testing")
            self.is_initialized = True
            return True
            
        try:
            logger.info("Initializing camera...")
            self.camera = Picamera2()
            
            # Get camera configuration from YAML
            camera_config = self.config.get('camera', {})
            timelapse_config = self.config.get('timelapse', {})
            
            # Configure camera settings
            resolution = tuple(camera_config.get('resolution', [4056, 3040]))
            quality = camera_config.get('quality', 95)
            
            # Create basic still capture configuration - no presets
            camera_config_dict = self.camera.create_still_configuration(
                main={"size": resolution},
                buffer_count=2
            )
            
            # Configure camera
            self.camera.configure(camera_config_dict)
            
            # Apply camera settings
            self._apply_camera_settings(camera_config)
            
            # Start camera
            self.camera.start()
            self.is_initialized = True
            
            logger.info(f"Camera initialized successfully with resolution {resolution}")
            return True
            
        except PermissionError as e:
            logger.error(f"Permission error initializing camera: {e}")
            self.is_initialized = False
            return False
        except OSError as e:
            logger.error(f"OS error initializing camera: {e}")
            self.is_initialized = False
            return False
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}", exc_info=True)
            self.is_initialized = False
            return False
    
    def _apply_camera_settings(self, camera_config: Dict[str, Any]) -> None:
        """Apply camera settings from configuration with error handling."""
        if not self.camera:
            return
            
        try:
            # Use camera defaults - no custom settings
            logger.info("Using camera defaults - no custom settings applied")
                    
        except Exception as e:
            logger.warning(f"Could not apply camera settings: {e}")
    
    def _check_disk_space(self, filename: str, min_space_mb: int = 50) -> bool:
        """Check if there's sufficient disk space for the image."""
        try:
            output_path = Path(filename)
            total, used, free = shutil.disk_usage(output_path.parent)
            free_mb = free / (1024 * 1024)
            
            if free_mb < min_space_mb:
                logger.error(f"Insufficient disk space: {free_mb:.1f}MB free, {min_space_mb}MB required")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking disk space: {e}")
            return False
    
    def _check_file_permissions(self, filename: str) -> bool:
        """Check if we have write permissions to the output directory."""
        try:
            output_path = Path(filename)
            test_file = output_path.parent / ".test_write_permission"
            test_file.touch()
            test_file.unlink()
            return True
        except (PermissionError, OSError) as e:
            logger.error(f"Permission error in output directory {output_path.parent}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error checking file permissions: {e}")
            return False
    
    def capture_image(self, filename: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """Capture a single image and save to specified filename with comprehensive error handling."""
        if not self.is_initialized:
            logger.error("Camera not initialized")
            return False
        
        # Check disk space and permissions before capture
        if not self._check_disk_space(filename):
            return False
        
        if not self._check_file_permissions(filename):
            return False
            
        # Handle mock camera when Picamera2 is not available
        if not PICAMERA_AVAILABLE:
            return self._capture_mock_image(filename)
            
        try:
            # Ensure output directory exists
            output_path = Path(filename)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Capture image directly to file for better color accuracy
            logger.info(f"Capturing image: {filename}")
            
            # Determine storage root and optional tag from config
            storage_cfg = self.config.get('storage', {}) if hasattr(self.config, 'get') else {}
            root_str = storage_cfg.get('root', './captures')
            tag = storage_cfg.get('tag', None)
            root_path = Path(root_str)

            # Create timestamp and build path
            ts = datetime.now()
            base_dir = _build_capture_dir(root_path, ts, tag)
            base_dir.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            filename = f"{ts.strftime('%H%M%S_%f')}.jpg"
            out_path = base_dir / filename
            
            # Capture image directly to file - no color conversions
            self.camera.capture_file(str(out_path))
            
            saved_path = out_path

            logger.info(f"Image saved successfully: {saved_path}")
            return True
            
        except PermissionError as e:
            logger.error(f"Permission error during capture: {e}")
            return False
        except OSError as e:
            logger.error(f"OS error during capture: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to capture image: {e}", exc_info=True)
            return False
    
    def _capture_mock_image(self, filename: str) -> bool:
        """Create a mock image for testing when camera is not available."""
        try:
            # Create a mock image for testing
            from PIL import Image
            import numpy as np
            
            # Ensure output directory exists
            output_path = Path(filename)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Create a simple test image
            width, height = 640, 480
            mock_image = np.random.randint(0, 255, (height, width, 3), dtype=np.uint8)
            img = Image.fromarray(mock_image)
            
            # Save with appropriate format
            if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
                img.save(filename, 'JPEG', quality=95, optimize=True)
            elif filename.lower().endswith('.png'):
                img.save(filename, 'PNG', optimize=True)
            elif filename.lower().endswith('.bmp'):
                img.save(filename, 'BMP')
            else:
                # Default to JPEG
                filename = f"{filename}.jpg"
                img.save(filename, 'JPEG', quality=95, optimize=True)
            
            logger.info(f"Mock image saved: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create mock image: {e}")
            return False
    
    def _save_image(self, image, filename: str) -> bool:
        """Save captured image with error handling."""
        try:
            from PIL import Image
            img = Image.fromarray(image)
            
            # Get quality setting from config
            quality = self.config.get('camera', {}).get('quality', 95)
            
            # Save with appropriate format
            if filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
                img.save(filename, 'JPEG', quality=quality, optimize=True)
            elif filename.lower().endswith('.png'):
                img.save(filename, 'PNG', optimize=True)
            elif filename.lower().endswith('.bmp'):
                img.save(filename, 'BMP')
            else:
                # Default to JPEG
                filename = f"{filename}.jpg"
                img.save(filename, 'JPEG', quality=quality, optimize=True)
            
            logger.info(f"Image saved successfully: {filename}")
            return True
            
        except PermissionError as e:
            logger.error(f"Permission error saving image: {e}")
            return False
        except OSError as e:
            logger.error(f"OS error saving image: {e}")
            return False
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            return False
    
    def get_camera_info(self) -> Dict[str, Any]:
        """Get camera information and current settings with error handling."""
        if not self.camera:
            return {"error": "Camera not initialized"}
            
        try:
            info = {
                "camera_model": "Raspberry Pi HQ Camera",
                "resolution": self.camera.camera_properties.get("PixelArraySize", "Unknown"),
                "sensor_mode": self.camera.camera_properties.get("SensorMode", "Unknown"),
                "is_initialized": self.is_initialized
            }
            
            # Add current settings
            controls = self.camera.capture_metadata()
            if controls:
                info.update({
                    "iso": controls.get("AnalogueGain", 0) * 100,
                    "exposure_time": controls.get("ExposureTime", 0),
                    "awb_mode": controls.get("AwbMode", "Unknown")
                })
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting camera info: {e}")
            return {"error": str(e)}
    
    def cleanup(self) -> None:
        """Clean up camera resources with comprehensive error handling."""
        if self.camera:
            try:
                logger.info("Starting camera cleanup...")
                
                # Stop camera operations
                if self.camera.started:
                    self.camera.stop()
                    logger.info("Camera stopped successfully")
                
                # Close camera
                self.camera.close()
                logger.info("Camera closed successfully")
                
                # Reset state
                self.is_initialized = False
                self.camera = None
                
                logger.info("Camera cleanup completed successfully")
                
            except PermissionError as e:
                logger.error(f"Permission error during camera cleanup: {e}")
            except OSError as e:
                logger.error(f"OS error during camera cleanup: {e}")
            except Exception as e:
                logger.error(f"Error during camera cleanup: {e}", exc_info=True)
        else:
            logger.info("No camera to cleanup")


class ImageProcessor:
    """Handles image processing and quality metrics with error handling."""
    
    def __init__(self):
        """Initialize image processor."""
        pass
    
    def calculate_sharpness(self, image_path: str) -> float:
        """Calculate image sharpness using Laplacian variance with error handling."""
        try:
            import cv2
            import numpy as np
            
            # Read image in grayscale
            image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if image is None:
                logger.error(f"Could not read image: {image_path}")
                return 0.0
            
            # Calculate Laplacian variance
            laplacian = cv2.Laplacian(image, cv2.CV_64F)
            variance = laplacian.var()
            
            return variance
            
        except ImportError:
            logger.warning("OpenCV not available for sharpness calculation")
            return 0.0
        except PermissionError as e:
            logger.error(f"Permission error reading image for sharpness: {e}")
            return 0.0
        except OSError as e:
            logger.error(f"OS error reading image for sharpness: {e}")
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating sharpness: {e}")
            return 0.0
    
    def check_exposure_quality(self, image_path: str) -> Dict[str, float]:
        """Analyze exposure quality metrics with error handling."""
        try:
            import cv2
            import numpy as np
            
            # Read image
            image = cv2.imread(image_path)
            if image is None:
                return {"error": "Could not read image"}
            
            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calculate histogram
            hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
            hist = hist.flatten()
            
            # Calculate exposure metrics
            mean_brightness = np.mean(gray)
            std_brightness = np.std(gray)
            
            # Check for over/under exposure
            overexposed_pixels = np.sum(gray > 250) / gray.size * 100
            underexposed_pixels = np.sum(gray < 5) / gray.size * 100
            
            return {
                "mean_brightness": float(mean_brightness),
                "std_brightness": float(std_brightness),
                "overexposed_percent": float(overexposed_pixels),
                "underexposed_percent": float(underexposed_pixels),
                "dynamic_range": float(np.max(gray) - np.min(gray))
            }
            
        except ImportError:
            logger.warning("OpenCV not available for exposure analysis")
            return {"error": "OpenCV not available"}
        except PermissionError as e:
            logger.error(f"Permission error reading image for exposure analysis: {e}")
            return {"error": f"Permission error: {e}"}
        except OSError as e:
            logger.error(f"OS error reading image for exposure analysis: {e}")
            return {"error": f"OS error: {e}"}
        except Exception as e:
            logger.error(f"Error analyzing exposure: {e}")
            return {"error": str(e)}
