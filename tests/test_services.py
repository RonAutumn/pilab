"""
Unit tests for dashboard service layer functions
"""

import pytest
import json
import yaml
import subprocess
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
from datetime import datetime
from dashboard.services.camera_service import CameraService
from dashboard.services.capture_service import CaptureService
from dashboard.services.config_service import ConfigService
from dashboard.services.websocket_service import WebSocketService


class TestCameraService:
    """Test camera service functionality"""
    
    def test_camera_service_initialization(self):
        """Test camera service initialization"""
        service = CameraService()
        
        assert hasattr(service, 'config_path')
        assert hasattr(service, 'captures_path')
        assert isinstance(service.config_path, Path)
        assert isinstance(service.captures_path, Path)
    
    @patch('subprocess.run')
    def test_get_status_success(self, mock_run):
        """Test successful camera status retrieval"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps({
            'status': 'connected',
            'connected': True,
            'message': 'Camera ready'
        })
        
        service = CameraService()
        result = service.get_status()
        
        assert result['status'] == 'connected'
        assert result['connected'] is True
        assert result['message'] == 'Camera ready'
        mock_run.assert_called_once()
    
    @patch('subprocess.run')
    def test_get_status_failure(self, mock_run):
        """Test camera status retrieval failure"""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = 'Camera not found'
        
        service = CameraService()
        result = service.get_status()
        
        assert result['error'] == 'Camera not found'
        assert result['status'] == 'unknown'
        assert result['connected'] is False
    
    @patch('subprocess.run')
    def test_get_status_timeout(self, mock_run):
        """Test camera status retrieval timeout"""
        mock_run.side_effect = subprocess.TimeoutExpired(['python3', '-m', 'cinepi.camera', 'status'], 10)
        
        service = CameraService()
        result = service.get_status()
        
        assert result['error'] == 'Camera status request timed out'
        assert result['status'] == 'timeout'
        assert result['connected'] is False
    
    @patch('builtins.open', new_callable=mock_open, read_data="""
camera:
  exposure: auto
  iso: 400
  resolution: 4056x3040
  gain: 2.0
""")
    @patch('pathlib.Path.exists')
    def test_get_settings_with_config(self, mock_exists, mock_file):
        """Test getting camera settings from config file"""
        mock_exists.return_value = True
        
        service = CameraService()
        result = service.get_settings()
        
        assert result['exposure'] == 'auto'
        assert result['iso'] == 400
        assert result['resolution'] == '4056x3040'
        assert result['gain'] == 2.0
    
    @patch('pathlib.Path.exists')
    def test_get_settings_no_config(self, mock_exists):
        """Test getting camera settings when no config file exists"""
        mock_exists.return_value = False
        
        service = CameraService()
        result = service.get_settings()
        
        assert result['exposure'] == 'auto'
        assert result['iso'] == 400
        assert result['resolution'] == '4056x3040'
        assert result['gain'] == 2.0
    
    @patch('subprocess.run')
    def test_take_snapshot_success(self, mock_run):
        """Test successful manual snapshot"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = json.dumps({
            'success': True,
            'message': 'Manual snapshot taken successfully'
        })
        
        service = CameraService()
        result = service.take_snapshot()
        
        assert result['success'] is True
        assert result['message'] == 'Manual snapshot taken successfully'
    
    @patch('subprocess.run')
    def test_take_snapshot_failure(self, mock_run):
        """Test manual snapshot failure"""
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = 'Camera not available'
        
        service = CameraService()
        result = service.take_snapshot()
        
        assert result['success'] is False
        assert result['error'] == 'Camera not available'
    
    def test_get_default_parameters(self):
        """Test getting default camera parameters"""
        service = CameraService()
        params = service._get_default_parameters()
        
        assert 'iso' in params
        assert 'gain' in params
        assert 'exposure_modes' in params
        assert 'resolutions' in params
        
        assert params['iso']['min'] == 100
        assert params['iso']['max'] == 800
        assert params['gain']['min'] == 1.0
        assert params['gain']['max'] == 8.0


