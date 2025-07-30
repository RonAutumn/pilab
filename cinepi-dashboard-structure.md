# CinePi Dashboard File Structure & Scaffolding Plan

## Overview
This document defines the directory structure, entry point, routing, and integration plan for the CinePi dashboard application. The structure is designed for Flask + HTMX with modular components, clear separation of concerns, and integration with existing CinePi modules.

## Design Principles
- **Modular Architecture**: Separate concerns between UI, business logic, and integration layers
- **Flask + HTMX**: Server-side rendering with real-time updates via WebSocket
- **Raspberry Pi Optimization**: Lightweight, efficient structure for Pi 5 hardware
- **Extensibility**: Plugin-ready architecture for future features
- **Integration**: Seamless connection with existing CinePi camera and timing modules

---

## Directory Structure

```
cinepi/
├── dashboard/                          # Main dashboard application
│   ├── __init__.py                     # Dashboard package initialization
│   ├── app.py                          # Flask application entry point
│   ├── config.py                       # Configuration management
│   ├── extensions.py                   # Flask extensions (WebSocket, etc.)
│   │
│   ├── routes/                         # Route definitions and handlers
│   │   ├── __init__.py
│   │   ├── main.py                     # Main dashboard routes
│   │   ├── api.py                      # REST API endpoints
│   │   ├── websocket.py                # WebSocket event handlers
│   │   └── static.py                   # Static file serving
│   │
│   ├── templates/                      # HTML templates (Jinja2)
│   │   ├── base.html                   # Base template with layout
│   │   ├── dashboard.html              # Main dashboard page
│   │   ├── components/                 # Reusable UI components
│   │   │   ├── live_preview.html       # Live preview panel
│   │   │   ├── control_panel.html      # Capture controls
│   │   │   ├── camera_settings.html    # Camera settings panel
│   │   │   ├── session_feedback.html   # Session monitoring
│   │   │   ├── timeline_browser.html   # Image timeline
│   │   │   ├── config_editor.html      # YAML configuration
│   │   │   └── live_logs.html          # Log streaming
│   │   └── partials/                   # HTMX partials
│   │       ├── status_updates.html     # Real-time status
│   │       ├── log_entries.html        # Log entries
│   │       └── timeline_items.html     # Timeline updates
│   │
│   ├── static/                         # Static assets
│   │   ├── css/                        # Stylesheets
│   │   │   ├── main.css                # Main styles
│   │   │   ├── components.css          # Component styles
│   │   │   └── responsive.css          # Responsive design
│   │   ├── js/                         # JavaScript files
│   │   │   ├── app.js                  # Main application logic
│   │   │   ├── websocket.js            # WebSocket handling
│   │   │   ├── components.js           # Component interactions
│   │   │   └── utils.js                # Utility functions
│   │   ├── images/                     # Images and icons
│   │   └── vendor/                     # Third-party libraries
│   │       ├── bootstrap/              # Bootstrap 5
│   │       ├── htmx/                   # HTMX library
│   │       ├── alpine/                 # Alpine.js
│   │       └── monaco/                 # Monaco Editor
│   │
│   ├── services/                       # Business logic and integration
│   │   ├── __init__.py
│   │   ├── camera_service.py           # Camera control integration
│   │   ├── capture_service.py          # Timelapse capture logic
│   │   ├── config_service.py           # Configuration management
│   │   ├── log_service.py              # Log streaming service
│   │   ├── websocket_service.py        # WebSocket event handling
│   │   └── file_service.py             # File management (images, configs)
│   │
│   ├── models/                         # Data models and schemas
│   │   ├── __init__.py
│   │   ├── camera.py                   # Camera settings model
│   │   ├── session.py                  # Session state model
│   │   ├── capture.py                  # Capture metadata model
│   │   └── config.py                   # Configuration model
│   │
│   ├── utils/                          # Utility functions
│   │   ├── __init__.py
│   │   ├── validators.py               # Input validation
│   │   ├── formatters.py               # Data formatting
│   │   ├── thumbnails.py               # Thumbnail generation
│   │   └── security.py                 # Security utilities
│   │
│   ├── plugins/                        # Plugin system (future extensibility)
│   │   ├── __init__.py
│   │   └── base.py                     # Plugin base class
│   │
│   └── tests/                          # Test suite
│       ├── __init__.py
│       ├── test_routes.py              # Route testing
│       ├── test_services.py            # Service testing
│       ├── test_models.py              # Model testing
│       └── test_integration.py         # Integration testing
│
├── requirements.txt                    # Python dependencies
├── dashboard_config.yaml              # Dashboard configuration
├── run_dashboard.py                   # Dashboard launcher script
└── README_dashboard.md                # Dashboard documentation
```

