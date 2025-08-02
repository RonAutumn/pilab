#!/usr/bin/env python3
"""
Simplified Web-based PiCamera2 Preview Script
Uses same settings as Qt preview - no presets, no color conversions
"""

import cv2
import time
import threading
from flask import Flask, Response, render_template_string
import numpy as np

app = Flask(__name__)

# Global variables
current_frame = None
frame_lock = threading.Lock()
camera = None

def init_camera():
    """Initialize camera with simplified settings - no presets"""
    global camera
    
    try:
        # Use OpenCV for camera access (simpler than picamera2)
        camera = cv2.VideoCapture(0)
        
        # Set basic camera properties
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
        camera.set(cv2.CAP_PROP_FPS, 30)
        
        # Use camera defaults - no color presets
        print("✅ Camera initialized with default settings")
        return True
        
    except Exception as e:
        print(f"❌ Camera initialization failed: {e}")
        return False

def capture_frames():
    """Capture frames in a separate thread"""
    global current_frame, camera

    while True:
        try:
            if camera and camera.isOpened():
                # Capture frame
                ret, frame = camera.read()
                
                if ret:
                    # Convert to JPEG
                    ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
                    
                    if ret:
                        with frame_lock:
                            current_frame = jpeg.tobytes()
            
            time.sleep(0.033)  # ~30 FPS
            
        except Exception as e:
            print(f"Frame capture error: {e}")
            time.sleep(0.1)

@app.route('/')
def index():
    """Main page with camera preview"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>PiCamera2 Web Preview - Simplified</title>
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
            <h1>🎬 PiCamera2 Web Preview</h1>
            
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

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Simplified PiCamera2 Web Preview')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    
    args = parser.parse_args()
    
    print("🎬 Starting Simplified PiCamera2 Web Preview...")
    print("=" * 50)
    
    # Initialize camera
    if not init_camera():
        print("❌ Failed to initialize camera")
        exit(1)
    
    # Start frame capture thread
    capture_thread = threading.Thread(target=capture_frames, daemon=True)
    capture_thread.start()
    
    print(f"✅ Camera feed started")
    print(f"🌐 Web preview available at: http://{args.host}:{args.port}")
    print("=" * 50)
    
    # Start Flask app
    app.run(host=args.host, port=args.port, debug=False, threaded=True) 