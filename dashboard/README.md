# CinePi Dashboard

A modern, responsive web dashboard for controlling CinePi timelapse camera systems. Built with Flask, featuring real-time updates, comprehensive camera controls, and a beautiful user interface.

## 🚀 Features

- **Real-time Camera Control**: Start/stop timelapse sessions, take manual snapshots
- **Camera Settings Management**: Adjust exposure, ISO, gain, and resolution
- **Live Preview**: MJPEG stream for real-time camera preview
- **Real-time Status Updates**: WebSocket-powered live status monitoring
- **Capture Management**: View, download, and delete capture files
- **Configuration Management**: YAML-based configuration with backup/restore
- **Responsive Design**: Mobile-first design optimized for tablets and touchscreens
- **Modern UI**: Dark theme with intuitive controls and real-time feedback

## 📋 Requirements

- Python 3.8+
- CinePi modules (timing, camera, capture)
- Flask and related dependencies
- Camera hardware (Raspberry Pi Camera Module or compatible)

## 🛠️ Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd cinepi-dashboard
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure CinePi
Ensure your CinePi modules are properly installed and configured:
```bash
# Verify CinePi modules are available
python3 -m cinepi.timing --help
python3 -m cinepi.camera --help
python3 -m cinepi.capture --help
```

### 4. Set Up File Permissions
```bash
# Create necessary directories
sudo mkdir -p /opt/cinepi/config
sudo mkdir -p /opt/cinepi/captures
sudo mkdir -p /var/log/cinepi-dashboard

# Set permissions
sudo chown -R $USER:$USER /opt/cinepi
sudo chmod 755 /opt/cinepi/config
sudo chmod 755 /opt/cinepi/captures
```

### 5. Start the Dashboard
```bash
python run_dashboard.py
```

The dashboard will be available at `http://localhost:5000`

## 🎯 Quick Start

### 1. Access the Dashboard
Open your web browser and navigate to `http://localhost:5000`

### 2. Check System Status
The dashboard will display:
- Camera connection status
- Current session information
- System resource usage
- Recent captures

### 3. Start a Timelapse Session
1. Set your desired interval (1-3600 seconds)
2. Click "Start Timelapse"
3. Monitor progress in real-time

### 4. Adjust Camera Settings
1. Navigate to the Camera Settings panel
2. Adjust exposure mode, ISO, gain, or resolution
3. Click "Update Settings" to apply changes

### 5. Take Manual Snapshots
Click "Take Snapshot" for immediate capture

## 📚 Documentation

### API Documentation
Complete REST API and WebSocket documentation: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)

### Integration Points
Detailed integration documentation: [INTEGRATION_POINTS.md](INTEGRATION_POINTS.md)

### API Endpoints Overview

#### Capture Control
- `POST /api/capture/start` - Start timelapse session
- `POST /api/capture/stop` - Stop timelapse session
- `GET /api/capture/status` - Get session status
- `GET /api/capture/list` - List recent captures
- `DELETE /api/capture/delete/<filename>` - Delete capture file
- `PUT /api/capture/interval` - Update capture interval
- `POST /api/capture/manual` - Take manual snapshot

#### Camera Settings
- `GET /api/camera/settings` - Get current settings
- `PUT /api/camera/settings` - Update camera settings

#### System Status
- `GET /api/status` - Get system status
- `GET /api/status/stream` - Stream real-time updates (SSE)
- `GET /api/logs` - Get system logs

#### Configuration
- `GET /api/config` - Get configuration
- `PUT /api/config` - Update configuration
- `POST /api/config/backup` - Create backup
- `POST /api/config/restore` - Restore from backup

## 🏗️ Architecture

### Directory Structure
```
dashboard/
├── app.py                 # Flask application factory
├── config.py             # Configuration management
├── extensions.py         # Flask extensions
├── routes/               # Route definitions
│   ├── api.py           # REST API endpoints
│   ├── main.py          # Main dashboard routes
│   └── websocket.py     # WebSocket event handlers
├── services/             # Business logic services
│   ├── capture_service.py    # Timelapse control
│   ├── camera_service.py     # Camera operations
│   ├── config_service.py     # Configuration management
│   └── websocket_service.py  # Real-time updates
├── static/               # Static assets
│   ├── css/             # Stylesheets
│   └── js/              # JavaScript files
├── templates/            # HTML templates
├── utils/                # Utility functions
└── tests/                # Test suite
```