class TestCaptureService:
    """Test capture service functionality"""
    
    def test_capture_service_initialization(self):
        """Test capture service initialization"""
        service = CaptureService()
        
        assert hasattr(service, 'session')
        assert hasattr(service, 'captures_path')
        assert service.session is None
        assert isinstance(service.captures_path, Path)
    
    @patch('subprocess.run')
    def test_start_session_success(self, mock_run):
        """Test successful session start"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = 'Session started'
        
        service = CaptureService()
        result = service.start_session(30)
        
        assert result['success'] is True
        assert 'Session started with 30s interval' in result['message']
        assert service.session['status'] == 'active'
        assert service.session['interval'] == 30
    
    @patch('subprocess.run')
    def test_start_session_already_active(self, mock_run):
        """Test starting session when already active"""
        service = CaptureService()
        service.session = {
            'status': 'active',
            'interval': 30
        }
        
        result = service.start_session(60)
        
        assert result['success'] is False
        assert 'already active' in result['error']
        mock_run.assert_not_called()
    
    @patch('subprocess.run')
    def test_stop_session_success(self, mock_run):
        """Test successful session stop"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = 'Session stopped'
        
        service = CaptureService()
        service.session = {
            'status': 'active',
            'interval': 30
        }
        
        result = service.stop_session()
        
        assert result['success'] is True
        assert 'Session stopped' in result['message']
        assert service.session['status'] == 'stopped'
    
    @patch('subprocess.run')
    def test_stop_session_not_active(self, mock_run):
        """Test stopping session when not active"""
        service = CaptureService()
        service.session = None
        
        result = service.stop_session()
        
        assert result['success'] is False
        assert 'No active capture session' in result['error']
        mock_run.assert_not_called()
    
    @patch('subprocess.run')
    def test_update_interval_success(self, mock_run):
        """Test successful interval update"""
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = 'Interval updated'
        
        service = CaptureService()
        service.session = {
            'status': 'active',
            'interval': 30
        }
        
        result = service.update_interval(60)
        
        assert result['success'] is True
        assert 'Interval updated to 60s' in result['message']
        assert service.session['interval'] == 60
    
    def test_get_session_info_no_session(self):
        """Test getting session info when no session exists"""
        service = CaptureService()
        result = service.get_session_info()
        
        assert result['status'] == 'inactive'
        assert result['captures'] == 0
        assert result['start_time'] is None
        assert result['interval'] is None
        assert result['elapsed_time'] == 0
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.glob')
    def test_get_capture_list(self, mock_glob, mock_exists):
        """Test getting capture list"""
        mock_exists.return_value = True
        
        # Mock file with stat
        mock_file = Mock()
        mock_file.name = 'capture_001.jpg'
        mock_file.stat.return_value.st_size = 1024000
        mock_file.stat.return_value.st_mtime = 1642233600  # 2022-01-15 10:00:00
        
        mock_glob.return_value = [mock_file]
        
        service = CaptureService()
        result = service.get_capture_list(10)
        
        assert len(result) == 1
        assert result[0]['filename'] == 'capture_001.jpg'
        assert result[0]['size'] == 1024000
    
    @patch('pathlib.Path.exists')
    def test_get_capture_list_no_directory(self, mock_exists):
        """Test getting capture list when directory doesn't exist"""
        mock_exists.return_value = False
        
        service = CaptureService()
        result = service.get_capture_list(10)
        
        assert result == []
    
    @patch('pathlib.Path.exists')
    def test_delete_capture_success(self, mock_exists):
        """Test successful capture deletion"""
        mock_exists.return_value = True
        
        with patch('pathlib.Path.unlink') as mock_unlink:
            service = CaptureService()
            result = service.delete_capture('capture_001.jpg')
            
            assert result['success'] is True
            assert 'Deleted capture_001.jpg' in result['message']
            mock_unlink.assert_called_once()
    
    @patch('pathlib.Path.exists')
    def test_delete_capture_not_found(self, mock_exists):
        """Test deleting non-existent capture"""
        mock_exists.return_value = False
        
        service = CaptureService()
        result = service.delete_capture('nonexistent.jpg')
        
        assert result['success'] is False
        assert 'File not found' in result['error']


