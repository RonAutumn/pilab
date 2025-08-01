#!/usr/bin/env python3
"""
Web-based PiCamera2 Preview Script
Serves camera feed over HTTP so you can view it in a web browser
"""

from picamera2 import Picamera2
from picamera2.encoders import JpegEncoder
from picamera2.outputs import FileOutput
import io
import time
from flask import Flask, Response, render_template_string
import threading

app = Flask(__name__)

# Global variables
picam2 = None
current_frame = None
frame_lock = threading.Lock()

def capture_frames():
    """Capture frames in a separate thread"""
    global current_frame, picam2
    
    while True:
        try:
            # Capture frame
            frame = picam2.capture_array()
            
            # Convert to JPEG
            import cv2
            ret, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            
            if ret:
                with frame_lock:
                    current_frame = jpeg.tobytes()
                    
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
        <title>PiCamera2 Web Preview</title>
        <style>
            body { 
                font-family: Arial, sans-serif; 
                text-align: center; 
                background: #1a1a1a; 
                color: white; 
                margin: 0; 
                padding: 20px; 
            }
            .container { 
                max-width: 800px; 
                margin: 0 auto; 
            }
            h1 { 
                color: #00ff00; 
                margin-bottom: 20px; 
            }
            .camera-feed { 
                border: 3px solid #00ff00; 
                border-radius: 10px; 
                max-width: 100%; 
                height: auto; 
            }
            .status { 
                margin-top: 20px; 
                padding: 10px; 
                background: #333; 
                border-radius: 5px; 
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🎥 PiCamera2 Web Preview</h1>
            <img src="/video_feed" class="camera-feed" alt="Camera Feed">
            <div class="status">
                <p>📡 Live camera feed from Raspberry Pi HQ Camera</p>
                <p>🔄 Auto-refreshing every 100ms</p>
            </div>
        </div>
        <script>
            // Auto-refresh the image every 100ms
            setInterval(function() {
                const img = document.querySelector('.camera-feed');
                img.src = '/video_feed?' + new Date().getTime();
            }, 100);
        </script>
    </body>
    </html>
    """
    return html

@app.route('/video_feed')
def video_feed():
    """MJPEG video stream"""
    def generate():
        while True:
            with frame_lock:
                if current_frame:
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + current_frame + b'\r\n')
                else:
                    # Send a placeholder frame
                    yield (b'--frame\r\n'
                           b'Content-Type: image/jpeg\r\n\r\n' + b'\r\n')
            time.sleep(0.1)  # 10 FPS
    
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

def main():
    global picam2
    
    print("🎥 Starting PiCamera2 Web Preview...")
    
    # Initialize camera
    picam2 = Picamera2()
    
    # Configure camera
    config = picam2.create_preview_configuration(
        main={"size": (640, 480)},
        buffer_count=4
    )
    picam2.configure(config)
    
    # Start camera
    picam2.start()
    print("✅ Camera started successfully")
    
    # Start frame capture thread
    capture_thread = threading.Thread(target=capture_frames, daemon=True)
    capture_thread.start()
    print("✅ Frame capture thread started")
    
    # Start web server
    print("🌐 Starting web server...")
    print("📱 Open your web browser and go to: http://192.168.1.158:8080")
    print("🔄 Press Ctrl+C to stop")
    
    try:
        app.run(host='0.0.0.0', port=8080, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\n🛑 Stopping camera preview...")
    finally:
        picam2.stop()
        print("✅ Camera stopped")

if __name__ == "__main__":
    main() 