### Service Layer
- **CaptureService**: Manages timelapse sessions and capture files
- **CameraService**: Handles camera control and settings
- **ConfigService**: Manages configuration files and backups
- **WebSocketService**: Provides real-time status updates

### Integration Points
- **CinePi Modules**: Subprocess integration with timing, camera, and capture modules
- **File System**: Configuration files, capture storage, and log management
- **WebSocket**: Real-time communication for live updates

## 🔧 Configuration

### Environment Variables
```bash
# Dashboard configuration
FLASK_ENV=production
FLASK_DEBUG=false
DASHBOARD_HOST=0.0.0.0
DASHBOARD_PORT=5000

# CinePi paths
CINEPI_CONFIG_PATH=/opt/cinepi/config/cinepi.yaml
CINEPI_CAPTURES_PATH=/opt/cinepi/captures
CINEPI_LOGS_PATH=/var/log/cinepi
```

### Configuration File
The dashboard uses the CinePi configuration file at `/opt/cinepi/config/cinepi.yaml`:

```yaml
camera:
  exposure_mode: auto
  iso: 400
  gain: 2.0
  resolution: 4056x3040

capture:
  interval: 30
  output_format: jpg
  quality: 95

system:
  log_level: info
  backup_enabled: true
```

## 🧪 Testing

### Run Tests
```bash
# Run all tests
python -m pytest

# Run specific test categories
python -m pytest tests/test_api.py
python -m pytest tests/test_services.py
python -m pytest tests/test_integration.py
```

### Manual Testing
```bash
# Test API endpoints
curl -X POST http://localhost:5000/api/capture/start \
  -H "Content-Type: application/json" \
  -d '{"interval": 30}'

curl -X GET http://localhost:5000/api/camera/settings

# Test WebSocket connection
wscat -c ws://localhost:5000/socket.io/
```

## 🚀 Deployment

### Development
```bash
python run_dashboard.py
```

### Production with Gunicorn
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "dashboard.app:create_app()"
```

### Systemd Service
Create `/etc/systemd/system/cinepi-dashboard.service`:
```ini
[Unit]
Description=CinePi Dashboard
After=network.target

[Service]
Type=simple
User=cinepi
WorkingDirectory=/opt/cinepi/dashboard
Environment=PATH=/opt/cinepi/venv/bin
ExecStart=/opt/cinepi/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 "dashboard.app:create_app()"
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl enable cinepi-dashboard
sudo systemctl start cinepi-dashboard
```

## 🔒 Security

### Current Security Measures
- Input validation for all API endpoints
- Filename validation to prevent path traversal
- Subprocess security with explicit command arrays
- Error message sanitization

### Recommended Security Enhancements
- Implement user authentication and authorization
- Add rate limiting for API endpoints
- Use HTTPS in production
- Implement API key authentication for external access

## 🐛 Troubleshooting

### Common Issues

#### Camera Not Connected
- Verify camera hardware is properly connected
- Check CinePi camera module is working: `python3 -m cinepi.camera status`
- Review system logs: `tail -f /var/log/cinepi-dashboard/app.log`

#### Permission Errors
- Check file permissions: `ls -la /opt/cinepi/`
- Ensure dashboard user has access to CinePi directories
- Verify log directory permissions

#### WebSocket Connection Issues
- Check firewall settings for WebSocket port
- Verify browser supports WebSocket connections
- Review browser console for connection errors

#### Configuration Errors
- Validate YAML syntax in configuration file
- Restore from backup if configuration is corrupted
- Check configuration file permissions

### Debug Mode
Enable debug mode for detailed error information:
```bash
export FLASK_DEBUG=true
python run_dashboard.py
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and add tests
4. Run the test suite: `python -m pytest`
5. Commit your changes: `git commit -am 'Add feature'`
6. Push to the branch: `git push origin feature-name`
7. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with Flask web framework
- Real-time updates powered by Flask-SocketIO
- Modern UI components and responsive design
- Integration with CinePi timelapse camera system

## 📞 Support

For support and questions:
- Create an issue on GitHub
- Check the troubleshooting guide
- Review the detailed documentation
- Contact the development team

---

*CinePi Dashboard v1.0.0 - Professional timelapse camera control system* 