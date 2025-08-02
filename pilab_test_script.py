#!/usr/bin/env python3
"""
PiLab Test Script - 10-Minute Interval Capture & Supabase Sync

This script captures an image every 10 minutes, saves it locally,
and uploads it to Supabase Storage. It's designed for testing
the PiLab infrastructure with the local Docker Supabase environment.
"""

import os
import sys
import time
import logging
import yaml
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add src directory to path for imports
sys.path.insert(0, str(Path(__file__).parent / 'src'))

try:
    from supabase_client import create_pilab_client
except ImportError as e:
    print(f"❌ Failed to import Supabase client: {e}")
    print("Make sure you're running this from the PiLab project root")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('pilab_test_script.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class PiLabTestScript:
    """Main test script class for PiLab 10-minute interval captures."""
    
    def __init__(self):
        """Initialize the test script."""
        self.config = None
        self.supabase_client = None
        self.capture_count = 0
        self.start_time = None
        
        # Load environment and configuration
        self._load_environment()
        self._load_config()
        self._initialize_supabase_client()
    
    def _load_environment(self):
        """Load environment variables from .env.pi file."""
        env_file = Path('.env.pi')
        if env_file.exists():
            load_dotenv(env_file)
            logger.info(f"✅ Loaded environment from {env_file}")
        else:
            logger.error(f"❌ Environment file {env_file} not found")
            sys.exit(1)
    
    def _load_config(self):
        """Load configuration from config.yaml."""
        config_file = Path('config.yaml')
        if not config_file.exists():
            logger.error(f"❌ Config file {config_file} not found")
            sys.exit(1)
        
        try:
            with open(config_file, 'r') as f:
                self.config = yaml.safe_load(f)
            logger.info("✅ Configuration loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load configuration: {e}")
            sys.exit(1)
    
    def _initialize_supabase_client(self):
        """Initialize the Supabase client."""
        try:
            self.supabase_client = create_pilab_client()
            logger.info("✅ Supabase client initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase client: {e}")
            sys.exit(1)
    
    def _get_capture_settings(self):
        """Get capture settings from configuration."""
        capture_config = self.config.get('capture', {})
        storage_config = self.config.get('storage', {})
        
        # Expand environment variables in local_dir
        local_dir = storage_config.get('local_dir', '/home/pi/pilab/captures')
        if isinstance(local_dir, str) and '${CAPTURE_DIR}' in local_dir:
            capture_dir = os.getenv('CAPTURE_DIR', '/home/pi/pilab/captures')
            local_dir = local_dir.replace('${CAPTURE_DIR}', capture_dir)
        
        return {
            'interval_sec': capture_config.get('interval_sec', 600),
            'resolution': capture_config.get('resolution', '4056x3040'),
            'rotation': capture_config.get('rotation', 180),
            'local_dir': local_dir,
            'bucket': storage_config.get('bucket', 'pilab-captures')
        }
    
    def _create_capture_filename(self):
        """Create a filename for the current capture."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.capture_count += 1
        return f"test_capture_{self.capture_count:03d}_{timestamp}.jpg"
    
    def _capture_image(self, filename):
        """
        Capture an image using the real PiCamera2.
        """
        settings = self._get_capture_settings()
        
        # Parse resolution
        resolution_str = settings['resolution']
        width, height = map(int, resolution_str.split('x'))
        rotation = settings['rotation']
        
        capture_dir = Path(settings['local_dir'])
        
        # Handle cross-platform paths for development
        if settings['local_dir'].startswith('/home/pi/'):
            capture_dir = Path('captures')
        
        capture_dir.mkdir(exist_ok=True)
        image_path = capture_dir / filename
        
        try:
            # Import PiCamera2
            from picamera2 import Picamera2
            import cv2
            
            logger.info(f"📸 Initializing camera for capture...")
            
            # Initialize camera
            picam2 = Picamera2()
            
            # Configure camera with specified settings
            config = picam2.create_still_configuration(
                main={'size': (width, height)},
                buffer_count=4
            )
            picam2.configure(config)
            
            # Start camera
            picam2.start()
            
            # Let camera warm up
            time.sleep(2)
            
            # Capture image
            logger.info(f"📸 Capturing image at {width}x{height}...")
            image = picam2.capture_array()
            
            # Apply rotation if needed
            if rotation == 180:
                image = cv2.rotate(image, cv2.ROTATE_180)
            elif rotation == 90:
                image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
            elif rotation == 270:
                image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
            
            # Save image
            cv2.imwrite(str(image_path), image)
            
            # Stop camera
            picam2.stop()
            
            # Close camera to release resources
            picam2.close()
            
            # Small delay to ensure camera is fully released
            time.sleep(1)
            
            logger.info(f"📸 Successfully captured real image: {image_path}")
            logger.info(f"📊 Image size: {image.shape}")
            
            return image_path
            
        except ImportError:
            logger.error("❌ PiCamera2 not available - falling back to placeholder")
            # Fallback to placeholder for development
            dummy_content = f"# PiLab Test Capture\n# Timestamp: {datetime.now().isoformat()}\n# Resolution: {settings['resolution']}\n# Rotation: {settings['rotation']}\n# This is a test image file (PiCamera2 not available)."
            image_path.write_text(dummy_content)
            return image_path
            
        except Exception as e:
            logger.error(f"❌ Camera capture failed: {e}")
            # Fallback to placeholder
            dummy_content = f"# PiLab Test Capture\n# Timestamp: {datetime.now().isoformat()}\n# Resolution: {settings['resolution']}\n# Rotation: {settings['rotation']}\n# Camera error: {e}"
            image_path.write_text(dummy_content)
            return image_path
    
    def _upload_to_supabase(self, image_path, filename):
        """Upload the captured image to Supabase Storage."""
        settings = self._get_capture_settings()
        bucket_name = settings['bucket']
        
        try:
            logger.info(f"☁️  Uploading to Supabase bucket '{bucket_name}': {filename}")
            
            # Read the image file
            with open(image_path, 'rb') as f:
                file_data = f.read()
            
            # Upload to Supabase Storage using the underlying client
            # Add explicit API key header
            headers = {
                "apikey": self.supabase_client.key,
                "Authorization": f"Bearer {self.supabase_client.key}"
            }
            
            result = self.supabase_client.client.storage.from_(bucket_name).upload(
                path=filename,
                file=file_data,
                file_options={"content-type": "image/jpeg"},
                headers=headers
            )
            
            logger.info(f"✅ Upload successful: {filename}")
            logger.info(f"📊 Upload result: {result}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Upload failed: {e}")
            return False
    
    def _log_capture_metadata(self, filename, image_path, upload_success):
        """Log capture metadata for tracking."""
        metadata = {
            'timestamp': datetime.now().isoformat(),
            'filename': filename,
            'local_path': str(image_path),
            'upload_success': upload_success,
            'capture_count': self.capture_count,
            'settings': self._get_capture_settings()
        }
        
        logger.info(f"📊 Capture metadata: {metadata}")
        
        # TODO: Store metadata in database or log file
        # This could be stored in the captures table or a separate log file
    
    def run_single_capture(self):
        """Run a single capture cycle."""
        logger.info("🔄 Starting capture cycle...")
        
        # Create filename
        filename = self._create_capture_filename()
        
        # Capture image
        image_path = self._capture_image(filename)
        
        # Upload to Supabase
        upload_success = self._upload_to_supabase(image_path, filename)
        
        # Log metadata
        self._log_capture_metadata(filename, image_path, upload_success)
        
        logger.info("✅ Capture cycle completed")
        return upload_success
    
    def run_continuous(self, max_captures=None):
        """
        Run continuous captures at the specified interval.
        
        Args:
            max_captures: Maximum number of captures to perform (None for unlimited)
        """
        settings = self._get_capture_settings()
        interval_sec = settings['interval_sec']
        
        logger.info(f"🚀 Starting PiLab test script")
        logger.info(f"📋 Settings: {settings}")
        logger.info(f"⏱️  Interval: {interval_sec} seconds ({interval_sec/60:.1f} minutes)")
        logger.info(f"🎯 Max captures: {max_captures if max_captures else 'Unlimited'}")
        
        self.start_time = datetime.now()
        capture_count = 0
        
        try:
            while True:
                # Check if we've reached max captures
                if max_captures and capture_count >= max_captures:
                    logger.info(f"🎯 Reached maximum captures ({max_captures})")
                    break
                
                # Run capture cycle
                success = self.run_single_capture()
                capture_count += 1
                
                if not success:
                    logger.warning("⚠️  Capture cycle had issues, but continuing...")
                
                # Calculate next capture time
                next_capture = datetime.now().timestamp() + interval_sec
                next_capture_time = datetime.fromtimestamp(next_capture)
                
                logger.info(f"⏰ Next capture at: {next_capture_time.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # Wait for next capture
                time.sleep(interval_sec)
                
        except KeyboardInterrupt:
            logger.info("🛑 Test script interrupted by user")
        except Exception as e:
            logger.error(f"❌ Test script error: {e}")
        finally:
            self._log_final_stats(capture_count)
    
    def _log_final_stats(self, total_captures):
        """Log final statistics."""
        if self.start_time:
            duration = datetime.now() - self.start_time
            logger.info(f"📊 Final Statistics:")
            logger.info(f"   Total captures: {total_captures}")
            logger.info(f"   Duration: {duration}")
            logger.info(f"   Average interval: {duration.total_seconds() / max(total_captures, 1):.1f} seconds")


def main():
    """Main entry point for the test script."""
    print("🔬 PiLab Test Script - 10-Minute Interval Capture & Supabase Sync")
    print("=" * 70)
    
    # Parse command line arguments
    import argparse
    parser = argparse.ArgumentParser(description='PiLab Test Script')
    parser.add_argument('--max-captures', type=int, help='Maximum number of captures to perform')
    parser.add_argument('--single', action='store_true', help='Run a single capture and exit')
    args = parser.parse_args()
    
    # Create and run test script
    test_script = PiLabTestScript()
    
    if args.single:
        logger.info("🎯 Running single capture mode")
        test_script.run_single_capture()
    else:
        logger.info("🔄 Running continuous capture mode")
        test_script.run_continuous(max_captures=args.max_captures)


if __name__ == "__main__":
    main() 