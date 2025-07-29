#!/usr/bin/env python3
"""
Live Preview Helper Script for CinePi Timelapse System

Provides real-time video streaming from Raspberry Pi HQ Camera via web browser.
Uses FrameDispatcher pattern to avoid interference with timelapse capture processes.

Usage:
    python preview.py [--port PORT] [--resolution WIDTH HEIGHT] [--fps FPS]
    python preview.py --config config.yaml
"""

import argparse
import logging
import signal
import sys
import threading
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from io import BytesIO

# Add src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from picamera2 import Picamera2
    from libcamera import controls
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False
    Picamera2 = None
    controls = None

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    Image = None

try:
    from flask import Flask, Response, render_template_string
    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None
    Response = None

from config_manager import ConfigManager

# Global variables for graceful shutdown
shutdown_requested = False
frame_dispatcher = None
app = None

logger = logging.getLogger(__name__)


class FrameDispatcher:
    """
    Thread-safe frame dispatcher for sharing camera frames between preview and timelapse.
    
    Uses a single Picamera2 pipeline to capture frames and distribute them to multiple
    consumers without resource contention.
    """
    
    def __init__(self, config_manager: ConfigManager, preview_resolution: Tuple[int, int] = (640, 480), fps: int = 20):
        """Initialize the frame dispatcher."""
        self.config = config_manager
        self.preview_resolution = preview_resolution
        self.fps = fps
        self.camera: Optional[Picamera2] = None
        self.is_initialized = False
        self.running = False
        
        # Thread safety
        self.lock = threading.Lock()
        self.current_frame = None
        self.frame_timestamp = 0
        self.frame_count = 0
        
        # Statistics
        self.stats = {
            'frames_captured': 0,
            'frames_dropped': 0,
            'start_time': None,
            'last_frame_time': None
        }
        
        # Capture thread
        self.capture_thread = None
        
    def initialize_camera(self) -> bool:
        """Initialize the camera for video streaming."""
        if not PICAMERA_AVAILABLE:
            logger.error("Picamera2 library not available")
            return False
            
        if not PIL_AVAILABLE:
            logger.error("PIL/Pillow library not available")
            return False
            
        try:
            logger.info("Initializing camera for live preview...")
            self.camera = Picamera2()
            
            # Get camera configuration
            camera_config = self.config.get('camera', {})
            
            # Use preview resolution for streaming (lower than timelapse)
            resolution = self.preview_resolution
            logger.info(f"Using preview resolution: {resolution}")
            
            # Create video configuration for streaming
            camera_config_dict = self.camera.create_video_configuration(
                main={"size": resolution, "format": "RGB888"},
                buffer_count=4  # More buffers for smooth streaming
            )
            
            # Configure camera
            self.camera.configure(camera_config_dict)
            
            # Apply basic camera settings
            self._apply_camera_settings(camera_config)
            
            # Start camera
            self.camera.start()
            self.is_initialized = True
            
            logger.info(f"Camera initialized successfully for preview at {resolution}")
            return True
            
        except PermissionError as e:
            logger.error(f"Permission error initializing camera: {e}")
            return False
        except OSError as e:
            logger.error(f"OS error initializing camera: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize camera: {e}", exc_info=True)
            return False
    
    def _apply_camera_settings(self, camera_config: Dict[str, Any]) -> None:
        """Apply basic camera settings for preview."""
        if not self.camera:
            return
            
        try:
            # Set exposure mode (auto for preview)
            exposure_mode = camera_config.get('exposure_mode', 'auto')
            if hasattr(controls, 'AeExposureMode'):
                exposure_map = {
                    'auto': controls.AeExposureMode.Auto,
                    'night': controls.AeExposureMode.Night,
                    'backlight': controls.AeExposureMode.BackLight,
                    'spotlight': controls.AeExposureMode.SpotLight,
                    'sports': controls.AeExposureMode.Sports,
                    'snow': controls.AeExposureMode.Snow,
                    'beach': controls.AeExposureMode.Beach,
                    'verylong': controls.AeExposureMode.VeryLong,
                    'fixedfps': controls.AeExposureMode.FixedFPS,
                    'antishake': controls.AeExposureMode.AntiShake,
                    'fireworks': controls.AeExposureMode.Fireworks
                }
                if exposure_mode in exposure_map:
                    self.camera.set_controls({"AeExposureMode": exposure_map[exposure_mode]})
            
            # Set AWB mode
            awb_mode = camera_config.get('awb_mode', 'auto')
            if hasattr(controls, 'AwbMode'):
                awb_map = {
                    'auto': controls.AwbMode.Auto,
                    'sunlight': controls.AwbMode.Sunlight,
                    'cloudy': controls.AwbMode.Cloudy,
                    'shade': controls.AwbMode.Shade,
                    'tungsten': controls.AwbMode.Tungsten,
                    'fluorescent': controls.AwbMode.Fluorescent,
                    'incandescent': controls.AwbMode.Incandescent,
                    'flash': controls.AwbMode.Flash,
                    'horizon': controls.AwbMode.Horizon
                }
                if awb_mode in awb_map:
                    self.camera.set_controls({"AwbMode": awb_map[awb_mode]})
                    
        except Exception as e:
            logger.warning(f"Could not apply all camera settings: {e}")
    
    def start_capture(self) -> bool:
        """Start the frame capture thread."""
        if not self.is_initialized:
            logger.error("Camera not initialized")
            return False
            
        if self.running:
            logger.warning("Capture already running")
            return True
            
        try:
            self.running = True
            self.stats['start_time'] = time.time()
            self.stats['last_frame_time'] = time.time()
            
            # Start capture thread
            self.capture_thread = threading.Thread(target=self._capture_loop, daemon=True)
            self.capture_thread.start()
            
            logger.info("Frame capture started")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start capture: {e}")
            self.running = False
            return False
    
    def _capture_loop(self) -> None:
        """Main capture loop that continuously captures frames."""
        frame_interval = 1.0 / self.fps
        
        while self.running and not shutdown_requested:
            try:
                start_time = time.time()
                
                # Capture frame
                frame = self.camera.capture_array()
                
                # Update frame with thread safety
                with self.lock:
                    self.current_frame = frame
                    self.frame_timestamp = time.time()
                    self.frame_count += 1
                    self.stats['frames_captured'] += 1
                    self.stats['last_frame_time'] = self.frame_timestamp
                
                # Calculate sleep time to maintain frame rate
                elapsed = time.time() - start_time
                sleep_time = max(0, frame_interval - elapsed)
                
                if sleep_time > 0:
                    time.sleep(sleep_time)
                else:
                    # Frame processing took longer than interval
                    self.stats['frames_dropped'] += 1
                    
            except Exception as e:
                logger.error(f"Error in capture loop: {e}")
                time.sleep(0.1)  # Brief pause on error
    
    def get_current_frame(self) -> Optional[Tuple[Any, float]]:
        """Get the current frame and timestamp (thread-safe)."""
        with self.lock:
            if self.current_frame is not None:
                return self.current_frame.copy(), self.frame_timestamp
            return None, 0
    
    def get_frame_jpeg(self, quality: int = 85) -> Optional[bytes]:
        """Get current frame as JPEG bytes (thread-safe)."""
        frame_data = self.get_current_frame()
        if frame_data[0] is not None:
            try:
                # Convert numpy array to PIL Image
                image = Image.fromarray(frame_data[0])
                
                # Save to bytes buffer
                buffer = BytesIO()
                image.save(buffer, format='JPEG', quality=quality, optimize=True)
                return buffer.getvalue()
                
            except Exception as e:
                logger.error(f"Error encoding frame to JPEG: {e}")
                return None
        return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current statistics (thread-safe)."""
        with self.lock:
            stats = self.stats.copy()
            if stats['start_time']:
                uptime = time.time() - stats['start_time']
                stats['uptime_seconds'] = uptime
                stats['fps_actual'] = stats['frames_captured'] / uptime if uptime > 0 else 0
            else:
                stats['uptime_seconds'] = 0
                stats['fps_actual'] = 0
            return stats
    
    def stop_capture(self) -> None:
        """Stop the frame capture thread."""
        self.running = False
        if self.capture_thread and self.capture_thread.is_alive():
            self.capture_thread.join(timeout=2.0)
        logger.info("Frame capture stopped")
    
    def cleanup(self) -> None:
        """Clean up camera resources."""
        self.stop_capture()
        
        if self.camera:
            try:
                self.camera.stop()
                self.camera.close()
                logger.info("Camera resources cleaned up")
            except Exception as e:
                logger.error(f"Error cleaning up camera: {e}")
        
        self.is_initialized = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True


def setup_signal_handlers():
    """Setup signal handlers for graceful shutdown."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/preview.log')
        ]
    )


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Live Preview Helper Script for CinePi Timelapse System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python preview.py                    # Use default settings
  python preview.py --port 8080       # Use custom port
  python preview.py --resolution 1280 720 --fps 30  # Custom resolution and FPS
  python preview.py --config my_config.yaml  # Use custom config file
        """
    )
    
    parser.add_argument(
        '--port', type=int, default=5000,
        help='Port for web server (default: 5000)'
    )
    
    parser.add_argument(
        '--resolution', nargs=2, type=int, metavar=('WIDTH', 'HEIGHT'),
        default=[640, 480],
        help='Preview resolution WIDTH HEIGHT (default: 640 480)'
    )
    
    parser.add_argument(
        '--fps', type=int, default=20,
        help='Target frame rate (default: 20)'
    )
    
    parser.add_argument(
        '--config', type=str, default='config.yaml',
        help='Configuration file path (default: config.yaml)'
    )
    
    parser.add_argument(
        '--host', type=str, default='0.0.0.0',
        help='Host to bind server to (default: 0.0.0.0)'
    )
    
    parser.add_argument(
        '--quality', type=int, default=85, choices=range(1, 101),
        help='JPEG quality for streaming (default: 85)'
    )
    
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


def main():
    """Main entry point."""
    global frame_dispatcher, app, shutdown_requested
    
    # Parse arguments
    args = parse_args()
    
    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(log_level)
    
    # Setup signal handlers
    setup_signal_handlers()
    
    logger.info("Starting CinePi Live Preview Server")
    logger.info(f"Preview resolution: {args.resolution[0]}x{args.resolution[1]}")
    logger.info(f"Target FPS: {args.fps}")
    logger.info(f"Server: http://{args.host}:{args.port}")
    
    # Check dependencies
    if not PICAMERA_AVAILABLE:
        logger.error("Picamera2 library not available. Install with: sudo apt install python3-picamera2")
        sys.exit(1)
    
    if not PIL_AVAILABLE:
        logger.error("PIL/Pillow library not available. Install with: pip install Pillow")
        sys.exit(1)
    
    if not FLASK_AVAILABLE:
        logger.error("Flask library not available. Install with: pip install flask")
        sys.exit(1)
    
    # Load configuration
    try:
        config_manager = ConfigManager(args.config)
        if not config_manager.load_config():
            logger.warning("Using default configuration")
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        sys.exit(1)
    
    # Initialize frame dispatcher
    try:
        frame_dispatcher = FrameDispatcher(
            config_manager=config_manager,
            preview_resolution=tuple(args.resolution),
            fps=args.fps
        )
        
        if not frame_dispatcher.initialize_camera():
            logger.error("Failed to initialize camera")
            sys.exit(1)
        
        if not frame_dispatcher.start_capture():
            logger.error("Failed to start frame capture")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Error initializing frame dispatcher: {e}")
        sys.exit(1)
    
    # Create Flask app
    app = Flask(__name__)
    
    # Define routes
    @app.route('/')
    def index():
        """Main page with live preview."""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>CinePi Live Preview</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background: #f0f0f0; }
                .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
                h1 { color: #333; text-align: center; }
                .video-container { text-align: center; margin: 20px 0; }
                img { max-width: 100%; height: auto; border: 2px solid #ddd; border-radius: 4px; }
                .status { background: #f8f9fa; padding: 15px; border-radius: 4px; margin: 20px 0; }
                .status h3 { margin-top: 0; color: #495057; }
                .status p { margin: 5px 0; }
                .controls { text-align: center; margin: 20px 0; }
                button { background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin: 0 5px; }
                button:hover { background: #0056b3; }
                .error { color: #dc3545; }
                .success { color: #28a745; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🎥 CinePi Live Preview</h1>
                
                <div class="video-container">
                    <img src="/video_feed" alt="Live Preview" id="preview">
                </div>
                
                <div class="status">
                    <h3>📊 Status</h3>
                    <p><strong>Camera:</strong> <span id="camera-status">Checking...</span></p>
                    <p><strong>Frame Rate:</strong> <span id="fps">--</span> FPS</p>
                    <p><strong>Uptime:</strong> <span id="uptime">--</span></p>
                    <p><strong>Frames Captured:</strong> <span id="frames">--</span></p>
                </div>
                
                <div class="controls">
                    <button onclick="refreshStats()">🔄 Refresh Stats</button>
                    <button onclick="location.reload()">🔄 Reload Page</button>
                </div>
            </div>
            
            <script>
                function refreshStats() {
                    fetch('/status')
                        .then(response => response.json())
                        .then(data => {
                            document.getElementById('camera-status').textContent = data.camera_active ? 'Active' : 'Inactive';
                            document.getElementById('camera-status').className = data.camera_active ? 'success' : 'error';
                            document.getElementById('fps').textContent = data.fps_actual.toFixed(1);
                            document.getElementById('uptime').textContent = formatUptime(data.uptime_seconds);
                            document.getElementById('frames').textContent = data.frames_captured;
                        })
                        .catch(error => {
                            console.error('Error fetching stats:', error);
                            document.getElementById('camera-status').textContent = 'Error';
                            document.getElementById('camera-status').className = 'error';
                        });
                }
                
                function formatUptime(seconds) {
                    const hours = Math.floor(seconds / 3600);
                    const minutes = Math.floor((seconds % 3600) / 60);
                    const secs = Math.floor(seconds % 60);
                    return `${hours}h ${minutes}m ${secs}s`;
                }
                
                // Refresh stats every 2 seconds
                setInterval(refreshStats, 2000);
                refreshStats(); // Initial load
            </script>
        </body>
        </html>
        """
        return render_template_string(html_template)
    
    @app.route('/video_feed')
    def video_feed():
        """MJPEG video stream endpoint."""
        def generate():
            while not shutdown_requested:
                jpeg_data = frame_dispatcher.get_frame_jpeg(quality=args.quality)
                if jpeg_data:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + jpeg_data + b'\r\n')
                else:
                    # Send a blank frame or error image
                    time.sleep(0.1)
        
        return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')
    
    @app.route('/status')
    def status():
        """JSON status endpoint."""
        if frame_dispatcher:
            stats = frame_dispatcher.get_stats()
            return {
                'camera_active': frame_dispatcher.is_initialized and frame_dispatcher.running,
                'fps_actual': stats.get('fps_actual', 0),
                'uptime_seconds': stats.get('uptime_seconds', 0),
                'frames_captured': stats.get('frames_captured', 0),
                'frames_dropped': stats.get('frames_dropped', 0),
                'resolution': args.resolution,
                'target_fps': args.fps
            }
        else:
            return {'error': 'Frame dispatcher not available'}, 500
    
    # Start Flask server
    try:
        logger.info("Starting Flask server...")
        app.run(
            host=args.host,
            port=args.port,
            threaded=True,
            debug=False,
            use_reloader=False
        )
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Error running Flask server: {e}")
    finally:
        # Cleanup
        logger.info("Shutting down...")
        if frame_dispatcher:
            frame_dispatcher.cleanup()
        logger.info("Shutdown complete")


if __name__ == '__main__':
    main() 