---

## Key Files and Their Purposes

### Entry Point: `dashboard/app.py`
```python
from flask import Flask
from flask_socketio import SocketIO
from dashboard.extensions import init_extensions
from dashboard.routes import init_routes
from dashboard.services import init_services

def create_app(config_name='default'):
    """Application factory pattern for Flask app creation"""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(f'dashboard.config.{config_name.capitalize()}Config')
    
    # Initialize extensions
    init_extensions(app)
    
    # Initialize services
    init_services(app)
    
    # Register routes
    init_routes(app)
    
    return app

if __name__ == '__main__':
    app = create_app()
    socketio = SocketIO(app)
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
```

### Configuration: `dashboard/config.py`
```python
import os
from pathlib import Path

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    DASHBOARD_ROOT = Path(__file__).parent.parent
    STATIC_FOLDER = DASHBOARD_ROOT / 'dashboard' / 'static'
    TEMPLATE_FOLDER = DASHBOARD_ROOT / 'dashboard' / 'templates'
    
    # CinePi integration paths
    CINEPI_ROOT = Path('/opt/cinepi')
    CONFIG_PATH = CINEPI_ROOT / 'config' / 'cinepi.yaml'
    CAPTURES_PATH = CINEPI_ROOT / 'captures'
    LOGS_PATH = CINEPI_ROOT / 'logs'
    
    # WebSocket configuration
    SOCKETIO_MESSAGE_QUEUE = 'redis://localhost:6379/0'
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'yaml', 'yml'}

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    # Add production-specific settings

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    WTF_CSRF_ENABLED = False
```

### Extensions: `dashboard/extensions.py`
```python
from flask_socketio import SocketIO
from flask_compress import Compress

socketio = SocketIO()
compress = Compress()

def init_extensions(app):
    """Initialize Flask extensions"""
    socketio.init_app(app, cors_allowed_origins="*")
    compress.init_app(app)
```

### Main Routes: `dashboard/routes/main.py`
```python
from flask import Blueprint, render_template, current_app
from dashboard.services.camera_service import CameraService
from dashboard.services.session_service import SessionService

main = Blueprint('main', __name__)

@main.route('/')
def dashboard():
    """Main dashboard page"""
    camera_service = CameraService()
    session_service = SessionService()
    
    context = {
        'camera_status': camera_service.get_status(),
        'session_info': session_service.get_session_info(),
        'config': current_app.config
    }
    
    return render_template('dashboard.html', **context)

@main.route('/stream')
def mjpeg_stream():
    """MJPEG stream endpoint"""
    return current_app.camera_service.get_mjpeg_stream()

@main.route('/snapshot')
def snapshot():
    """Manual snapshot endpoint"""
    return current_app.camera_service.take_snapshot()
```

### API Routes: `dashboard/routes/api.py`
```python
from flask import Blueprint, request, jsonify
from dashboard.services.capture_service import CaptureService
from dashboard.services.camera_service import CameraService
from dashboard.services.config_service import ConfigService

api = Blueprint('api', __name__, url_prefix='/api')

@api.route('/capture/start', methods=['POST'])
def start_capture():
    """Start timelapse capture"""
    data = request.get_json()
    interval = data.get('interval', 30)
    
    capture_service = CaptureService()
    result = capture_service.start_session(interval)
    
    return jsonify(result)

@api.route('/capture/stop', methods=['POST'])
def stop_capture():
    """Stop timelapse capture"""
    capture_service = CaptureService()
    result = capture_service.stop_session()
    
    return jsonify(result)

@api.route('/camera/settings', methods=['GET', 'PUT'])
def camera_settings():
    """Get or update camera settings"""
    camera_service = CameraService()
    
    if request.method == 'GET':
        return jsonify(camera_service.get_settings())
    else:
        data = request.get_json()
        result = camera_service.update_settings(data)
        return jsonify(result)

@api.route('/config', methods=['GET', 'PUT'])
def config():
    """Get or update configuration"""
    config_service = ConfigService()
    
    if request.method == 'GET':
        return jsonify(config_service.get_config())
    else:
        data = request.get_json()
        result = config_service.update_config(data)
        return jsonify(result)
```

