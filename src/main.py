"""
Main entry point for CinePi timelapse system.
Orchestrates camera operations, configuration management, and logging.
"""

import argparse
import logging
import time
import signal
import sys
import os
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, List
from collections import deque

# Add src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent))

from config_manager import ConfigManager
from metrics import MetricsLogger, ImageQualityMetrics
from capture_utils import CameraManager
from timing_controller import TimingController

# Global variables for graceful shutdown
shutdown_requested = False
camera_manager = None
metrics_logger = None


class StatusMonitor:
    """Real-time console status monitoring for the timelapse system."""
    
    def __init__(self, config: ConfigManager, verbose: bool = False):
        """Initialize the status monitor."""
        self.config = config
        self.verbose = verbose
        self.capture_count = 0
        self.start_time = datetime.now()
        self.last_capture_time = self.start_time
        self.last_quality_metrics = None
        self.quality_history = deque(maxlen=50)  # Keep last 50 quality readings
        self.interval_seconds = config.get('timelapse.interval_seconds', 30)
        self.duration_hours = config.get('timelapse.duration_hours', 24)
        self.output_dir = config.get('timelapse.output_dir', 'output/images')
        
        # Calculate end time if duration is specified
        self.end_time = None
        if self.duration_hours > 0:
            self.end_time = self.start_time + timedelta(hours=self.duration_hours)
    
    def update_capture(self, capture_number: int, quality_metrics: Optional[Dict] = None):
        """Update capture statistics."""
        self.capture_count = capture_number
        self.last_capture_time = datetime.now()
        
        if quality_metrics:
            self.last_quality_metrics = quality_metrics
            self.quality_history.append(quality_metrics)
    
    def get_next_capture_time(self) -> datetime:
        """Calculate the next scheduled capture time."""
        return self.last_capture_time + timedelta(seconds=self.interval_seconds)
    
    def get_time_until_next(self) -> float:
        """Get seconds until next capture."""
        next_time = self.get_next_capture_time()
        return max(0, (next_time - datetime.now()).total_seconds())
    
    def set_timing_controller(self, timing_controller: TimingController):
        """Set the timing controller for precise timing information."""
        self.timing_controller = timing_controller
    
    def get_precise_time_until_next(self) -> float:
        """Get precise time until next capture using timing controller."""
        if hasattr(self, 'timing_controller'):
            return self.timing_controller.get_time_until_next()
        return self.get_time_until_next()
    
    def get_elapsed_time(self) -> float:
        """Get elapsed time in hours."""
        return (datetime.now() - self.start_time).total_seconds() / 3600
    
    def get_remaining_time(self) -> Optional[float]:
        """Get remaining time in hours if duration is set."""
        if self.end_time:
            remaining = (self.end_time - datetime.now()).total_seconds() / 3600
            return max(0, remaining)
        return None
    
    def get_quality_statistics(self) -> Dict:
        """Calculate quality statistics from history."""
        if not self.quality_history:
            return {}
        
        sharpness_scores = [m['sharpness_score'] for m in self.quality_history if 'sharpness_score' in m]
        brightness_values = [m['brightness_value'] for m in self.quality_history if 'brightness_value' in m]
        
        stats = {}
        if sharpness_scores:
            stats['avg_sharpness'] = sum(sharpness_scores) / len(sharpness_scores)
            stats['min_sharpness'] = min(sharpness_scores)
            stats['max_sharpness'] = max(sharpness_scores)
        
        if brightness_values:
            stats['avg_brightness'] = sum(brightness_values) / len(brightness_values)
            stats['min_brightness'] = min(brightness_values)
            stats['max_brightness'] = max(brightness_values)
        
        return stats
    
    def display_status_line(self, current_time: datetime, capture_success: bool = True, error_msg: str = ""):
        """Display the main status line with real-time updates."""
        elapsed_hours = self.get_elapsed_time()
        time_until_next = self.get_time_until_next()
        
        # Base status line
        status_line = (
            f"\r[{current_time.strftime('%H:%M:%S')}] "
            f"Capture #{self.capture_count:04d} | "
            f"Elapsed: {elapsed_hours:.1f}h"
        )
        
        # Add remaining time if duration is set
        remaining = self.get_remaining_time()
        if remaining is not None:
            status_line += f" | Remaining: {remaining:.1f}h"
        
        # Add quality metrics if available
        if self.last_quality_metrics and capture_success:
            sharpness = self.last_quality_metrics.get('sharpness_score', 0)
            brightness = self.last_quality_metrics.get('brightness_value', 0)
            status_line += f" | Sharpness: {sharpness:.1f} | Brightness: {brightness:.1f}"
        
        # Add next capture time with timing accuracy info
        if hasattr(self, 'timing_controller'):
            precise_time_until_next = self.get_precise_time_until_next()
            drift_info = self.timing_controller.get_drift_info()
            drift_percent = drift_info['drift_percentage']
            
            if precise_time_until_next > 0:
                next_time = self.get_next_capture_time()
                status_line += f" | Next: {next_time.strftime('%H:%M:%S')} ({precise_time_until_next:.0f}s) | Drift: {drift_percent:.1f}%"
            else:
                status_line += " | Next: NOW | Drift: {drift_percent:.1f}%"
        else:
            if time_until_next > 0:
                next_time = self.get_next_capture_time()
                status_line += f" | Next: {next_time.strftime('%H:%M:%S')} ({time_until_next:.0f}s)"
            else:
                status_line += " | Next: NOW"
        
        # Add error message if any
        if error_msg:
            status_line += f" | {error_msg}"
        
        # Add dry run indicator
        if hasattr(self, 'dry_run') and self.dry_run:
            status_line += " | [DRY RUN]"
        
        # Clear line and print
        print(f"{status_line:<120}", end="", flush=True)
    
    def display_periodic_summary(self, current_time: datetime):
        """Display periodic summary statistics."""
        if self.capture_count % 10 != 0:  # Every 10 captures
            return
        
        elapsed_hours = self.get_elapsed_time()
        avg_interval = elapsed_hours * 3600 / self.capture_count if self.capture_count > 0 else 0
        
        # Get timing accuracy information if available
        timing_info = ""
        if hasattr(self, 'timing_controller'):
            drift_info = self.timing_controller.get_drift_info()
            timing_stats = self.timing_controller.get_timing_stats()
            timing_info = f" | Timing: {timing_stats.avg_interval:.1f}s avg | Drift: {drift_info['drift_percentage']:.1f}%"
        
        # Get quality statistics
        quality_stats = self.get_quality_statistics()
        
        print(f"\n\n=== Progress Summary (Capture #{self.capture_count}) ===")
        print(f"Time: {current_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Elapsed: {elapsed_hours:.2f} hours")
        print(f"Average interval: {avg_interval:.1f} seconds{timing_info}")
        
        if quality_stats:
            print(f"Quality Statistics (last {len(self.quality_history)} captures):")
            if 'avg_sharpness' in quality_stats:
                print(f"  Sharpness: {quality_stats['avg_sharpness']:.1f} avg "
                      f"({quality_stats['min_sharpness']:.1f}-{quality_stats['max_sharpness']:.1f})")
            if 'avg_brightness' in quality_stats:
                print(f"  Brightness: {quality_stats['avg_brightness']:.1f} avg "
                      f"({quality_stats['min_brightness']:.1f}-{quality_stats['max_brightness']:.1f})")
        
        # Add verbose information if enabled
        if self.verbose:
            print(f"Output directory: {self.output_dir}")
            print(f"Interval: {self.interval_seconds} seconds")
            if self.end_time:
                remaining = self.get_remaining_time()
                print(f"Duration: {self.duration_hours} hours ({remaining:.1f}h remaining)")
            else:
                print(f"Duration: Indefinite")
        
        print("=" * 60)
    
    def display_final_summary(self, output_dir: Path):
        """Display final summary when timelapse completes."""
        total_time = (datetime.now() - self.start_time).total_seconds()
        total_hours = total_time / 3600
        avg_interval = total_time / self.capture_count if self.capture_count > 0 else 0
        
        quality_stats = self.get_quality_statistics()
        
        print(f"\n\n=== Final Timelapse Summary ===")
        print(f"Total captures: {self.capture_count}")
        print(f"Total time: {total_hours:.2f} hours")
        print(f"Average interval: {avg_interval:.1f} seconds")
        print(f"Output directory: {output_dir}")
        
        if quality_stats:
            print(f"\nQuality Summary:")
            if 'avg_sharpness' in quality_stats:
                print(f"  Sharpness: {quality_stats['avg_sharpness']:.1f} average "
                      f"({quality_stats['min_sharpness']:.1f}-{quality_stats['max_sharpness']:.1f} range)")
            if 'avg_brightness' in quality_stats:
                print(f"  Brightness: {quality_stats['avg_brightness']:.1f} average "
                      f"({quality_stats['min_brightness']:.1f}-{quality_stats['max_brightness']:.1f} range)")
        
        print("=" * 40)
    
    def set_dry_run(self, dry_run: bool):
        """Set dry run mode."""
        self.dry_run = dry_run


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    signal_name = signal.Signals(signum).name
    print(f"\nReceived {signal_name} signal. Initiating graceful shutdown...")
    logging.info(f"Received {signal_name} signal. Initiating graceful shutdown...")
    shutdown_requested = True


