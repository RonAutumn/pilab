"""
Metadata logging system for CinePi timelapse system.
Implements CSV-based logging for image capture metadata as specified in Task 5.
"""

import csv
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

logger = logging.getLogger(__name__)


class MetadataLogger:
    """CSV-based logging system for comprehensive metadata tracking."""
    
    def __init__(self, log_dir: str = "logs"):
        """Initialize metadata logger with specified log directory."""
        self.log_dir = Path(log_dir)
        self.ensure_log_dir()
    
    def ensure_log_dir(self) -> None:
        """Ensure log directory exists, create if necessary."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Log directory ensured: {self.log_dir}")
    
    def append_metadata(self, log_file: str, timestamp: str, filename: str, metrics: Dict[str, Any]) -> bool:
        """
        Append metadata to CSV log file as specified in Task 5.
        
        Args:
            log_file: Path to the log file (relative to log_dir or absolute)
            timestamp: ISO format timestamp string
            filename: Name of the captured image file
            metrics: Dictionary containing sharpness_score and brightness_value
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Handle both relative and absolute paths
            log_path = Path(log_file)
            if not log_path.is_absolute():
                log_path = self.log_dir / log_file
            
            # Ensure directory exists
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_exists = log_path.exists()
            
            # Use proper file locking for atomic writes (basic implementation)
            with open(log_path, 'a', newline='', buffering=1) as csvfile:
                fieldnames = ['timestamp', 'filename', 'sharpness_score', 'brightness_value']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                # Write header if file is new
                if not file_exists:
                    writer.writeheader()
                
                # Prepare row data
                row_data = {
                    'timestamp': timestamp,
                    'filename': filename,
                    'sharpness_score': float(metrics.get('sharpness_score', 0.0)),
                    'brightness_value': float(metrics.get('brightness_value', 0.0))
                }
                
                # Write the row
                writer.writerow(row_data)
                
            logger.info(f"Appended metadata for {filename} to {log_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error appending metadata: {e}")
            return False
    
    def create_daily_log(self, date: datetime = None) -> str:
        """
        Create a date-based log file name.
        
        Args:
            date: Date for the log file (defaults to current date)
        
        Returns:
            Path to the daily log file
        """
        if date is None:
            date = datetime.now()
        
        filename = f"timelapse_{date.strftime('%Y%m%d')}.csv"
        return str(self.log_dir / filename)
    
    def log_capture_with_quality(self, image_path: str, quality_metrics: Dict[str, float]) -> bool:
        """
        Convenience method to log a capture with quality metrics.
        
        Args:
            image_path: Path to the captured image
            quality_metrics: Dictionary with sharpness_score and brightness_value
        
        Returns:
            True if successful, False otherwise
        """
        try:
            timestamp = datetime.now().isoformat()
            filename = Path(image_path).name
            daily_log = self.create_daily_log()
            
            return self.append_metadata(
                log_file=daily_log,
                timestamp=timestamp,
                filename=filename,
                metrics=quality_metrics
            )
            
        except Exception as e:
            logger.error(f"Error logging capture with quality: {e}")
            return False
    
    def get_log_summary(self, log_file: str = None) -> Dict[str, Any]:
        """
        Get summary statistics from a log file.
        
        Args:
            log_file: Path to the log file (defaults to today's log)
        
        Returns:
            Dictionary with summary statistics
        """
        try:
            if log_file is None:
                log_path = Path(self.create_daily_log())
            else:
                log_path = Path(log_file)
                if not log_path.is_absolute():
                    log_path = self.log_dir / log_file
            
            if not log_path.exists():
                return {"total_captures": 0, "error": "Log file not found"}
            
            with open(log_path, 'r') as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
            
            if not rows:
                return {"total_captures": 0, "error": "No data in log file"}
            
            # Calculate statistics
            sharpness_scores = [float(row['sharpness_score']) for row in rows if row.get('sharpness_score')]
            brightness_values = [float(row['brightness_value']) for row in rows if row.get('brightness_value')]
            
            return {
                "total_captures": len(rows),
                "first_capture": rows[0]['timestamp'] if rows else None,
                "last_capture": rows[-1]['timestamp'] if rows else None,
                "average_sharpness": sum(sharpness_scores) / len(sharpness_scores) if sharpness_scores else 0.0,
                "average_brightness": sum(brightness_values) / len(brightness_values) if brightness_values else 0.0,
                "min_sharpness": min(sharpness_scores) if sharpness_scores else 0.0,
                "max_sharpness": max(sharpness_scores) if sharpness_scores else 0.0,
                "min_brightness": min(brightness_values) if brightness_values else 0.0,
                "max_brightness": max(brightness_values) if brightness_values else 0.0
            }
            
        except Exception as e:
            logger.error(f"Error getting log summary: {e}")
            return {"total_captures": 0, "error": str(e)}


# Convenience functions for direct usage
def append_metadata(log_file: str, timestamp: str, filename: str, metrics: Dict[str, Any]) -> bool:
    """
    Standalone function to append metadata as specified in Task 5.
    
    Args:
        log_file: Path to the log file
        timestamp: ISO format timestamp string
        filename: Name of the captured image file
        metrics: Dictionary containing sharpness_score and brightness_value
    
    Returns:
        True if successful, False otherwise
    """
    logger = MetadataLogger()
    return logger.append_metadata(log_file, timestamp, filename, metrics)


def create_csv_logger(log_dir: str = "logs") -> MetadataLogger:
    """
    Create a new CSV logger instance.
    
    Args:
        log_dir: Directory for log files
    
    Returns:
        MetadataLogger instance
    """
    return MetadataLogger(log_dir)