### WebSocket Routes: `dashboard/routes/websocket.py`
```python
from flask_socketio import emit, join_room, leave_room
from dashboard.routes import socketio
from dashboard.services.websocket_service import WebSocketService

@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print('Client connected')
    emit('status', {'message': 'Connected to CinePi Dashboard'})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print('Client disconnected')

@socketio.on('join_dashboard')
def handle_join_dashboard():
    """Join dashboard room for real-time updates"""
    join_room('dashboard')
    emit('joined', {'room': 'dashboard'})

@socketio.on('request_status')
def handle_status_request():
    """Send current status to client"""
    ws_service = WebSocketService()
    status = ws_service.get_current_status()
    emit('status_update', status)
```

### Camera Service: `dashboard/services/camera_service.py`
```python
import subprocess
import json
from pathlib import Path
from dashboard.models.camera import CameraSettings

class CameraService:
    """Service for camera control and integration"""
    
    def __init__(self):
        self.config_path = Path('/opt/cinepi/config/cinepi.yaml')
        self.captures_path = Path('/opt/cinepi/captures')
    
    def get_status(self):
        """Get current camera status"""
        # Integration with existing CinePi camera module
        try:
            # Call existing CinePi camera status function
            result = subprocess.run(['python3', '-m', 'cinepi.camera', 'status'], 
                                  capture_output=True, text=True)
            return json.loads(result.stdout)
        except Exception as e:
            return {'error': str(e), 'status': 'unknown'}
    
    def get_settings(self):
        """Get current camera settings"""
        # Load from existing CinePi config
        settings = CameraSettings()
        settings.load_from_file(self.config_path)
        return settings.to_dict()
    
    def update_settings(self, new_settings):
        """Update camera settings"""
        settings = CameraSettings()
        settings.update_from_dict(new_settings)
        settings.save_to_file(self.config_path)
        
        # Apply settings to camera
        self._apply_camera_settings(settings)
        return {'success': True, 'message': 'Settings updated'}
    
    def get_mjpeg_stream(self):
        """Get MJPEG stream response"""
        # Integration with existing CinePi streaming
        from flask import Response
        import cv2
        
        def generate_frames():
            # Use existing CinePi camera stream
            cap = cv2.VideoCapture(0)  # Or CinePi camera instance
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Convert frame to JPEG
                ret, buffer = cv2.imencode('.jpg', frame)
                if not ret:
                    continue
                
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + buffer.tobytes() + b'\r\n')
        
        return Response(generate_frames(),
                       mimetype='multipart/x-mixed-replace; boundary=frame')
    
    def take_snapshot(self):
        """Take manual snapshot"""
        # Integration with existing CinePi capture module
        try:
            result = subprocess.run(['python3', '-m', 'cinepi.capture', 'manual'], 
                                  capture_output=True, text=True)
            return json.loads(result.stdout)
        except Exception as e:
            return {'error': str(e)}
    
    def _apply_camera_settings(self, settings):
        """Apply settings to camera hardware"""
        # Integration with existing CinePi camera control
        pass
```

