# CinePi Dashboard API Documentation

## Overview

The CinePi Dashboard provides a comprehensive REST API and WebSocket interface for controlling timelapse camera operations, managing camera settings, and monitoring system status. This documentation covers all endpoints, service interfaces, and integration points.

## Base URL

All API endpoints are prefixed with `/api` unless otherwise noted.

## Authentication

Currently, the API does not require authentication. All endpoints are publicly accessible.

## Response Format

All API responses follow a consistent JSON format:

### Success Response
```json
{
  "success": true,
  "message": "Operation completed successfully",
  "data": { ... }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error description"
}
```

## HTTP Status Codes

- `200` - Success
- `400` - Bad Request (validation error)
- `404` - Not Found
- `500` - Internal Server Error

---

## REST API Endpoints

### Capture Control Endpoints

#### 1. Start Timelapse Capture
**Endpoint:** `POST /api/capture/start`

**Description:** Start a new timelapse capture session with specified interval.

**Request Body:**
```json
{
  "interval": 30
}
```

**Parameters:**
- `interval` (int, optional): Capture interval in seconds (default: 30, range: 1-3600)

**Response:**
```json
{
  "success": true,
  "message": "Session started with 30s interval",
  "session": {
    "start_time": "2024-01-15T14:30:00",
    "interval": 30,
    "status": "active"
  }
}
```

**Error Responses:**
- `400` - Invalid interval value
- `500` - Session already active or system error

---

#### 2. Stop Timelapse Capture
**Endpoint:** `POST /api/capture/stop`

**Description:** Stop the currently active timelapse capture session.

**Response:**
```json
{
  "success": true,
  "message": "Session stopped",
  "session": {
    "start_time": "2024-01-15T14:30:00",
    "end_time": "2024-01-15T15:30:00",
    "interval": 30,
    "status": "stopped"
  }
}
```

**Error Responses:**
- `500` - No active session or system error

---

#### 3. Get Capture Status
**Endpoint:** `GET /api/capture/status`

**Description:** Get current capture session status and information.

**Response:**
```json
{
  "status": "active",
  "interval": 30,
  "captures": 120,
  "start_time": "2024-01-15T14:30:00",
  "elapsed_time": 3600,
  "next_capture": "2024-01-15T15:30:30"
}
```

---

#### 4. List Recent Captures
**Endpoint:** `GET /api/capture/list`

**Description:** Get list of recent capture files.

**Query Parameters:**
- `limit` (int, optional): Maximum number of captures to return (default: 50, max: 1000)

**Response:**
```json
{
  "success": true,
  "captures": [
    {
      "filename": "cinepi_20240115_143000.jpg",
      "timestamp": "2024-01-15T14:30:00",
      "size": 2048576,
      "path": "/opt/cinepi/captures/cinepi_20240115_143000.jpg"
    }
  ],
  "count": 1
}
```

---

#### 5. Delete Capture File
**Endpoint:** `DELETE /api/capture/delete/<filename>`

**Description:** Delete a specific capture file.

**Parameters:**
- `filename` (string): Name of the file to delete

**Response:**
```json
{
  "success": true,
  "message": "File deleted successfully"
}
```

**Error Responses:**
- `400` - Invalid filename
- `404` - File not found
- `500` - System error

---

#### 6. Update Capture Interval
**Endpoint:** `PUT /api/capture/interval`

**Description:** Update the capture interval during an active session.

**Request Body:**
```json
{
  "interval": 60
}
```

**Parameters:**
- `interval` (int, required): New interval in seconds (range: 1-3600)

**Response:**
```json
{
  "success": true,
  "message": "Interval updated to 60 seconds",
  "session": {
    "interval": 60,
    "status": "active"
  }
}
```

---

#### 7. Take Manual Snapshot
**Endpoint:** `POST /api/capture/manual`

**Description:** Take a manual snapshot immediately.

**Response:**
```json
{
  "success": true,
  "message": "Snapshot taken successfully",
  "filename": "cinepi_20240115_143000.jpg",
  "timestamp": "2024-01-15T14:30:00"
}
```

---

### Camera Settings Endpoints

#### 8. Get Camera Settings
**Endpoint:** `GET /api/camera/settings`

**Description:** Get current camera settings.

**Response:**
```json
{
  "exposure_mode": "auto",
  "iso": 400,
  "gain": 2.0,
  "resolution": "4056x3040",
  "supported_resolutions": [
    "4056x3040",
    "2028x1520",
    "1920x1080"
  ]
}
```

---

#### 9. Update Camera Settings
**Endpoint:** `PUT /api/camera/settings`

