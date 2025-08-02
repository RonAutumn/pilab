#!/usr/bin/env python3
"""
Simplified Web-based Camera Preview Script
Uses picamera2 with simplified settings - no presets, no color conversions
"""

import time
import threading
from flask import Flask, Response, render_template_string
import numpy as np

# Add src directory to Python path for imports
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    from picamera2 import Picamera2
    from libcamera import controls
    PICAMERA_AVAILABLE = True
except ImportError:
    PICAMERA_AVAILABLE = False
    Picamera2 = None
    controls = None

app = Flask(__name__)

# Global variables
current_frame = None
frame_lock = threading.Lock()
camera = None

def init_camera():
    """Initialize camera with simplified settings - no presets"""
    global camera
    
    try:
        # Use picamera2 with simplified settings
        camera = Picamera2()
        
        # Create simple configuration - no presets, no color conversions
        config = camera.create_still_configuration(
            main={"size": (1920, 1080)}
        )
        
        # Configure camera with minimal settings
        camera.configure(config)
        camera.start()
        
        # Use camera defaults - no color presets
        print('✅ Camera initialized with default settings')
        return True
        
    except Exception as e:
        print(f'❌ Camera initialization failed: {e}')
        return False

def capture_frames():
    """Capture frames in a separate thread"""
    global current_frame, camera

    while True:
        try:
            if camera:
                # Capture frame using picamera2
                frame = camera.capture_array()
                
                if frame is not None:
                    # Convert to JPEG using PIL
                    from PIL import Image
                    img = Image.fromarray(frame)
                    
                    # Save to bytes
                    import io
                    img_byte_arr = io.BytesIO()
                    img.save(img_byte_arr, format='JPEG', quality=85)
                    img_byte_arr = img_byte_arr.getvalue()
                    
                    with frame_lock:
                        current_frame = img_byte_arr
            
            time.sleep(0.033)  # ~30 FPS
            
        except Exception as e:
            print(f'Frame capture error: {e}')
            time.sleep(0.1)

@app.route('/')
def index():
    """Main page with camera preview"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Camera Web Preview - Simplified</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                margin: 20px; 
                background: #f0f0f0;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 { 
                color: #333; 
                text-align: center;
                margin-bottom: 30px;
            }
            .camera-feed {
                text-align: center;
                margin: 20px 0;
            }
            .camera-feed img {
                max-width: 100%;
                border: 2px solid #ddd;
                border-radius: 8px;
            }
            .status {
                text-align: center;
                padding: 10px;
                background: #e8f5e8;
                border-radius: 5px;
                margin: 20px 0;
                color: #2d5a2d;
            }
            .info {
                background: #f8f9fa;
                padding: 15px;
                border-radius: 5px;
                margin: 20px 0;
                border-left: 4px solid #007bff;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎬 Camera Web Preview</h1>
            
            <div class="status">
                ✅ <strong>Simplified Camera Settings</strong> - No presets, no color conversions
            </div>
            
            <div class="camera-feed">
                <img src="/video_feed" alt="Camera Feed" />
            </div>
            
            <div class="info">
                <h3>📋 Camera Settings Applied:</h3>
                <ul>
                    <li>✅ <strong>No IMX477 overlay</strong> - Removed from /boot/config.txt</li>
                    <li>✅ <strong>No color presets</strong> - Using camera defaults</li>
                    <li>✅ <strong>No AWB overrides</strong> - Natural white balance</li>
                    <li>✅ <strong>No format forcing</strong> - Native camera format</li>
                    <li>✅ <strong>No color conversions</strong> - Direct capture</li>
                </ul>
            </div>
            
            <div class="info">
                <h3>🔧 Technical Details:</h3>
                <ul>
                    <li><strong>Resolution:</strong> 1920x1080</li>
                    <li><strong>Frame Rate:</strong> 30 FPS</li>
                    <li><strong>Quality:</strong> 85% JPEG</li>
                    <li><strong>Color Space:</strong> Native (no conversions)</li>
                    <li><strong>Camera Library:</strong> picamera2 (same as Qt preview)</li>
                </ul>
            </div>
        </div>
        
        <script>
            // Auto-refresh image every 100ms for smooth video
            setInterval(function() {
                var img = document.querySelector('.camera-feed img');
                img.src = '/video_feed?' + new Date().getTime();
            }, 100);
        </script>
    </body>
    </html>
    """
    return html

@app.route('/video_feed')
def video_feed():
    """Video streaming route"""
    def generate():
        while True:
            with frame_lock:
                if current_frame is not None:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + current_frame + b'\r\n')
            time.sleep(0.033)  # ~30 FPS
    
    return Response(generate(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def main():
    """Main function"""
    print('🎥 Starting Simplified Camera Web Preview...')
    
    # Initialize camera
    if not init_camera():
        print('❌ Failed to initialize camera')
        return False
    
    # Start frame capture thread
    capture_thread = threading.Thread(target=capture_frames, daemon=True)
    capture_thread.start()
    
    print('✅ Camera feed started')
    print('🌐 Web preview available at: http://0.0.0.0:8080')
    
    # Start Flask app
    app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
    
    return True

if __name__ == '__main__':
    main() 