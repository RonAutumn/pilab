# CinePi Dashboard Integration Points

## Overview

This document details all integration points between the CinePi Dashboard Flask application and the existing CinePi system modules. It covers subprocess calls, file system interactions, data flow, and configuration management.

## Table of Contents

1. [CinePi Module Integration](#cinepi-module-integration)
2. [File System Integration](#file-system-integration)
3. [Configuration Management](#configuration-management)
4. [Data Flow Diagrams](#data-flow-diagrams)
5. [Error Handling and Recovery](#error-handling-and-recovery)
6. [Security Considerations](#security-considerations)
7. [Testing Integration Points](#testing-integration-points)

---

## CinePi Module Integration

### 1. Timing Controller Integration

**Module:** `cinepi.timing`
**Purpose:** Control timelapse capture timing and session management

#### Subprocess Commands

##### Start Timelapse Session
```python
# Command executed by CaptureService.start_session()
subprocess.run([
    'python3', '-m', 'cinepi.timing', 'start', 
    '--interval', str(interval)
], capture_output=True, text=True, timeout=30)
```

**Parameters:**
- `interval` (int): Capture interval in seconds (1-3600)

**Expected Response:**
- Return code 0: Success
- Return code non-zero: Error with stderr output

**Error Handling:**
- Timeout after 30 seconds
- Subprocess execution errors
- Invalid interval values

##### Stop Timelapse Session
```python
# Command executed by CaptureService.stop_session()
subprocess.run([
    'python3', '-m', 'cinepi.timing', 'stop'
], capture_output=True, text=True, timeout=30)
```

**Expected Response:**
- Return code 0: Success
- Return code non-zero: Error with stderr output

**Error Handling:**
- Timeout after 30 seconds
- No active session to stop

#### Integration Points in Code

**File:** `dashboard/services/capture_service.py`
```python
def start_session(self, interval):
    # Integration with CinePi timing controller
    result = subprocess.run([
        'python3', '-m', 'cinepi.timing', 'start', 
        '--interval', str(interval)
    ], capture_output=True, text=True, timeout=30)
    
    if result.returncode == 0:
        # Update session state
        self.session = {
            'start_time': datetime.now(),
            'interval': interval,
            'status': 'active'
        }
        return {'success': True, 'message': f'Session started with {interval}s interval'}
    else:
        return {'success': False, 'error': result.stderr or 'Failed to start capture session'}
```

---

### 2. Camera Module Integration

**Module:** `cinepi.camera`
**Purpose:** Camera control, settings management, and status monitoring

#### Subprocess Commands

##### Get Camera Status
```python
# Command executed by CameraService.get_status()
subprocess.run([
    'python3', '-m', 'cinepi.camera', 'status'
], capture_output=True, text=True, timeout=10)
```

**Expected Response:**
- JSON output with camera status
- Return code 0: Success
- Return code non-zero: Camera not connected or error

##### Get Camera Settings
```python
# Command executed by CameraService.get_settings()
subprocess.run([
    'python3', '-m', 'cinepi.camera', 'settings'
], capture_output=True, text=True, timeout=10)
```

**Expected Response:**
- JSON output with current camera settings
- Return code 0: Success
- Return code non-zero: Error reading settings

##### Update Camera Settings
```python
# Command executed by CameraService.update_settings()
subprocess.run([
    'python3', '-m', 'cinepi.camera', 'settings',
    '--exposure', settings['exposure_mode'],
    '--iso', str(settings['iso']),
    '--gain', str(settings['gain']),
    '--resolution', settings['resolution']
], capture_output=True, text=True, timeout=10)
```

**Parameters:**
- `exposure_mode`: "auto" or "manual"
- `iso`: Integer value (100-800)
- `gain`: Float value (1.0-8.0)
- `resolution`: String from supported resolutions

##### Take Manual Snapshot
```python
# Command executed by CameraService.take_snapshot()
subprocess.run([
    'python3', '-m', 'cinepi.camera', 'snapshot'
], capture_output=True, text=True, timeout=30)
```

**Expected Response:**
- Return code 0: Snapshot taken successfully
- Return code non-zero: Error taking snapshot

#### Integration Points in Code

**File:** `dashboard/services/camera_service.py`
```python
def get_status(self):
    """Get camera connection status"""
    try:
        result = subprocess.run([
            'python3', '-m', 'cinepi.camera', 'status'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            status_data = json.loads(result.stdout)
            return {
                'status': 'connected',
                'connected': True,
                'error': None,
                'details': status_data
            }
        else:
            return {
                'status': 'disconnected',
                'connected': False,
                'error': result.stderr or 'Camera not connected'
            }
    except Exception as e:
        return {
            'status': 'error',
            'connected': False,
            'error': str(e)
        }
```

---

### 3. Capture Module Integration

**Module:** `cinepi.capture`
**Purpose:** Manual snapshot capture and file management

#### Subprocess Commands

##### Take Manual Snapshot
```python
# Command executed by CaptureService.take_snapshot()
subprocess.run([
    'python3', '-m', 'cinepi.capture', 'manual'
], capture_output=True, text=True, timeout=30)
```

**Expected Response:**
- Return code 0: Snapshot taken successfully
- Filename in stdout or stderr
- Return code non-zero: Error taking snapshot

#### Integration Points in Code

**File:** `dashboard/services/capture_service.py`
```python
def take_snapshot(self):
    """Take manual snapshot"""
    try:
        result = subprocess.run([
            'python3', '-m', 'cinepi.capture', 'manual'
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Extract filename from output
            filename = self._extract_filename(result.stdout or result.stderr)
            return {
                'success': True,
                'message': 'Snapshot taken successfully',
                'filename': filename,
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'error': result.stderr or 'Failed to take snapshot'
            }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': 'Snapshot request timed out'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
```

---

## File System Integration

### 1. Configuration Files

#### Primary Configuration
**Path:** `/opt/cinepi/config/cinepi.yaml`
**Purpose:** Main CinePi configuration file
**Format:** YAML
**Permissions:** Read/write for dashboard service

**Example Structure:**
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

#### Backup Configuration
**Directory:** `/opt/cinepi/config/backups/`
**Format:** `cinepi_backup_YYYYMMDD_HHMMSS.yaml`
**Purpose:** Configuration backup files
**Retention:** Configurable (default: 30 days)

**Integration Code:**
```python
# ConfigService.create_backup()
def create_backup(self):
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'cinepi_backup_{timestamp}.yaml'
    backup_path = self.backup_dir / backup_filename
    
    # Copy current config to backup
    shutil.copy2(self.config_path, backup_path)
    
    return {
        'success': True,
        'message': 'Backup created successfully',
        'backup_file': backup_filename
    }
```

### 2. Capture Files

#### Capture Directory
**Path:** `/opt/cinepi/captures/`
**Purpose:** Storage for timelapse and manual capture images
**Format:** `cinepi_YYYYMMDD_HHMMSS.jpg`
**Permissions:** Read/write for dashboard service

**File Management:**
```python
# CaptureService.get_capture_list()
def get_capture_list(self, limit=50):
    """Get list of recent capture files"""
    captures = []
    
    # Scan capture directory
    for file_path in sorted(self.captures_path.glob('cinepi_*.jpg'), reverse=True):
        if len(captures) >= limit:
            break
            
        captures.append({
            'filename': file_path.name,
            'timestamp': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
            'size': file_path.stat().st_size,
            'path': str(file_path)
        })
    
    return captures
```

#### File Deletion
```python
# CaptureService.delete_capture()
def delete_capture(self, filename):
    """Delete a specific capture file"""
    # Validate filename for security
    if not validate_filename(filename):
        return {'success': False, 'error': 'Invalid filename'}
    
    file_path = self.captures_path / filename
    
    if not file_path.exists():
        return {'success': False, 'error': 'File not found'}
    
    try:
        file_path.unlink()
        return {'success': True, 'message': 'File deleted successfully'}
    except Exception as e:
        return {'success': False, 'error': str(e)}
```

### 3. Log Files

#### System Logs
**Directory:** `/var/log/cinepi/`
**Purpose:** CinePi system logs
**Format:** Text files with timestamps
**Log Levels:** info, warning, error

#### Dashboard Logs
**Directory:** `/var/log/cinepi-dashboard/`
**Purpose:** Dashboard application logs
**Format:** Text files with timestamps
**Log Levels:** info, warning, error

**Log Reading Integration:**
```python
# WebSocketService.get_recent_logs()
def get_recent_logs(self, limit=50):
    """Get recent log entries"""
    logs = []
    
    # Read from multiple log sources
    log_files = [
        '/var/log/cinepi/system.log',
        '/var/log/cinepi-dashboard/app.log'
    ]
    
    for log_file in log_files:
        if os.path.exists(log_file):
            try:
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-limit:]:
                        log_entry = self._parse_log_line(line)
                        if log_entry:
                            logs.append(log_entry)
            except Exception as e:
                logs.append({
                    'timestamp': datetime.now().isoformat(),
                    'level': 'error',
                    'message': f'Error reading log file: {e}',
                    'module': 'websocket_service'
                })
    
    # Sort by timestamp and limit
    logs.sort(key=lambda x: x['timestamp'], reverse=True)
    return logs[:limit]
```

---

## Configuration Management

### 1. Configuration Loading

**File:** `dashboard/services/config_service.py`

```python
def get_config(self):
    """Get current CinePi configuration"""
    try:
        if not self.config_path.exists():
            # Return default configuration
            return self._get_default_config()
        
        with open(self.config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Validate configuration structure
        if not self._validate_config_structure(config_data):
            return self._get_default_config()
        
        return config_data
    except Exception as e:
        return {
            'error': f'Error loading configuration: {e}',
            'config': self._get_default_config()
        }
```

### 2. Configuration Updates

```python
def update_config(self, new_config):
    """Update CinePi configuration"""
    try:
        # Validate new configuration
        if not self._validate_config_structure(new_config):
            return {
                'success': False,
                'error': 'Invalid configuration structure'
            }
        
        # Create backup before updating
        backup_result = self.create_backup()
        if not backup_result['success']:
            return backup_result
        
        # Write new configuration
        with open(self.config_path, 'w') as f:
            yaml.dump(new_config, f, default_flow_style=False)
        
        # Apply configuration to CinePi modules
        self._apply_config_to_modules(new_config)
        
        return {
            'success': True,
            'message': 'Configuration updated successfully'
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
```

### 3. Configuration Validation

```python
def _validate_config_structure(self, config):
    """Validate configuration structure"""
    required_sections = ['camera', 'capture', 'system']
    
    for section in required_sections:
        if section not in config:
            return False
    
    # Validate camera settings
    camera = config.get('camera', {})
    if 'exposure_mode' not in camera:
        return False
    
    # Validate capture settings
    capture = config.get('capture', {})
    if 'interval' not in capture:
        return False
    
    return True
```

---

## Data Flow Diagrams

### 1. Capture Session Flow

```
Dashboard UI → Flask API → CaptureService → CinePi Timing Module
     ↓              ↓            ↓              ↓
WebSocket ← Status Update ← Session State ← Subprocess Result
```

### 2. Camera Settings Flow

```
Dashboard UI → Flask API → CameraService → CinePi Camera Module
     ↓              ↓            ↓              ↓
WebSocket ← Settings Update ← Config File ← Subprocess Result
```

### 3. Real-time Status Flow

```
CinePi Modules → System Monitoring → WebSocketService → Dashboard UI
     ↓                ↓                ↓              ↓
Status Data → Resource Monitoring → WebSocket Events → Real-time Updates
```

---

## Error Handling and Recovery

### 1. Subprocess Error Handling

```python
def _execute_cinepi_command(self, command, timeout=30):
    """Execute CinePi module command with error handling"""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        if result.returncode == 0:
            return {
                'success': True,
                'output': result.stdout,
                'error': None
            }
        else:
            return {
                'success': False,
                'output': result.stdout,
                'error': result.stderr or 'Command failed'
            }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': None,
            'error': f'Command timed out after {timeout} seconds'
        }
    except FileNotFoundError:
        return {
            'success': False,
            'output': None,
            'error': 'CinePi module not found'
        }
    except Exception as e:
        return {
            'success': False,
            'output': None,
            'error': str(e)
        }
```

### 2. File System Error Recovery

```python
def _safe_file_operation(self, operation, *args, **kwargs):
    """Safely execute file system operations"""
    try:
        return operation(*args, **kwargs)
    except PermissionError:
        return {
            'success': False,
            'error': 'Permission denied accessing file system'
        }
    except FileNotFoundError:
        return {
            'success': False,
            'error': 'File or directory not found'
        }
    except OSError as e:
        return {
            'success': False,
            'error': f'File system error: {e}'
        }
```

### 3. Configuration Error Recovery

```python
def _recover_configuration(self):
    """Recover from configuration errors"""
    try:
        # Try to restore from latest backup
        backups = self._list_backups()
        if backups:
            latest_backup = backups[0]
            return self.restore_backup(latest_backup['filename'])
        
        # Create new default configuration
        default_config = self._get_default_config()
        with open(self.config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        
        return {
            'success': True,
            'message': 'Configuration recovered with defaults'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Failed to recover configuration: {e}'
        }
```

---

## Security Considerations

### 1. Input Validation

```python
def validate_filename(filename):
    """Validate filename for security"""
    # Prevent path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # Check file extension
    if not filename.endswith('.jpg'):
        return False
    
    # Check filename format
    if not re.match(r'^cinepi_\d{8}_\d{6}\.jpg$', filename):
        return False
    
    return True
```

### 2. Subprocess Security

```python
def _secure_subprocess_call(self, command):
    """Execute subprocess with security measures"""
    # Validate command structure
    if not isinstance(command, list):
        raise ValueError("Command must be a list")
    
    # Check for dangerous commands
    dangerous_commands = ['rm', 'del', 'format', 'dd']
    for cmd in command:
        if cmd in dangerous_commands:
            raise ValueError(f"Dangerous command not allowed: {cmd}")
    
    # Execute with timeout and output capture
    return subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=30,
        shell=False  # Prevent shell injection
    )
```

### 3. File Path Security

```python
def _secure_path_join(self, base_path, filename):
    """Safely join file paths"""
    # Normalize paths
    base_path = os.path.abspath(base_path)
    filename = os.path.basename(filename)  # Remove path components
    
    # Join paths
    full_path = os.path.join(base_path, filename)
    
    # Ensure result is within base path
    if not full_path.startswith(base_path):
        raise ValueError("Path traversal attempt detected")
    
    return full_path
```

---

## Testing Integration Points

### 1. Unit Tests

```python
# test_capture_service.py
def test_start_session_integration():
    """Test integration with CinePi timing module"""
    service = CaptureService()
    
    # Mock subprocess call
    with patch('subprocess.run') as mock_run:
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "Session started"
        
        result = service.start_session(30)
        
        assert result['success'] == True
        mock_run.assert_called_once_with([
            'python3', '-m', 'cinepi.timing', 'start', '--interval', '30'
        ], capture_output=True, text=True, timeout=30)
```

### 2. Integration Tests

```python
# test_integration.py
def test_full_capture_workflow():
    """Test complete capture workflow integration"""
    # Start dashboard
    app = create_app('testing')
    client = app.test_client()
    
    # Start capture session
    response = client.post('/api/capture/start', json={'interval': 30})
    assert response.status_code == 200
    assert response.json['success'] == True
    
    # Check session status
    response = client.get('/api/capture/status')
    assert response.status_code == 200
    assert response.json['status'] == 'active'
    
    # Stop capture session
    response = client.post('/api/capture/stop')
    assert response.status_code == 200
    assert response.json['success'] == True
```

### 3. End-to-End Tests

```python
# test_e2e.py
def test_camera_settings_integration():
    """Test camera settings integration end-to-end"""
    # Update camera settings
    settings = {
        'exposure_mode': 'manual',
        'iso': 800,
        'gain': 4.0,
        'resolution': '4056x3040'
    }
    
    response = client.put('/api/camera/settings', json=settings)
    assert response.status_code == 200
    assert response.json['success'] == True
    
    # Verify settings were applied
    response = client.get('/api/camera/settings')
    assert response.status_code == 200
    assert response.json['exposure_mode'] == 'manual'
    assert response.json['iso'] == 800
```

---

## Monitoring and Logging

### 1. Integration Monitoring

```python
def monitor_integration_health(self):
    """Monitor health of all integration points"""
    health_status = {
        'cinepi_modules': self._check_cinepi_modules(),
        'file_system': self._check_file_system(),
        'configuration': self._check_configuration(),
        'web_socket': self._check_web_socket()
    }
    
    return health_status
```

### 2. Performance Monitoring

```python
def monitor_integration_performance(self):
    """Monitor performance of integration points"""
    performance_metrics = {
        'subprocess_response_time': self._measure_subprocess_time(),
        'file_operation_time': self._measure_file_operations(),
        'web_socket_latency': self._measure_web_socket_latency(),
        'memory_usage': self._measure_memory_usage()
    }
    
    return performance_metrics
```

---

## Troubleshooting Guide

### 1. Common Integration Issues

#### CinePi Module Not Found
**Symptoms:** FileNotFoundError in subprocess calls
**Solution:** Verify CinePi modules are installed and accessible

#### Permission Denied
**Symptoms:** PermissionError accessing files or directories
**Solution:** Check file permissions and service user access

#### Configuration Corruption
**Symptoms:** YAML parsing errors or invalid configuration
**Solution:** Restore from backup or recreate default configuration

### 2. Debug Commands

```bash
# Check CinePi module availability
python3 -m cinepi.timing --help
python3 -m cinepi.camera --help
python3 -m cinepi.capture --help

# Check file permissions
ls -la /opt/cinepi/config/
ls -la /opt/cinepi/captures/

# Check service logs
tail -f /var/log/cinepi-dashboard/app.log
```

---

*Last Updated: January 15, 2024*
*Version: 1.0.0* 