def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown."""
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl-C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    logging.info("Signal handlers configured for graceful shutdown")


def check_disk_space(output_dir: Path, min_space_mb: int = 100) -> bool:
    """Check if there's sufficient disk space for captures."""
    try:
        total, used, free = shutil.disk_usage(output_dir)
        free_mb = free / (1024 * 1024)
        
        if free_mb < min_space_mb:
            logging.error(f"Insufficient disk space: {free_mb:.1f}MB free, {min_space_mb}MB required")
            return False
        
        logging.debug(f"Disk space available: {free_mb:.1f}MB")
        return True
        
    except Exception as e:
        logging.error(f"Error checking disk space: {e}")
        return False


def check_file_permissions(output_dir: Path) -> bool:
    """Check if we have write permissions to the output directory."""
    try:
        test_file = output_dir / ".test_write_permission"
        test_file.touch()
        test_file.unlink()
        return True
    except (PermissionError, OSError) as e:
        logging.error(f"Permission error in output directory {output_dir}: {e}")
        return False
    except Exception as e:
        logging.error(f"Error checking file permissions: {e}")
        return False


def setup_logging(config: ConfigManager) -> None:
    """Set up logging configuration with enhanced error handling."""
    try:
        log_level = config.get('logging.log_level', 'INFO')
        log_dir = Path(config.get('logging.log_dir', 'logs'))
        
        # Directory creation is now handled by ensure_directories()
        # Just verify the directory exists and is writable
        if not log_dir.exists():
            raise FileNotFoundError(f"Log directory {log_dir} does not exist. Run ensure_directories() first.")
        
        if not check_file_permissions(log_dir):
            print(f"Error: Cannot write to log directory {log_dir}")
            sys.exit(1)
        
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_dir / 'cinepi.log'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        
        logging.info("Logging system initialized successfully")
        
    except Exception as e:
        print(f"Error setting up logging: {e}")
        # Fallback to basic console logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logging.error(f"Failed to set up file logging: {e}")


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="CinePi Timelapse Camera System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                           # Use default config
  python main.py --interval 60             # 60 second intervals
  python main.py --duration 2              # Run for 2 hours
  python main.py --interval 30 --duration 4 # 30s intervals for 4 hours
        """
    )
    
    parser.add_argument(
        '--interval', '-i',
        type=int,
        help='Capture interval in seconds (overrides config)'
    )
    
    parser.add_argument(
        '--duration', '-d',
        type=float,
        help='Duration to run in hours (overrides config, 0 = indefinite)'
    )
    
    parser.add_argument(
        '--output-dir', '-o',
        type=str,
        help='Output directory for images (overrides config)'
    )
    
    parser.add_argument(
        '--config', '-c',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Test configuration without capturing images'
    )
    
    return parser.parse_args()


def load_config(args: argparse.Namespace) -> ConfigManager:
    """Load and validate configuration with error handling."""
    try:
        config = ConfigManager(config_path=args.config)
        
        # Override config with command line arguments
        if args.interval:
            config.set('timelapse.interval_seconds', args.interval)
        
        if args.duration is not None:
            config.set('timelapse.duration_hours', args.duration)
        
        if args.output_dir:
            config.set('timelapse.output_dir', args.output_dir)
        
        if args.verbose:
            config.set('logging.log_level', 'DEBUG')
        
        # Validate configuration
        if not config.validate_config():
            raise ValueError("Invalid configuration. Please check config.yaml")
        
        return config
        
    except FileNotFoundError:
        print(f"Error: Configuration file '{args.config}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)


def init_camera(config: ConfigManager) -> Optional[CameraManager]:
    """Initialize camera with configuration and comprehensive error handling."""
    global camera_manager
    
    try:
        camera_manager = CameraManager(config)
        if camera_manager.initialize_camera():
            logging.info("Camera initialized successfully")
            return camera_manager
        else:
            logging.error("Failed to initialize camera")
            return None
            
    except ImportError as e:
        logging.error(f"Camera library not available: {e}")
        print("Error: Camera library not available. Please install required dependencies.")
        return None
    except PermissionError as e:
        logging.error(f"Permission error initializing camera: {e}")
        print("Error: Permission denied accessing camera. Try running with sudo.")
        return None
    except Exception as e:
        logging.error(f"Unexpected error initializing camera: {e}", exc_info=True)
        print(f"Error: Failed to initialize camera: {e}")
        return None


def generate_filename(config: ConfigManager, capture_number: int, output_dir: Path = None) -> str:
    """Generate timestamped filename for captured image with millisecond precision and uniqueness.
    
    Args:
        config: Configuration manager instance
        capture_number: Sequential capture number
        output_dir: Output directory to check for filename uniqueness
        
    Returns:
        str: Generated filename with timestamp and optional counter for uniqueness
    """
    try:
        prefix = config.get('timelapse.filename_prefix', 'timelapse')
        image_format = config.get('timelapse.image_format', 'jpg')
        add_timestamp = config.get('timelapse.add_timestamp', True)
        
        # Ensure image format is lowercase and has no leading dot
        image_format = image_format.lower().lstrip('.')
        
        # Generate base filename
        if add_timestamp:
            # Use millisecond precision: YYYYMMDD_HHMMSS_mmm
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
            if image_format:
                base_filename = f"{prefix}_{timestamp}_{capture_number:06d}.{image_format}"
            else:
                base_filename = f"{prefix}_{timestamp}_{capture_number:06d}"
        else:
            if image_format:
                base_filename = f"{prefix}_{capture_number:06d}.{image_format}"
            else:
                base_filename = f"{prefix}_{capture_number:06d}"
        
        # If output directory is provided, ensure filename uniqueness
        if output_dir:
            return ensure_filename_uniqueness(base_filename, output_dir)
        
        return base_filename
            
    except Exception as e:
        logging.error(f"Error generating filename: {e}")
        # Fallback filename with millisecond precision
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
        return f"timelapse_{timestamp}_{capture_number:06d}.jpg"


def ensure_filename_uniqueness(filename: str, output_dir: Path) -> str:
    """Ensure filename uniqueness by adding counter if file already exists.
    
    Args:
        filename: Base filename to check
        output_dir: Directory to check for existing files
        
    Returns:
        str: Unique filename (original or with counter suffix)
    """
    try:
        filepath = output_dir / filename
        
        # If file doesn't exist, return original filename
        if not filepath.exists():
            return filename
        
        # Extract filename parts for counter addition
        name_parts = filename.rsplit('.', 1)
        if len(name_parts) != 2:
            # Fallback if filename doesn't have extension
            base_name = filename
            extension = ''
        else:
            base_name, extension = name_parts
        
        # Add counter until we find a unique filename
        counter = 1
        while True:
            if extension:
                new_filename = f"{base_name}_{counter:03d}.{extension}"
            else:
                new_filename = f"{base_name}_{counter:03d}"
            
            new_filepath = output_dir / new_filename
            if not new_filepath.exists():
                logging.debug(f"Filename collision resolved: {filename} -> {new_filename}")
                return new_filename
            
            counter += 1
            
            # Safety check to prevent infinite loop
            if counter > 999:
                logging.warning(f"Could not generate unique filename for {filename} after 999 attempts")
                # Use timestamp as fallback
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]
                return f"{base_name}_{timestamp}.{extension}" if extension else f"{base_name}_{timestamp}"
                
    except Exception as e:
        logging.error(f"Error ensuring filename uniqueness: {e}")
        # Return original filename as fallback
        return filename


def ensure_directories(config: ConfigManager) -> bool:
    """Ensure all required directories exist and are writable.
    
    Creates the following directories if they don't exist:
    - Output directory for images
    - Log directory for log files
    - Any parent directories needed
    
    Args:
        config: Configuration manager instance
        
    Returns:
        bool: True if all directories were created successfully, False otherwise
        
    Raises:
        PermissionError: If directory creation fails due to permissions
        OSError: If directory creation fails for other reasons
    """
    logger = logging.getLogger(__name__)
    logger.info("Ensuring all required directories exist...")
    
    directories_to_create = []
    
    try:
        # Get directory paths from configuration
        output_dir = Path(config.get('timelapse.output_dir', 'output/images'))
        log_dir = Path(config.get('logging.log_dir', 'logs'))
        
        directories_to_create.extend([output_dir, log_dir])
        
        # Create each directory with proper error handling
        for directory in directories_to_create:
            try:
                # Create directory and all parent directories
                directory.mkdir(parents=True, exist_ok=True)
                logger.info(f"Directory ensured: {directory}")
                
                # Verify write permissions
                if not check_file_permissions(directory):
                    raise PermissionError(f"Cannot write to directory: {directory}")
                    
            except PermissionError as e:
                logger.error(f"Permission error creating directory {directory}: {e}")
                print(f"Error: Permission denied creating directory {directory}")
                print(f"Please check permissions or run with appropriate privileges")
                return False
                
            except OSError as e:
                logger.error(f"OS error creating directory {directory}: {e}")
                print(f"Error: Failed to create directory {directory}: {e}")
                return False
                
            except Exception as e:
                logger.error(f"Unexpected error creating directory {directory}: {e}")
                print(f"Error: Unexpected error creating directory {directory}: {e}")
                return False
        
        # Check disk space for output directory
        if not check_disk_space(output_dir):
            logger.error("Insufficient disk space for output directory")
            print("Error: Insufficient disk space for output directory")
            return False
        
        logger.info("All required directories created and verified successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error in ensure_directories: {e}")
        print(f"Error: Failed to ensure directories: {e}")
        return False


def ensure_output_directory(config: ConfigManager) -> Path:
    """Ensure output directory exists and create daily subdirectory if needed."""
    try:
        output_dir = Path(config.get('timelapse.output_dir', 'output/images'))
        
        # Directory creation is now handled by ensure_directories()
        # Just verify the directory exists and is writable
        if not output_dir.exists():
            raise FileNotFoundError(f"Output directory {output_dir} does not exist. Run ensure_directories() first.")
        
        # Check permissions
        if not check_file_permissions(output_dir):
            raise PermissionError(f"Cannot write to output directory: {output_dir}")
        
        # Check disk space
        if not check_disk_space(output_dir):
            raise OSError("Insufficient disk space")
        
        if config.get('timelapse.create_daily_dirs', True):
            daily_dir = output_dir / datetime.now().strftime("%Y-%m-%d")
            daily_dir.mkdir(exist_ok=True)
            return daily_dir
        
        return output_dir
        
    except Exception as e:
        logging.error(f"Error ensuring output directory: {e}")
        raise


def capture_loop(config: ConfigManager, camera: CameraManager, metrics: MetricsLogger, args: argparse.Namespace) -> None:
    """Main timelapse capture loop with comprehensive error handling."""
    global shutdown_requested
    
    logger = logging.getLogger(__name__)
    
    # Get configuration values
    interval = config.get('timelapse.interval_seconds', 30)
    duration_hours = config.get('timelapse.duration_hours', 24)
    
    try:
        output_dir = ensure_output_directory(config)
    except (PermissionError, OSError) as e:
        logger.error(f"Output directory error: {e}")
        print(f"Error: {e}")
        return
    except Exception as e:
        logger.error(f"Unexpected error with output directory: {e}")
        print(f"Error: {e}")
        return
    
    # Initialize status monitor
    status_monitor = StatusMonitor(config, verbose=args.verbose)
    status_monitor.set_dry_run(args.dry_run)
    
    # Calculate end time if duration is specified
    end_time = None
    if duration_hours > 0:
        end_time = datetime.now() + timedelta(hours=duration_hours)
        logger.info(f"Timelapse will run until: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Initialize timing controller for precise timing
    timing_controller = TimingController(interval, max_drift_threshold=1.0)
    
    # Initialize counters and timing
    capture_count = 0
    start_time = datetime.now()
    last_capture_time = start_time
    
    # Set timing controller in status monitor
    status_monitor.set_timing_controller(timing_controller)
    
    logger.info(f"Starting timelapse capture loop")
    logger.info(f"Interval: {interval} seconds")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Duration: {'Indefinite' if duration_hours == 0 else f'{duration_hours} hours'}")
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No images will be captured")
    
    # Display initial status
    print(f"\n=== CinePi Timelapse System ===")
    print(f"Started: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Interval: {interval} seconds")
    print(f"Output: {output_dir}")
    print(f"Duration: {'Indefinite' if duration_hours == 0 else f'{duration_hours} hours'}")
    if args.dry_run:
        print("Mode: DRY RUN (no images captured)")
    print("=" * 40)
    print()
    
    try:
        while not shutdown_requested:
            current_time = datetime.now()
            
            # Check if we should stop
            if end_time and current_time >= end_time:
                logger.info(f"Reached end time. Stopping timelapse.")
                break
            
            # Use timing controller for precise timing
            should_capture, time_until_next = timing_controller.wait_for_next_capture()
            
            if should_capture:
                capture_count += 1
                
                # Check system resources before capture
                try:
                    if not check_disk_space(output_dir):
                        logger.error("Insufficient disk space. Stopping capture.")
                        print("Error: Insufficient disk space. Stopping capture.")
                        break
                except Exception as e:
                    logger.error(f"Error checking disk space: {e}")
                    # Continue with capture attempt
                
                # Generate filename with uniqueness check
                try:
                    filename = generate_filename(config, capture_count, output_dir)
                    filepath = output_dir / filename
                except Exception as e:
                    logger.error(f"Error generating filename: {e}")
                    continue
                
                # Display status using StatusMonitor
                status_monitor.display_status_line(current_time)
                
                if not args.dry_run:
                    # Capture image with error handling
                    capture_success = False
                    error_msg = ""
                    try:
                        if camera.capture_image(str(filepath)):
                            logger.info(f"Captured: {filename}")
                            capture_success = True
                        else:
                            logger.error(f"Failed to capture: {filename}")
                            error_msg = "Capture failed"
                    except PermissionError as e:
                        logger.error(f"Permission error during capture: {e}")
                        error_msg = "Permission error"
                    except OSError as e:
                        logger.error(f"OS error during capture: {e}")
                        error_msg = "System error"
                    except Exception as e:
                        logger.error(f"Unexpected error during capture: {e}", exc_info=True)
                        error_msg = "Capture error"
                    
                    if capture_success:
                        # Calculate quality metrics with error handling
                        quality_metrics = None
                        try:
                            quality_metrics = ImageQualityMetrics.evaluate_image_quality(str(filepath))
                            
                            # Log metadata with error handling
                            try:
                                # Get timing statistics
                                timing_stats = timing_controller.get_timing_stats()
                                drift_info = timing_controller.get_drift_info()
                                
                                metadata = {
                                    'timestamp': current_time.isoformat(),
                                    'filename': filename,
                                    'filepath': str(filepath),
                                    'capture_number': capture_count,
                                    'interval_seconds': interval,
                                    'sharpness_score': quality_metrics['sharpness_score'],
                                    'brightness_value': quality_metrics['brightness_value'],
                                    'timing_interval': timing_stats.actual_interval,
                                    'timing_drift': timing_stats.actual_interval - interval,
                                    'timing_accumulated_drift': drift_info['current_drift'],
                                    'timing_system_clock_adjustments': drift_info['system_clock_adjustments']
                                }
                                
                                if not metrics.log_capture_event(str(filepath), metadata):
                                    logger.warning(f"Failed to log metadata for {filename}")
                                
                            except Exception as e:
                                logger.error(f"Error logging metadata: {e}")
                            
                        except Exception as e:
                            logger.error(f"Error processing image {filename}: {e}")
                            error_msg = "Error processing image"
                    
                    # Update status monitor with capture results
                    status_monitor.update_capture(capture_count, quality_metrics)
                    
                    # Display updated status with error message if any
                    status_monitor.display_status_line(current_time, capture_success, error_msg)
                else:
                    # Update status monitor for dry run
                    status_monitor.update_capture(capture_count)
                    status_monitor.display_status_line(current_time, True, "")
                
                # Notify timing controller that capture is complete
                timing_controller.capture_completed()
                last_capture_time = current_time
                
                # Display periodic summary and log system metrics
                status_monitor.display_periodic_summary(current_time)
                
                if capture_count % 10 == 0:
                    logger.info(f"Progress: {capture_count} captures completed")
                    
                    # Log system metrics with error handling
                    try:
                        system_metrics = metrics.log_system_metrics()
                        logger.debug(f"System metrics: {system_metrics}")
                    except Exception as e:
                        logger.debug(f"Could not log system metrics: {e}")
            
            # Timing controller handles sleep intervals automatically
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal. Stopping capture loop...")
    except Exception as e:
        logger.error(f"Error in capture loop: {e}", exc_info=True)
    finally:
        # Final summary using StatusMonitor
        status_monitor.display_final_summary(output_dir)
        
        # Log comprehensive timing report
        timing_controller.log_timing_report()
        
        logger.info(f"Timelapse completed. {capture_count} captures in {status_monitor.get_elapsed_time():.2f} hours")


def cleanup_resources():
    """Clean up all resources gracefully."""
    global camera_manager, metrics_logger
    
    logging.info("Starting cleanup process...")
    
    try:
        # Clean up camera
        if camera_manager:
            camera_manager.cleanup()
            logging.info("Camera cleanup completed")
    except Exception as e:
        logging.error(f"Error during camera cleanup: {e}")
    
    try:
        # Clean up metrics logger
        if metrics_logger:
            metrics_logger.cleanup()
            logging.info("Metrics logger cleanup completed")
    except Exception as e:
        logging.error(f"Error during metrics logger cleanup: {e}")
    
    logging.info("Cleanup process completed")


def main():
    """Main timelapse entry point with comprehensive error handling."""
    global shutdown_requested, camera_manager, metrics_logger
    
    # Set up signal handlers early
    setup_signal_handlers()
    
    # Parse command line arguments
    try:
        args = parse_args()
    except Exception as e:
        print(f"Error parsing arguments: {e}")
        return 1
    
    try:
        # Load configuration
        config = load_config(args)
        
        # Ensure all required directories exist
        if not ensure_directories(config):
            print("Exiting due to directory creation failures.")
            return 1

        # Set up logging
        setup_logging(config)
        logger = logging.getLogger(__name__)
        logger.info("CinePi Timelapse System Starting...")
        
        # Initialize components with error handling
        try:
            metrics_logger = MetricsLogger(
                log_dir=config.get('logging.log_dir'),
                csv_filename=config.get('logging.csv_filename')
            )
        except Exception as e:
            logger.error(f"Failed to initialize metrics logger: {e}")
            print(f"Error: Failed to initialize metrics logger: {e}")
            return 1
        
        # Initialize camera
        camera_manager = init_camera(config)
        if not camera_manager:
            logger.error("Failed to initialize camera. Exiting.")
            return 1
        
        # Run capture loop
        capture_loop(config, camera_manager, metrics_logger, args)
        
        return 0
        
    except KeyboardInterrupt:
        print("\nReceived interrupt signal. Shutting down...")
        return 0
    except Exception as e:
        print(f"Fatal error: {e}")
        logging.error(f"Fatal error: {e}", exc_info=True)
        return 1
    finally:
        # Always attempt cleanup
        cleanup_resources()
        logging.info("CinePi Timelapse System stopped")


if __name__ == "__main__":
    sys.exit(main())