### Capture Service: `dashboard/services/capture_service.py`
```python
import subprocess
import json
from datetime import datetime
from dashboard.models.session import Session

class CaptureService:
    """Service for timelapse capture control"""
    
    def __init__(self):
        self.session = None
    
    def start_session(self, interval):
        """Start timelapse capture session"""
        try:
            # Integration with existing CinePi timing controller
            result = subprocess.run([
                'python3', '-m', 'cinepi.timing', 'start', 
                '--interval', str(interval)
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.session = Session(
                    start_time=datetime.now(),
                    interval=interval,
                    status='active'
                )
                return {'success': True, 'message': 'Session started'}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def stop_session(self):
        """Stop timelapse capture session"""
        try:
            # Integration with existing CinePi timing controller
            result = subprocess.run([
                'python3', '-m', 'cinepi.timing', 'stop'
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                if self.session:
                    self.session.status = 'stopped'
                    self.session.end_time = datetime.now()
                return {'success': True, 'message': 'Session stopped'}
            else:
                return {'success': False, 'error': result.stderr}
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_session_info(self):
        """Get current session information"""
        if not self.session:
            return {'status': 'inactive', 'captures': 0}
        
        # Get capture count from file system
        captures_path = Path('/opt/cinepi/captures')
        capture_count = len(list(captures_path.glob('*.jpg')))
        
        return {
            'status': self.session.status,
            'start_time': self.session.start_time.isoformat(),
            'interval': self.session.interval,
            'captures': capture_count
        }
```

### Configuration Service: `dashboard/services/config_service.py`
```python
import yaml
from pathlib import Path
from dashboard.models.config import Config

class ConfigService:
    """Service for configuration management"""
    
    def __init__(self):
        self.config_path = Path('/opt/cinepi/config/cinepi.yaml')
        self.backup_path = Path('/opt/cinepi/config/backups')
        self.backup_path.mkdir(exist_ok=True)
    
    def get_config(self):
        """Load configuration from file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            return {'error': str(e)}
    
    def update_config(self, new_config):
        """Update configuration file"""
        try:
            # Validate configuration
            config = Config()
            config.load_from_dict(new_config)
            
            # Create backup
            self._create_backup()
            
            # Save new configuration
            with open(self.config_path, 'w') as f:
                yaml.dump(new_config, f, default_flow_style=False)
            
            return {'success': True, 'message': 'Configuration updated'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_backup(self):
        """Create configuration backup"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_path / f'cinepi_backup_{timestamp}.yaml'
            
            with open(self.config_path, 'r') as src, open(backup_file, 'w') as dst:
                dst.write(src.read())
            
            return {'success': True, 'backup_file': str(backup_file)}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def restore_backup(self, backup_file):
        """Restore configuration from backup"""
        try:
            backup_path = self.backup_path / backup_file
            
            if not backup_path.exists():
                return {'success': False, 'error': 'Backup file not found'}
            
            # Create backup of current config
            self._create_backup()
            
            # Restore from backup
            with open(backup_path, 'r') as src, open(self.config_path, 'w') as dst:
                dst.write(src.read())
            
            return {'success': True, 'message': 'Configuration restored'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _create_backup(self):
        """Create automatic backup"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = self.backup_path / f'cinepi_auto_backup_{timestamp}.yaml'
        
        with open(self.config_path, 'r') as src, open(backup_file, 'w') as dst:
            dst.write(src.read())
```

---

## Integration Strategy

### 1. Existing CinePi Module Integration
```python
# dashboard/services/integration.py
"""
Integration layer for existing CinePi modules
"""

import sys
from pathlib import Path

# Add CinePi modules to path
CINEPI_ROOT = Path('/opt/cinepi')
sys.path.insert(0, str(CINEPI_ROOT))

# Import existing CinePi modules
try:
    from cinepi.camera import Camera
    from cinepi.timing import TimingController
    from cinepi.config import ConfigManager
    from cinepi.capture import CaptureManager
except ImportError as e:
    print(f"Warning: Could not import CinePi modules: {e}")

class CinePiIntegration:
    """Integration wrapper for existing CinePi modules"""
    
    def __init__(self):
        self.camera = None
        self.timing = None
        self.config = None
        self.capture = None
        
        self._initialize_modules()
    
    def _initialize_modules(self):
        """Initialize CinePi modules"""
        try:
            self.camera = Camera()
            self.timing = TimingController()
            self.config = ConfigManager()
            self.capture = CaptureManager()
        except Exception as e:
            print(f"Warning: Could not initialize CinePi modules: {e}")
    
    def get_camera_status(self):
        """Get camera status from existing module"""
        if self.camera:
            return self.camera.get_status()
        return {'error': 'Camera module not available'}
    
    def start_timelapse(self, interval):
        """Start timelapse using existing timing controller"""
        if self.timing:
            return self.timing.start_session(interval)
        return {'error': 'Timing module not available'}
```