**Description:** Update camera settings.

**Request Body:**
```json
{
  "exposure_mode": "manual",
  "iso": 800,
  "gain": 4.0,
  "resolution": "4056x3040"
}
```

**Parameters:**
- `exposure_mode` (string): "auto" or "manual"
- `iso` (int): ISO value (100-800)
- `gain` (float): Gain value (1.0-8.0)
- `resolution` (string): Resolution from supported list

**Response:**
```json
{
  "success": true,
  "message": "Camera settings updated successfully",
  "settings": {
    "exposure_mode": "manual",
    "iso": 800,
    "gain": 4.0,
    "resolution": "4056x3040"
  }
}
```

---

### Status and Monitoring Endpoints

#### 10. Get System Status
**Endpoint:** `GET /api/status`

**Description:** Get comprehensive system status including camera, session, and system information.

**Response:**
```json
{
  "camera": {
    "status": "connected",
    "connected": true,
    "error": null
  },
  "session": {
    "status": "active",
    "interval": 30,
    "captures": 120,
    "elapsed_time": 3600
  },
  "system": {
    "cpu_usage": 15.2,
    "memory_usage": 45.8,
    "disk_usage": 23.1,
    "uptime": 86400,
    "temperature": 45.2
  }
}
```

---

#### 11. Stream Status Updates
**Endpoint:** `GET /api/status/stream`

**Description:** Stream real-time status updates using Server-Sent Events (SSE).

**Response:** Server-Sent Events stream with status updates every 2 seconds.

**Example:**
```
data: {"camera": {...}, "session": {...}, "system": {...}}

data: {"camera": {...}, "session": {...}, "system": {...}}
```

---

#### 12. Get System Logs
**Endpoint:** `GET /api/logs`

**Description:** Get recent system logs.

**Query Parameters:**
- `limit` (int, optional): Maximum number of log entries (default: 50)
- `level` (string, optional): Filter by log level (info, warning, error)

**Response:**
```json
{
  "logs": [
    {
      "timestamp": "2024-01-15T14:30:00",
      "level": "info",
      "message": "Capture session started",
      "module": "capture_service"
    }
  ],
  "count": 1,
  "timestamp": "2024-01-15T14:30:00"
}
```

---

### Configuration Management Endpoints

#### 13. Get Configuration
**Endpoint:** `GET /api/config`

**Description:** Get current CinePi configuration.

**Response:**
```json
{
  "camera": {
    "exposure_mode": "auto",
    "iso": 400,
    "gain": 2.0,
    "resolution": "4056x3040"
  },
  "capture": {
    "interval": 30,
    "output_format": "jpg",
    "quality": 95
  },
  "system": {
    "log_level": "info",
    "backup_enabled": true
  }
}
```

---

#### 14. Update Configuration
**Endpoint:** `PUT /api/config`

**Description:** Update CinePi configuration.

**Request Body:**
```json
{
  "camera": {
    "exposure_mode": "manual",
    "iso": 800
  },
  "capture": {
    "interval": 60
  }
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration updated successfully"
}
```

---

#### 15. Create Configuration Backup
**Endpoint:** `POST /api/config/backup`

**Description:** Create a backup of the current configuration.

**Response:**
```json
{
  "success": true,
  "message": "Backup created successfully",
  "backup_file": "cinepi_backup_20240115_143000.yaml"
}
```

---

#### 16. Restore Configuration Backup
**Endpoint:** `POST /api/config/restore`

**Description:** Restore configuration from a backup file.

**Request Body:**
```json
{
  "backup_file": "cinepi_backup_20240115_143000.yaml"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration restored successfully"
}
```

---

## Main Dashboard Routes

### 17. Dashboard Home
**Endpoint:** `GET /`

**Description:** Main dashboard page with camera control interface.

**Response:** HTML page with dashboard interface.

---

### 18. MJPEG Stream
**Endpoint:** `GET /stream`

**Description:** Live MJPEG stream for camera preview.

**Response:** MJPEG stream response.

---

### 19. Manual Snapshot
**Endpoint:** `GET /snapshot`

**Description:** Take manual snapshot and return image.

**Response:** Image file or JSON error response.

---

### 20. System Status (Legacy)
**Endpoint:** `GET /status`

**Description:** Legacy status endpoint (use `/api/status` for API).

**Response:**
```json
{
  "camera": { ... },
  "session": { ... },
  "system": { ... }
}
```

---

### 21. Health Check
**Endpoint:** `GET /health`