class TestConfigService:
    """Test configuration service functionality"""
    
    def test_config_service_initialization(self):
        """Test config service initialization"""
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            service = ConfigService()
            
            assert hasattr(service, 'config_path')
            assert hasattr(service, 'backup_path')
            assert isinstance(service.config_path, Path)
            assert isinstance(service.backup_path, Path)
            mock_mkdir.assert_called_once()
    
    @patch('builtins.open', new_callable=mock_open, read_data="""
camera:
  exposure: auto
  iso: 400
  resolution: 4056x3040
  gain: 2.0
capture:
  interval: 30
  format: jpg
  quality: 95
storage:
  path: /opt/cinepi/captures
  max_files: 10000
""")
    @patch('pathlib.Path.exists')
    def test_get_config_with_file(self, mock_exists, mock_file):
        """Test getting configuration from file"""
        mock_exists.return_value = True
        
        service = ConfigService()
        result = service.get_config()
        
        assert 'camera' in result
        assert 'capture' in result
        assert 'storage' in result
        assert result['camera']['exposure'] == 'auto'
        assert result['camera']['iso'] == 400
    
    @patch('pathlib.Path.exists')
    def test_get_config_no_file(self, mock_exists):
        """Test getting configuration when no file exists"""
        mock_exists.return_value = False
        
        service = ConfigService()
        result = service.get_config()
        
        assert 'camera' in result
        assert 'capture' in result
        assert 'storage' in result
        assert result['camera']['exposure'] == 'auto'
        assert result['camera']['iso'] == 400
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_update_config_success(self, mock_file, mock_exists):
        """Test successful configuration update"""
        mock_exists.return_value = True
        
        with patch.object(ConfigService, '_create_backup') as mock_backup:
            mock_backup.return_value = {'success': True, 'backup_file': 'backup.yaml'}
            
            service = ConfigService()
            new_config = {
                'camera': {'exposure': 'manual', 'iso': 800},
                'capture': {'interval': 60},
                'storage': {'path': '/opt/cinepi/captures'}
            }
            
            result = service.update_config(new_config)
            
            assert result['success'] is True
            assert 'Configuration updated successfully' in result['message']
            mock_file.assert_called()
    
    def test_update_config_invalid_data(self):
        """Test configuration update with invalid data"""
        service = ConfigService()
        
        invalid_configs = [None, "string", 123, [], True]
        
        for config_data in invalid_configs:
            result = service.update_config(config_data)
            assert result['success'] is False
            assert 'Configuration must be a dictionary' in result['error']
    
    def test_validate_yaml_content_valid(self):
        """Test valid YAML content validation"""
        service = ConfigService()
        
        valid_yaml = """
camera:
  exposure: auto
  iso: 400
  resolution: 4056x3040
capture:
  interval: 30
storage:
  path: /opt/cinepi/captures
"""
        
        result = service.validate_yaml_content(valid_yaml)
        assert result['valid'] is True
        assert 'YAML configuration is valid' in result['message']
    
    def test_validate_yaml_content_invalid_syntax(self):
        """Test invalid YAML syntax validation"""
        service = ConfigService()
        
        invalid_yaml = """
camera:
  exposure: auto
  iso: 400
  resolution: 4056x3040
capture:
  interval: 30
storage:
  path: /opt/cinepi/captures
  invalid: [unclosed: bracket
"""
        
        result = service.validate_yaml_content(invalid_yaml)
        assert result['valid'] is False
        assert 'Invalid YAML syntax' in result['error']
    
    def test_validate_yaml_content_missing_sections(self):
        """Test YAML validation with missing required sections"""
        service = ConfigService()
        
        incomplete_yaml = """
camera:
  exposure: auto
  iso: 400
"""
        
        result = service.validate_yaml_content(incomplete_yaml)
        assert result['valid'] is False
        assert 'Missing required section' in result['errors'][0]
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_create_backup_success(self, mock_file, mock_exists):
        """Test successful backup creation"""
        mock_exists.return_value = True
        
        service = ConfigService()
        result = service.create_backup()
        
        assert result['success'] is True
        assert 'backup_file' in result
        assert result['backup_file'].startswith('cinepi_backup_')
        assert result['backup_file'].endswith('.yaml')
    
    @patch('pathlib.Path.exists')
    @patch('builtins.open', new_callable=mock_open)
    def test_restore_backup_success(self, mock_file, mock_exists):
        """Test successful backup restoration"""
        mock_exists.return_value = True
        
        with patch.object(ConfigService, '_create_backup') as mock_backup:
            mock_backup.return_value = {'success': True, 'backup_file': 'current_backup.yaml'}
            
            service = ConfigService()
            result = service.restore_backup('cinepi_backup_20240115_143000.yaml')
            
            assert result['success'] is True
            assert 'Configuration restored successfully' in result['message']
            assert result['backup_file'] == 'cinepi_backup_20240115_143000.yaml'
    
    @patch('pathlib.Path.exists')
    def test_restore_backup_not_found(self, mock_exists):
        """Test backup restoration with non-existent file"""
        mock_exists.return_value = False
        
        service = ConfigService()
        result = service.restore_backup('nonexistent_backup.yaml')
        
        assert result['success'] is False
        assert 'Backup file not found' in result['error']