### 2. WebSocket Integration
```python
# dashboard/services/websocket_service.py
"""
WebSocket service for real-time updates
"""

import asyncio
import json
from datetime import datetime
from flask_socketio import emit
from dashboard.routes import socketio

class WebSocketService:
    """Service for WebSocket event handling and broadcasting"""
    
    def __init__(self):
        self.clients = set()
        self.update_interval = 1.0  # seconds
    
    def broadcast_status(self, status_data):
        """Broadcast status update to all connected clients"""
        socketio.emit('status_update', status_data, room='dashboard')
    
    def broadcast_log(self, log_entry):
        """Broadcast log entry to all connected clients"""
        socketio.emit('log_entry', {
            'timestamp': datetime.now().isoformat(),
            'message': log_entry
        }, room='dashboard')
    
    def broadcast_capture_update(self, capture_info):
        """Broadcast capture update to all connected clients"""
        socketio.emit('capture_update', capture_info, room='dashboard')
    
    def get_current_status(self):
        """Get current system status for new connections"""
        # This would integrate with existing CinePi status
        return {
            'camera_status': 'active',
            'session_status': 'running',
            'capture_count': 47,
            'next_capture': '00:12'
        }
```

---

## Application Entry Point: `run_dashboard.py`
```python
#!/usr/bin/env python3
"""
CinePi Dashboard Launcher Script
"""

import os
import sys
from pathlib import Path
from dashboard.app import create_app
from dashboard.extensions import socketio

def main():
    """Main entry point for CinePi Dashboard"""
    
    # Set up environment
    os.environ.setdefault('FLASK_ENV', 'development')
    
    # Create application
    app = create_app()
    
    # Run with SocketIO
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )

if __name__ == '__main__':
    main()
```

---

## Requirements: `requirements.txt`
```
# Core Flask dependencies
Flask==2.3.3
Flask-SocketIO==5.3.6
Flask-Compress==1.14

# CinePi integration
PyYAML==6.0.1
opencv-python==4.8.1.78

# WebSocket and real-time
python-socketio==5.9.0
eventlet==0.33.3

# Development and testing
pytest==7.4.2
pytest-flask==1.3.0
black==23.9.1
flake8==6.1.0

# Production
gunicorn==21.2.0
```

---

## Configuration: `dashboard_config.yaml`
```yaml
# CinePi Dashboard Configuration

dashboard:
  name: "CinePi Dashboard"
  version: "1.0.0"
  debug: false
  
  # Server settings
  host: "0.0.0.0"
  port: 5000
  
  # Security
  secret_key: "your-secret-key-here"
  csrf_enabled: true
  
  # File paths
  cinepi_root: "/opt/cinepi"
  config_path: "/opt/cinepi/config/cinepi.yaml"
  captures_path: "/opt/cinepi/captures"
  logs_path: "/opt/cinepi/logs"
  
  # WebSocket settings
  socketio_message_queue: "redis://localhost:6379/0"
  
  # Camera settings
  max_resolution: "4056x3040"
  supported_resolutions:
    - "4056x3040"
    - "2028x1520"
    - "1014x760"
  
  # Capture settings
  min_interval: 5  # seconds
  max_interval: 3600  # seconds (1 hour)
  default_interval: 30  # seconds
  
  # UI settings
  theme: "light"
  auto_refresh: true
  refresh_interval: 1000  # milliseconds
```

---

## Next Steps

1. **Implementation**: Create the directory structure and scaffold files
2. **Integration Testing**: Test integration with existing CinePi modules
3. **Component Development**: Implement individual UI components
4. **Performance Optimization**: Optimize for Raspberry Pi 5
5. **Documentation**: Create user and developer documentation

This file structure provides a solid foundation for the CinePi dashboard, ensuring modularity, extensibility, and seamless integration with existing CinePi functionality while maintaining the Flask + HTMX architecture chosen for optimal Raspberry Pi performance. 