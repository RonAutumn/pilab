"""
Pytest configuration and fixtures for CinePi Dashboard tests
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch
from flask import Flask
from dashboard import create_app
from dashboard.config import TestConfig


@pytest.fixture
def app():
    """Create and configure a Flask app for testing"""
    # Create temporary directories for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create test directories
        test_cinepi = temp_path / 'test_cinepi'
        test_cinepi.mkdir()
        (test_cinepi / 'config').mkdir()
        (test_cinepi / 'captures').mkdir()
        (test_cinepi / 'logs').mkdir()
        
        # Create test config file
        test_config_path = test_cinepi / 'config' / 'test_cinepi.yaml'
        test_config_path.write_text("""
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
        
        # Patch the config paths for testing
        with patch('dashboard.config.TestConfig.CINEPI_ROOT', test_cinepi), \
             patch('dashboard.config.TestConfig.CONFIG_PATH', test_config_path), \
             patch('dashboard.config.TestConfig.CAPTURES_PATH', test_cinepi / 'captures'), \
             patch('dashboard.config.TestConfig.LOGS_PATH', test_cinepi / 'logs'):
            
            app = create_app('testing')
            app.config['TESTING'] = True
            
            with app.app_context():
                yield app


@pytest.fixture
def client(app):
    """Create a test client for the Flask app"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner for the Flask app"""
    return app.test_cli_runner()


@pytest.fixture
def mock_camera_service():
    """Mock camera service for testing"""
    with patch('dashboard.services.camera_service.CameraService') as mock:
        service = mock.return_value
        service.get_status.return_value = {
            'status': 'connected',
            'connected': True,
            'message': 'Camera ready'
        }
        service.get_settings.return_value = {
            'exposure': 'auto',
            'iso': 400,
            'resolution': '4056x3040',
            'gain': 2.0
        }
        service.get_supported_parameters.return_value = {
            'iso': {'min': 100, 'max': 800, 'step': 100},
            'gain': {'min': 1.0, 'max': 8.0, 'step': 0.1},
            'exposure_modes': ['auto', 'manual'],
            'resolutions': ['4056x3040', '2028x1520', '1014x760']
        }
        service.take_snapshot.return_value = {
            'success': True,
            'message': 'Manual snapshot taken successfully'
        }
        service.update_settings.return_value = {
            'success': True,
            'message': 'Settings updated successfully'
        }
        yield service


@pytest.fixture
def mock_capture_service():
    """Mock capture service for testing"""
    with patch('dashboard.services.capture_service.CaptureService') as mock:
        service = mock.return_value
        service.start_session.return_value = {
            'success': True,
            'message': 'Session started with 30s interval',
            'session': {
                'start_time': '2024-01-15T10:00:00',
                'interval': 30,
                'status': 'active'
            }
        }
        service.stop_session.return_value = {
            'success': True,
            'message': 'Session stopped',
            'session': {
                'start_time': '2024-01-15T10:00:00',
                'end_time': '2024-01-15T10:05:00',
                'interval': 30,
                'status': 'stopped'
            }
        }
        service.get_session_info.return_value = {
            'status': 'active',
            'captures': 10,
            'start_time': '2024-01-15T10:00:00',
            'interval': 30,
            'elapsed_time': 300
        }
        service.get_capture_list.return_value = [
            {
                'filename': 'capture_001.jpg',
                'size': 1024000,
                'timestamp': '2024-01-15T10:00:00',
                'path': '/opt/cinepi/captures/capture_001.jpg'
            }
        ]
        service.update_interval.return_value = {
            'success': True,
            'message': 'Interval updated to 60s',
            'session': {
                'start_time': '2024-01-15T10:00:00',
                'interval': 60,
                'status': 'active'
            }
        }
        yield service


@pytest.fixture
def mock_config_service():
    """Mock config service for testing"""
    with patch('dashboard.services.config_service.ConfigService') as mock:
        service = mock.return_value
        service.get_config.return_value = {
            'camera': {
                'exposure': 'auto',
                'iso': 400,
                'resolution': '4056x3040',
                'gain': 2.0
            },
            'capture': {
                'interval': 30,
                'format': 'jpg',
                'quality': 95
            },
            'storage': {
                'path': '/opt/cinepi/captures',
                'max_files': 10000
            }
        }
        service.update_config.return_value = {
            'success': True,
            'message': 'Configuration updated successfully'
        }
        service.create_backup.return_value = {
            'success': True,
            'backup_file': 'cinepi_backup_20240115_143000.yaml'
        }
        service.restore_backup.return_value = {
            'success': True,
            'message': 'Configuration restored successfully'
        }
        yield service


@pytest.fixture
def mock_websocket_service():
    """Mock WebSocket service for testing"""
    with patch('dashboard.services.websocket_service.WebSocketService') as mock:
        service = mock.return_value
        service.get_current_status.return_value = {
            'camera': {'status': 'connected', 'connected': True},
            'session': {'status': 'active', 'captures': 10},
            'system': {'uptime': '2h 30m', 'version': '1.0.0'},
            'timestamp': '2024-01-15T10:00:00'
        }
        service.get_recent_logs.return_value = [
            {
                'timestamp': '2024-01-15T10:00:00',
                'message': 'Dashboard started',
                'level': 'info',
                'source': 'dashboard'
            }
        ]
        yield service


@pytest.fixture
def sample_camera_settings():
    """Sample camera settings for testing"""
    return {
        'exposure_mode': 'auto',
        'iso': 400,
        'resolution': '4056x3040',
        'gain': 2.0
    }


@pytest.fixture
def sample_config_data():
    """Sample configuration data for testing"""
    return {
        'camera': {
            'exposure': 'auto',
            'iso': 400,
            'resolution': '4056x3040',
            'gain': 2.0
        },
        'capture': {
            'interval': 30,
            'format': 'jpg',
            'quality': 95
        },
        'storage': {
            'path': '/opt/cinepi/captures',
            'max_files': 10000
        }
    }


@pytest.fixture
def temp_file():
    """Create a temporary file for testing"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write('test content')
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    try:
        Path(temp_path).unlink()
    except FileNotFoundError:
        pass 