**Description:** Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "service": "cinepi-dashboard",
  "version": "1.0.0"
}
```

---

## WebSocket Events

The dashboard supports real-time communication via WebSocket events.

### Connection Events

#### Connect
**Event:** `connect`

**Description:** Client connects to WebSocket.

**Emitted by:** Server

**Data:**
```json
{
  "message": "Connected to CinePi Dashboard",
  "type": "success"
}
```

#### Disconnect
**Event:** `disconnect`

**Description:** Client disconnects from WebSocket.

**Emitted by:** Server

---

### Room Management Events

#### Join Dashboard
**Event:** `join_dashboard`

**Description:** Join dashboard room for real-time updates.

**Emitted by:** Client

**Response:**
```json
{
  "joined": {"room": "dashboard"},
  "status_update": { ... }
}
```

#### Leave Dashboard
**Event:** `leave_dashboard`

**Description:** Leave dashboard room.

**Emitted by:** Client

**Response:**
```json
{
  "left": {"room": "dashboard"}
}
```

---

### Status and Log Events

#### Request Status
**Event:** `request_status`

**Description:** Request current system status.

**Emitted by:** Client

**Response:**
```json
{
  "status_update": {
    "camera": { ... },
    "session": { ... },
    "system": { ... }
  }
}
```

#### Request Logs
**Event:** `request_logs`

**Description:** Request recent log entries.

**Emitted by:** Client

**Response:**
```json
{
  "log_entries": [
    {
      "timestamp": "2024-01-15T14:30:00",
      "level": "info",
      "message": "Capture session started"
    }
  ]
}
```

---

### Broadcast Events

#### Capture Started
**Event:** `capture_started`

**Description:** Broadcast capture session started.

**Emitted by:** Server (broadcast)

**Data:**
```json
{
  "type": "started",
  "interval": 30,
  "timestamp": "2024-01-15T14:30:00"
}
```

#### Capture Stopped
**Event:** `capture_stopped`

**Description:** Broadcast capture session stopped.

**Emitted by:** Server (broadcast)

**Data:**
```json
{
  "type": "stopped",
  "timestamp": "2024-01-15T15:30:00"
}
```

#### Capture Taken
**Event:** `capture_taken`

**Description:** Broadcast new capture taken.

**Emitted by:** Server (broadcast)

**Data:**
```json
{
  "type": "taken",
  "filename": "cinepi_20240115_143000.jpg",
  "timestamp": "2024-01-15T14:30:00",
  "count": 121
}
```

#### Settings Updated
**Event:** `settings_updated`

**Description:** Broadcast settings update.

**Emitted by:** Server (broadcast)

**Data:**
```json
{
  "settings": {
    "exposure_mode": "manual",
    "iso": 800
  },
  "timestamp": "2024-01-15T14:30:00"
}
```

#### Error Occurred
**Event:** `error_occurred`

**Description:** Broadcast error notification.

**Emitted by:** Server (broadcast)

**Data:**
```json
{
  "error": "Camera connection failed",
  "timestamp": "2024-01-15T14:30:00",
  "severity": "error"
}
```

---

## Service Layer Interfaces

### CaptureService

**Location:** `dashboard/services/capture_service.py`

**Purpose:** Handles timelapse capture control and session management.

**Key Methods:**
- `start_session(interval)` - Start timelapse session
- `stop_session()` - Stop timelapse session
- `update_interval(interval)` - Update capture interval
- `get_session_info()` - Get session status
- `get_capture_list(limit)` - List capture files
- `delete_capture(filename)` - Delete capture file
- `take_snapshot()` - Take manual snapshot

**CinePi Integration:**
- Uses `python3 -m cinepi.timing` for timing control
- Uses `python3 -m cinepi.capture` for manual snapshots
- Integrates with `/opt/cinepi/captures` directory

---

### CameraService

**Location:** `dashboard/services/camera_service.py`

**Purpose:** Handles camera control and settings management.

**Key Methods:**
- `get_status()` - Get camera connection status
- `get_settings()` - Get current camera settings
- `update_settings(settings)` - Update camera settings
- `take_snapshot()` - Take manual snapshot
- `get_mjpeg_stream()` - Get MJPEG stream response

**CinePi Integration:**
- Uses `python3 -m cinepi.camera` for camera operations
- Integrates with `/opt/cinepi/config/cinepi.yaml` for settings
- Applies settings via subprocess calls

---

### ConfigService

**Location:** `dashboard/services/config_service.py`

**Purpose:** Handles configuration file management and backup/restore.

**Key Methods:**
- `get_config()` - Get current configuration
- `update_config(data)` - Update configuration
- `create_backup()` - Create configuration backup
- `restore_backup(filename)` - Restore from backup
- `validate_config(data)` - Validate configuration

**CinePi Integration:**
- Manages `/opt/cinepi/config/cinepi.yaml`
- Creates backups in `/opt/cinepi/config/backups/`
- Validates configuration structure

---

### WebSocketService

**Location:** `dashboard/services/websocket_service.py`

**Purpose:** Handles real-time status updates and WebSocket communication.

**Key Methods:**
- `get_current_status()` - Get comprehensive system status
- `get_recent_logs(limit)` - Get recent log entries
- `broadcast_status_update()` - Broadcast status to clients
- `broadcast_log_update()` - Broadcast log updates
- `broadcast_error(error)` - Broadcast error notifications

**Integration:**
- Monitors system resources (CPU, memory, disk)
- Reads log files for real-time updates
- Integrates with camera and capture services

---

## Integration Points

### CinePi Module Integration

The dashboard integrates with existing CinePi modules through subprocess calls:

#### Timing Controller
- **Module:** `cinepi.timing`
- **Commands:**
  - `python3 -m cinepi.timing start --interval <seconds>`
  - `python3 -m cinepi.timing stop`
- **Purpose:** Control timelapse capture timing

#### Camera Module
- **Module:** `cinepi.camera`
- **Commands:**
  - `python3 -m cinepi.camera status`
  - `python3 -m cinepi.camera settings`
  - `python3 -m cinepi.camera snapshot`
- **Purpose:** Camera control and settings management

#### Capture Module
- **Module:** `cinepi.capture`
- **Commands:**
  - `python3 -m cinepi.capture manual`
- **Purpose:** Manual snapshot capture

### File System Integration

#### Configuration Files
- **Primary Config:** `/opt/cinepi/config/cinepi.yaml`
- **Backup Directory:** `/opt/cinepi/config/backups/`
- **Backup Format:** `cinepi_backup_YYYYMMDD_HHMMSS.yaml`

#### Capture Files
- **Capture Directory:** `/opt/cinepi/captures/`
- **File Format:** `cinepi_YYYYMMDD_HHMMSS.jpg`
- **Permissions:** Read/write for dashboard service

#### Log Files
- **System Logs:** `/var/log/cinepi/`
- **Dashboard Logs:** `/var/log/cinepi-dashboard/`
- **Log Levels:** info, warning, error

### External Dependencies

#### Python Dependencies
- Flask (web framework)
- Flask-SocketIO (WebSocket support)
- PyYAML (configuration management)
- psutil (system monitoring)

#### System Dependencies
- Python 3.8+
- CinePi modules (timing, camera, capture)
- Camera hardware drivers
- File system permissions

---

## Error Handling

### Validation Errors (400)
- Invalid interval values
- Invalid camera settings
- Invalid filenames
- Missing required parameters

### System Errors (500)
- CinePi module failures
- File system errors
- Configuration errors
- Subprocess timeouts

### Error Response Format
```json
{
  "success": false,
  "error": "Error description",
  "details": "Additional error details (optional)"
}
```

---

## Rate Limiting

Currently, no rate limiting is implemented. Consider implementing rate limiting for production deployments.

## Security Considerations

1. **Input Validation:** All user inputs are validated to prevent injection attacks
2. **File Path Security:** Filename validation prevents path traversal attacks
3. **Subprocess Security:** Subprocess calls use explicit command arrays
4. **Error Information:** Error messages are sanitized to prevent information disclosure

## Future Enhancements

1. **Authentication:** Implement user authentication and authorization
2. **Rate Limiting:** Add rate limiting for API endpoints
3. **API Versioning:** Implement API versioning for backward compatibility
4. **Caching:** Add response caching for static data
5. **Metrics:** Add API usage metrics and monitoring
6. **Documentation:** Generate OpenAPI/Swagger documentation

---

## Testing

### Manual Testing
1. Start the Flask dashboard: `python run_dashboard.py`
2. Test each endpoint using curl or Postman
3. Verify WebSocket connections using a WebSocket client
4. Test error conditions and edge cases

### Automated Testing
- Unit tests for service classes
- Integration tests for API endpoints
- WebSocket event testing
- Error handling validation

### Example Test Commands
```bash
# Test capture start
curl -X POST http://localhost:5000/api/capture/start \
  -H "Content-Type: application/json" \
  -d '{"interval": 30}'

# Test camera settings
curl -X GET http://localhost:5000/api/camera/settings

# Test WebSocket connection
wscat -c ws://localhost:5000/socket.io/
```

---

*Last Updated: January 15, 2024*
*Version: 1.0.0* 