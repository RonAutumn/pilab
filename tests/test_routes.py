"""
Unit tests for dashboard Flask routes
"""

import pytest
import json
from unittest.mock import patch, Mock
from flask import Flask
from dashboard.routes.api import api_bp


class TestCaptureRoutes:
    """Test capture-related API routes"""
    
    def test_start_capture_success(self, client, mock_capture_service):
        """Test successful capture start"""
        with patch('dashboard.routes.api.CaptureService', return_value=mock_capture_service):
            response = client.post('/api/capture/start', 
                                 json={'interval': 30})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'Session started with 30s interval' in data['message']
    
    def test_start_capture_default_interval(self, client, mock_capture_service):
        """Test capture start with default interval"""
        with patch('dashboard.routes.api.CaptureService', return_value=mock_capture_service):
            response = client.post('/api/capture/start', json={})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
    
    def test_start_capture_invalid_interval(self, client):
        """Test capture start with invalid interval"""
        response = client.post('/api/capture/start', 
                             json={'interval': 1})  # Too low
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Invalid interval' in data['error']
    
    def test_start_capture_invalid_interval_high(self, client):
        """Test capture start with interval too high"""
        response = client.post('/api/capture/start', 
                             json={'interval': 7200})  # Too high
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Invalid interval' in data['error']
    
    def test_start_capture_service_error(self, client):
        """Test capture start with service error"""
        mock_service = Mock()
        mock_service.start_session.return_value = {
            'success': False,
            'error': 'Camera not available'
        }
        
        with patch('dashboard.routes.api.CaptureService', return_value=mock_service):
            response = client.post('/api/capture/start', 
                                 json={'interval': 30})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Camera not available' in data['error']
    
    def test_stop_capture_success(self, client, mock_capture_service):
        """Test successful capture stop"""
        with patch('dashboard.routes.api.CaptureService', return_value=mock_capture_service):
            response = client.post('/api/capture/stop')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'Session stopped' in data['message']
    
    def test_stop_capture_service_error(self, client):
        """Test capture stop with service error"""
        mock_service = Mock()
        mock_service.stop_session.return_value = {
            'success': False,
            'error': 'No active session'
        }
        
        with patch('dashboard.routes.api.CaptureService', return_value=mock_service):
            response = client.post('/api/capture/stop')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'No active session' in data['error']
    
    def test_get_capture_status_success(self, client, mock_capture_service):
        """Test successful capture status retrieval"""
        with patch('dashboard.routes.api.CaptureService', return_value=mock_capture_service):
            response = client.get('/api/capture/status')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'active'
            assert data['captures'] == 10
    
    def test_get_capture_status_service_error(self, client):
        """Test capture status with service error"""
        mock_service = Mock()
        mock_service.get_session_info.side_effect = Exception('Service error')
        
        with patch('dashboard.routes.api.CaptureService', return_value=mock_service):
            response = client.get('/api/capture/status')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_list_captures_success(self, client, mock_capture_service):
        """Test successful capture list retrieval"""
        with patch('dashboard.routes.api.CaptureService', return_value=mock_capture_service):
            response = client.get('/api/capture/list?limit=10')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'captures' in data
            assert 'count' in data
            assert len(data['captures']) == 1
    
    def test_list_captures_invalid_limit(self, client):
        """Test capture list with invalid limit"""
        response = client.get('/api/capture/list?limit=0')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Limit must be between 1 and 1000' in data['error']
    
    def test_list_captures_limit_too_high(self, client):
        """Test capture list with limit too high"""
        response = client.get('/api/capture/list?limit=2000')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Limit must be between 1 and 1000' in data['error']
    
    def test_delete_capture_success(self, client, mock_capture_service):
        """Test successful capture deletion"""
        mock_capture_service.delete_capture.return_value = {
            'success': True,
            'message': 'Deleted capture_001.jpg'
        }
        
        with patch('dashboard.routes.api.CaptureService', return_value=mock_capture_service):
            response = client.delete('/api/capture/delete/capture_001.jpg')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'Deleted capture_001.jpg' in data['message']
    
    def test_delete_capture_invalid_filename(self, client):
        """Test capture deletion with invalid filename"""
        response = client.delete('/api/capture/delete/test.exe')

        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Invalid filename' in data['error']
    
    def test_delete_capture_wrong_extension(self, client):
        """Test capture deletion with wrong file extension"""
        response = client.delete('/api/capture/delete/file.txt')
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Invalid filename' in data['error']
    
    def test_update_interval_success(self, client, mock_capture_service):
        """Test successful interval update"""
        with patch('dashboard.routes.api.CaptureService', return_value=mock_capture_service):
            response = client.put('/api/capture/interval', 
                                json={'interval': 60})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'Interval updated to 60s' in data['message']
    
    def test_update_interval_missing_parameter(self, client):
        """Test interval update with missing parameter"""
        response = client.put('/api/capture/interval', json={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Interval parameter is required' in data['error']
    
    def test_update_interval_invalid_value(self, client):
        """Test interval update with invalid value"""
        response = client.put('/api/capture/interval', 
                            json={'interval': 1})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Invalid interval' in data['error']
    
    def test_manual_capture_success(self, client, mock_camera_service):
        """Test successful manual capture"""
        with patch('dashboard.routes.api.CameraService', return_value=mock_camera_service):
            response = client.post('/api/capture/manual')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'Manual snapshot taken successfully' in data['message']


class TestCameraRoutes:
    """Test camera-related API routes"""
    
    def test_get_camera_settings_success(self, client, mock_camera_service):
        """Test successful camera settings retrieval"""
        with patch('dashboard.routes.api.CameraService', return_value=mock_camera_service):
            response = client.get('/api/camera/settings')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['exposure'] == 'auto'
            assert data['iso'] == 400
            assert data['resolution'] == '4056x3040'
            assert data['gain'] == 2.0
    
    def test_get_camera_parameters_success(self, client, mock_camera_service):
        """Test successful camera parameters retrieval"""
        with patch('dashboard.routes.api.CameraService', return_value=mock_camera_service):
            response = client.get('/api/camera/parameters')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'iso' in data
            assert 'gain' in data
            assert 'exposure_modes' in data
            assert 'resolutions' in data
    
    def test_update_camera_settings_success(self, client, mock_camera_service):
        """Test successful camera settings update"""
        with patch('dashboard.routes.api.CameraService', return_value=mock_camera_service):
            response = client.put('/api/camera/settings', 
                                json={
                                    'exposure_mode': 'manual',
                                    'iso': 800,
                                    'resolution': '4056x3040',
                                    'gain': 4.0
                                })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'Settings updated successfully' in data['message']
    
    def test_update_camera_settings_no_data(self, client):
        """Test camera settings update with no data"""
        response = client.put('/api/camera/settings', json={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'No data provided' in data['error']
    
    def test_update_camera_settings_invalid_exposure(self, client):
        """Test camera settings update with invalid exposure mode"""
        response = client.put('/api/camera/settings', 
                            json={'exposure_mode': 'invalid'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Exposure mode must be "auto" or "manual"' in data['error']
    
    def test_update_camera_settings_invalid_iso(self, client):
        """Test camera settings update with invalid ISO"""
        response = client.put('/api/camera/settings', 
                            json={'iso': 1000})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'ISO must be between 100 and 800' in data['error']
    
    def test_update_camera_settings_invalid_resolution(self, client):
        """Test camera settings update with invalid resolution"""
        response = client.put('/api/camera/settings', 
                            json={'resolution': 'invalid'})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Resolution must be one of' in data['error']
    
    def test_update_camera_settings_invalid_gain(self, client):
        """Test camera settings update with invalid gain"""
        response = client.put('/api/camera/settings', 
                            json={'gain': 10.0})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Gain must be between 1.0 and 8.0' in data['error']


class TestStatusRoutes:
    """Test status-related API routes"""
    
    def test_get_system_status_success(self, client, mock_websocket_service):
        """Test successful system status retrieval"""
        with patch('dashboard.services.websocket_service.WebSocketService', return_value=mock_websocket_service):
            response = client.get('/api/status')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'camera' in data
            assert 'session' in data
            assert 'system' in data
            assert 'timestamp' in data
    
    def test_get_system_status_service_error(self, client):
        """Test system status with service error"""
        mock_service = Mock()
        mock_service.get_current_status.side_effect = Exception('Service error')

        with patch('dashboard.services.websocket_service.WebSocketService', return_value=mock_service):
            response = client.get('/api/status')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_stream_status_success(self, client, mock_websocket_service):
        """Test successful status streaming"""
        with patch('dashboard.services.websocket_service.WebSocketService', return_value=mock_websocket_service):
            response = client.get('/api/status/stream')
            
            assert response.status_code == 200
            assert response.mimetype == 'text/event-stream'
    
    def test_get_logs_success(self, client, mock_websocket_service):
        """Test successful logs retrieval"""
        with patch('dashboard.services.websocket_service.WebSocketService', return_value=mock_websocket_service):
            response = client.get('/api/logs?limit=10&level=info')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'logs' in data
            assert 'count' in data
            assert 'timestamp' in data
            assert len(data['logs']) == 1
    
    def test_get_logs_default_parameters(self, client, mock_websocket_service):
        """Test logs retrieval with default parameters"""
        with patch('dashboard.services.websocket_service.WebSocketService', return_value=mock_websocket_service):
            response = client.get('/api/logs')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'logs' in data
            assert 'count' in data


class TestConfigRoutes:
    """Test configuration-related API routes"""
    
    def test_get_config_success(self, client, mock_config_service):
        """Test successful configuration retrieval"""
        with patch('dashboard.routes.api.ConfigService', return_value=mock_config_service):
            response = client.get('/api/config')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert 'camera' in data
            assert 'capture' in data
            assert 'storage' in data
    
    def test_update_config_success(self, client, mock_config_service):
        """Test successful configuration update"""
        with patch('dashboard.routes.api.ConfigService', return_value=mock_config_service):
            response = client.put('/api/config', 
                                json={
                                    'camera': {'exposure': 'manual', 'iso': 800},
                                    'capture': {'interval': 60},
                                    'storage': {'path': '/opt/cinepi/captures'}
                                })
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'Configuration updated successfully' in data['message']
    
    def test_update_config_no_data(self, client):
        """Test configuration update with no data"""
        response = client.put('/api/config', json={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'No configuration data provided' in data['error']
    
    def test_create_backup_success(self, client, mock_config_service):
        """Test successful backup creation"""
        with patch('dashboard.routes.api.ConfigService', return_value=mock_config_service):
            response = client.post('/api/config/backup')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'backup_file' in data
    
    def test_restore_backup_success(self, client, mock_config_service):
        """Test successful backup restoration"""
        with patch('dashboard.routes.api.ConfigService', return_value=mock_config_service):
            response = client.post('/api/config/restore', 
                                 json={'backup_file': 'cinepi_backup_20240115_143000.yaml'})
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'Configuration restored successfully' in data['message']
    
    def test_restore_backup_missing_file(self, client):
        """Test backup restoration with missing file parameter"""
        response = client.post('/api/config/restore', json={})
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Backup file not specified' in data['error']


class TestErrorHandling:
    """Test error handling in routes"""
    
    def test_route_exception_handling(self, client):
        """Test that route exceptions are properly handled"""
        mock_service = Mock()
        mock_service.get_status.side_effect = Exception('Unexpected error')
        
        with patch('dashboard.routes.api.CameraService', return_value=mock_service):
            response = client.get('/api/camera/settings')
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_invalid_json_handling(self, client):
        """Test handling of invalid JSON in requests"""
        response = client.post('/api/capture/start',
                             data='invalid json',
                             content_type='application/json')

        assert response.status_code == 500  # Should return 500 for invalid JSON
    
    def test_missing_content_type(self, client):
        """Test handling of requests without content type"""
        response = client.post('/api/capture/start',
                             data='{"interval": 30}')

        assert response.status_code == 500  # Should return 500 for missing content type 