"""
Metrics and logging utilities for CinePi timelapse system.
Handles CSV logging, performance metrics, and system monitoring.
"""

import csv
import logging
import time
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

try:
    import cv2
    import numpy as np
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    cv2 = None
    np = None

logger = logging.getLogger(__name__)


class ImageQualityMetrics:
    """Handles image quality assessment using OpenCV with error handling."""
    
    @staticmethod
    def calculate_sharpness(image_path: str) -> float:
        """
        Calculate image sharpness using Laplacian variance method with error handling.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Sharpness score (higher = sharper)
        """
        if not OPENCV_AVAILABLE:
            logger.warning("OpenCV not available for sharpness calculation")
            return 0.0
            
        try:
            # Read image and convert to grayscale
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image: {image_path}")
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calculate Laplacian variance
            laplacian = cv2.Laplacian(gray, cv2.CV_64F)
            sharpness = laplacian.var()
            
            return float(sharpness)
            
        except PermissionError as e:
            logger.error(f"Permission error calculating sharpness for {image_path}: {e}")
            return 0.0
        except OSError as e:
            logger.error(f"OS error calculating sharpness for {image_path}: {e}")
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating sharpness for {image_path}: {e}")
            return 0.0
    
    @staticmethod
    def calculate_brightness(image_path: str) -> float:
        """
        Calculate image brightness using mean pixel value with error handling.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Brightness value (0-255, higher = brighter)
        """
        if not OPENCV_AVAILABLE:
            logger.warning("OpenCV not available for brightness calculation")
            return 0.0
            
        try:
            # Read image and convert to grayscale
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"Could not read image: {image_path}")
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Calculate mean pixel value
            brightness = cv2.mean(gray)[0]
            
            return float(brightness)
            
        except PermissionError as e:
            logger.error(f"Permission error calculating brightness for {image_path}: {e}")
            return 0.0
        except OSError as e:
            logger.error(f"OS error calculating brightness for {image_path}: {e}")
            return 0.0
        except Exception as e:
            logger.error(f"Error calculating brightness for {image_path}: {e}")
            return 0.0
    
    @staticmethod
    def evaluate_image_quality(image_path: str) -> Dict[str, float]:
        """
        Comprehensive image quality assessment with error handling.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with sharpness_score and brightness_value
        """
        try:
            sharpness = ImageQualityMetrics.calculate_sharpness(image_path)
            brightness = ImageQualityMetrics.calculate_brightness(image_path)
            
            return {
                'sharpness_score': sharpness,
                'brightness_value': brightness
            }
        except Exception as e:
            logger.error(f"Error evaluating image quality for {image_path}: {e}")
            return {
                'sharpness_score': 0.0,
                'brightness_value': 0.0
            }
    
    @staticmethod
    def get_brightness_warnings(brightness: float) -> List[str]:
        """
        Get brightness warnings based on thresholds.
        
        Args:
            brightness: Brightness value (0-255)
            
        Returns:
            List of warning messages
        """
        warnings = []
        
        if brightness < 30:
            warnings.append("Image is very dark (brightness < 30)")
        elif brightness > 220:
            warnings.append("Image is very bright (brightness > 220)")
            
        return warnings