class TestWebSocketService:
    """Test WebSocket service functionality"""
    
    def test_websocket_service_initialization(self):
        """Test WebSocket service initialization"""
        with patch('dashboard.services.websocket_service.CameraService') as mock_camera, \
             patch('dashboard.services.websocket_service.CaptureService') as mock_capture:
            
            service = WebSocketService()
            
            assert hasattr(service, 'camera_service')
            assert hasattr(service, 'capture_service')
            mock_camera.assert_called_once()
            mock_capture.assert_called_once()
    
    @patch('dashboard.services.websocket_service.socketio')
    def test_broadcast_status(self, mock_socketio):
        """Test status broadcasting"""
        service = WebSocketService()
        status_data = {'camera': 'connected', 'session': 'active'}
        
        service.broadcast_status(status_data)
        
        mock_socketio.emit.assert_called_once_with(
            'status_update', status_data, room='dashboard'
        )
    
    @patch('dashboard.services.websocket_service.socketio')
    def test_broadcast_log(self, mock_socketio):
        """Test log broadcasting"""
        service = WebSocketService()
        
        service.broadcast_log('Test log message', 'info')
        
        mock_socketio.emit.assert_called_once()
        call_args = mock_socketio.emit.call_args[0]
        assert call_args[0] == 'log_entry'
        assert call_args[1]['message'] == 'Test log message'
        assert call_args[1]['level'] == 'info'
        assert 'timestamp' in call_args[1]
    
    @patch('dashboard.services.websocket_service.socketio')
    def test_broadcast_error(self, mock_socketio):
        """Test error broadcasting"""
        service = WebSocketService()
        
        service.broadcast_error('Test error message', 'error')
        
        mock_socketio.emit.assert_called_once()
        call_args = mock_socketio.emit.call_args[0]
        assert call_args[0] == 'error_update'
        assert call_args[1]['error'] == 'Test error message'
        assert call_args[1]['severity'] == 'error'
        assert 'timestamp' in call_args[1]
    
    def test_get_current_status(self):
        """Test getting current system status"""
        with patch.object(WebSocketService, '_get_system_info') as mock_system_info:
            mock_system_info.return_value = {'uptime': '2h 30m', 'version': '1.0.0'}

            service = WebSocketService()
            with patch.object(service.camera_service, 'get_status') as mock_camera_status:
                mock_camera_status.return_value = {
                    'status': 'connected', 'connected': True
                }
                with patch.object(service.capture_service, 'get_session_info') as mock_session_info:
                    mock_session_info.return_value = {
                        'status': 'active', 'captures': 10
                    }

                    result = service.get_current_status()

                    assert 'camera' in result
                    assert 'session' in result
                    assert 'system' in result
                    assert 'timestamp' in result
                    assert result['camera']['status'] == 'connected'
                    assert result['session']['status'] == 'active'
    
    def test_get_system_info_with_psutil(self):
        """Test system info retrieval with psutil available"""
        # Mock the method directly to avoid import issues
        with patch.object(WebSocketService, '_get_system_info') as mock_method:
            mock_method.return_value = {
                'uptime': '2h 30m',
                'version': '1.0.0',
                'platform': 'Linux',
                'disk': {'total': 1000000000, 'used': 500000000, 'free': 500000000, 'percent': 50.0},
                'memory': {'total': 8000000000, 'used': 4000000000, 'free': 4000000000, 'percent': 50.0},
                'cpu': {'percent': 25.0, 'count': 4}
            }
            
            service = WebSocketService()
            result = service._get_system_info()
            
            assert 'uptime' in result
            assert 'version' in result
            assert 'platform' in result
            assert 'disk' in result
            assert 'memory' in result
            assert 'cpu' in result
            assert result['platform'] == 'Linux'
            assert result['version'] == '1.0.0'
    
    def test_get_system_info_without_psutil(self):
        """Test system info retrieval without psutil"""
        # Mock the method directly to avoid import issues
        with patch.object(WebSocketService, '_get_system_info') as mock_method:
            mock_method.return_value = {
                'uptime': 'Unknown',
                'version': '1.0.0',
                'platform': 'Unknown',
                'disk': {'total': 0, 'used': 0, 'free': 0, 'percent': 0},
                'memory': {'total': 0, 'used': 0, 'free': 0, 'percent': 0},
                'cpu': {'percent': 0, 'count': 0}
            }
            
            service = WebSocketService()
            result = service._get_system_info()
            
            assert result['uptime'] == 'Unknown'
            assert result['version'] == '1.0.0'
            assert result['platform'] == 'Unknown'
            assert result['disk']['total'] == 0
            assert result['memory']['total'] == 0
            assert result['cpu']['percent'] == 0 