class MetricsLogger:
    """Handles logging of timelapse metrics and system performance with error handling."""
    
    def __init__(self, log_dir: str = "logs", csv_filename: str = "timelapse_metadata.csv"):
        """Initialize metrics logger with error handling."""
        self.log_dir = Path(log_dir)
        self.csv_path = self.log_dir / csv_filename
        self.csv_file = None
        self.csv_writer = None
        self.ensure_log_dir()
    
    def ensure_log_dir(self) -> None:
        """Ensure log directory exists with error handling."""
        try:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            
            # Check if we can write to the directory
            test_file = self.log_dir / ".test_write_permission"
            test_file.touch()
            test_file.unlink()
            
        except PermissionError as e:
            logger.error(f"Permission error creating log directory {self.log_dir}: {e}")
            raise
        except OSError as e:
            logger.error(f"OS error creating log directory {self.log_dir}: {e}")
            raise
        except Exception as e:
            logger.error(f"Error creating log directory {self.log_dir}: {e}")
            raise
    
    def _check_disk_space(self, min_space_mb: int = 10) -> bool:
        """Check if there's sufficient disk space for logging."""
        try:
            total, used, free = shutil.disk_usage(self.log_dir)
            free_mb = free / (1024 * 1024)
            
            if free_mb < min_space_mb:
                logger.error(f"Insufficient disk space for logging: {free_mb:.1f}MB free, {min_space_mb}MB required")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking disk space for logging: {e}")
            return False
    
    def _backup_csv_file(self) -> bool:
        """Create a backup of the CSV file before modifications."""
        try:
            if self.csv_path.exists():
                backup_path = self.csv_path.with_suffix('.csv.backup')
                shutil.copy2(self.csv_path, backup_path)
                logger.debug(f"CSV backup created: {backup_path}")
                return True
            return True
        except Exception as e:
            logger.error(f"Error creating CSV backup: {e}")
            return False
    
    def log_capture_event(self, image_path: str, metadata: Dict[str, Any]) -> bool:
        """Log a single capture event with metadata and comprehensive error handling."""
        try:
            # Check disk space before logging
            if not self._check_disk_space():
                logger.error("Insufficient disk space for logging")
                return False
            
            # Create backup before writing
            self._backup_csv_file()
            
            file_exists = self.csv_path.exists()
            
            # Use atomic write to prevent corruption
            temp_path = self.csv_path.with_suffix('.csv.tmp')
            
            with open(temp_path, 'w', newline='') as csvfile:
                fieldnames = [
                    'timestamp',
                    'image_path',
                    'filename',
                    'sharpness_score',
                    'brightness_value',
                    'brightness_warnings',
                    'file_size',
                    'resolution',
                    'exposure_time',
                    'iso',
                    'focal_length',
                    'aperture',
                    'temperature',
                    'humidity',
                    'cpu_temp',
                    'memory_usage',
                    'disk_space',
                    'capture_duration',
                    'timing_interval',
                    'timing_drift',
                    'timing_accumulated_drift',
                    'timing_system_clock_adjustments'
                ]
                
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Always write header first
                writer.writeheader()
                
                # Copy existing data if file exists
                if file_exists:
                    try:
                        with open(self.csv_path, 'r', newline='') as existing_file:
                            reader = csv.DictReader(existing_file)
                            for row in reader:
                                writer.writerow(row)
                    except Exception as e:
                        logger.error(f"Error copying existing CSV data: {e}")
                        # Continue with new data only
                
                # Extract filename from path
                filename = Path(image_path).name
                
                # Get file size if available
                file_size = 0
                try:
                    if Path(image_path).exists():
                        file_size = Path(image_path).stat().st_size
                except Exception:
                    pass
                
                row_data = {
                    'timestamp': datetime.now().isoformat(),
                    'image_path': str(image_path),
                    'filename': filename,
                    'file_size': file_size,
                    **metadata
                }
                
                writer.writerow(row_data)
            
            # Atomic move to replace original file
            temp_path.replace(self.csv_path)
            
            logger.info(f"Logged capture event: {image_path}")
            return True
            
        except PermissionError as e:
            logger.error(f"Permission error logging capture event: {e}")
            return False
        except OSError as e:
            logger.error(f"OS error logging capture event: {e}")
            return False
        except Exception as e:
            logger.error(f"Error logging capture event: {e}", exc_info=True)
            return False
    
    def append_metadata(self, log_file: str, timestamp: str, filename: str, metrics: Dict[str, Any]) -> bool:
        """
        Append metadata to CSV log file as specified in Task 5 with error handling.
        
        Args:
            log_file: Path to the log file
            timestamp: ISO format timestamp
            filename: Name of the captured image file
            metrics: Dictionary containing sharpness_score and brightness_value
        
        Returns:
            True if successful, False otherwise
        """
        try:
            log_path = Path(log_file)
            file_exists = log_path.exists()
            
            # Ensure directory exists
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Check disk space
            if not self._check_disk_space():
                logger.error("Insufficient disk space for metadata logging")
                return False
            
            # Use atomic write
            temp_path = log_path.with_suffix('.csv.tmp')
            
            with open(temp_path, 'w', newline='') as csvfile:
                fieldnames = ['timestamp', 'filename', 'sharpness_score', 'brightness_value']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Always write header first
                writer.writeheader()
                
                # Copy existing data if file exists
                if file_exists:
                    try:
                        with open(log_path, 'r', newline='') as existing_file:
                            reader = csv.DictReader(existing_file)
                            for row in reader:
                                writer.writerow(row)
                    except Exception as e:
                        logger.error(f"Error copying existing metadata: {e}")
                
                row_data = {
                    'timestamp': timestamp,
                    'filename': filename,
                    'sharpness_score': metrics.get('sharpness_score', 0.0),
                    'brightness_value': metrics.get('brightness_value', 0.0)
                }
                
                writer.writerow(row_data)
            
            # Atomic move
            temp_path.replace(log_path)
            
            return True
            
        except PermissionError as e:
            logger.error(f"Permission error appending metadata: {e}")
            return False
        except OSError as e:
            logger.error(f"OS error appending metadata: {e}")
            return False
        except Exception as e:
            logger.error(f"Error appending metadata: {e}")
            return False
    
    def get_capture_stats(self) -> Dict[str, Any]:
        """Get statistics about captured images with error handling."""
        try:
            if not self.csv_path.exists():
                return {"total_captures": 0, "first_capture": None, "last_capture": None}
            
            with open(self.csv_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                
            if not rows:
                return {"total_captures": 0, "first_capture": None, "last_capture": None}
            
            # Calculate additional statistics
            sharpness_scores = [float(row.get('sharpness_score', 0)) for row in rows if row.get('sharpness_score')]
            brightness_values = [float(row.get('brightness_value', 0)) for row in rows if row.get('brightness_value')]
            
            stats = {
                "total_captures": len(rows),
                "first_capture": rows[0]['timestamp'],
                "last_capture": rows[-1]['timestamp'],
                "average_file_size": sum(float(row.get('file_size', 0)) for row in rows) / len(rows),
                "average_sharpness": sum(sharpness_scores) / len(sharpness_scores) if sharpness_scores else 0.0,
                "average_brightness": sum(brightness_values) / len(brightness_values) if brightness_values else 0.0,
                "min_sharpness": min(sharpness_scores) if sharpness_scores else 0.0,
                "max_sharpness": max(sharpness_scores) if sharpness_scores else 0.0,
                "min_brightness": min(brightness_values) if brightness_values else 0.0,
                "max_brightness": max(brightness_values) if brightness_values else 0.0
            }
            
            return stats
            
        except PermissionError as e:
            logger.error(f"Permission error getting capture stats: {e}")
            return {"total_captures": 0, "error": f"Permission error: {e}"}
        except OSError as e:
            logger.error(f"OS error getting capture stats: {e}")
            return {"total_captures": 0, "error": f"OS error: {e}"}
        except Exception as e:
            logger.error(f"Error getting capture stats: {e}")
            return {"total_captures": 0, "error": str(e)}
    
    def log_system_metrics(self) -> Dict[str, Any]:
        """Log current system metrics with error handling."""
        try:
            # TODO: Implement actual system metrics collection
            metrics = {
                'cpu_temp': 0.0,  # Placeholder
                'memory_usage': 0.0,  # Placeholder
                'disk_space': 0.0,  # Placeholder
                'uptime': time.time()
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
            return {}
    
    def cleanup(self) -> None:
        """Clean up resources and ensure data integrity."""
        try:
            logger.info("Cleaning up metrics logger...")
            
            # Close any open file handles
            if self.csv_file:
                self.csv_file.close()
                self.csv_file = None
            
            # Ensure CSV file is properly written
            if self.csv_path.exists():
                # Verify file integrity
                try:
                    with open(self.csv_path, 'r') as f:
                        # Try to read the file to ensure it's not corrupted
                        f.read()
                    logger.info("CSV file integrity verified")
                except Exception as e:
                    logger.error(f"CSV file integrity check failed: {e}")
            
            logger.info("Metrics logger cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during metrics logger cleanup: {e}")
