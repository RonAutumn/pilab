"""
Test error handling for API endpoints

This test verifies that the API properly returns 400 errors for invalid JSON
and invalid camera settings, rather than 500 errors.
"""

import json
import pytest
from dashboard import create_app


@pytest.fixture
def client():
    """Create test client"""
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_invalid_json_camera_settings(client):
    """Test that invalid JSON returns 400 error for camera settings"""
    # Send invalid JSON
    response = client.put('/api/camera/settings', 
                         data='{"exposure_mode": "auto", "iso": 400,}',  # Invalid JSON
                         content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'Invalid JSON' in data['error']


def test_invalid_camera_settings_validation(client):
    """Test that invalid camera settings return 400 error"""
    # Send valid JSON but invalid camera settings
    invalid_settings = {
        "exposure_mode": "invalid_mode",  # Invalid exposure mode
        "iso": 999,  # Invalid ISO
        "resolution": "invalid_resolution",  # Invalid resolution
        "gain": 10.0  # Invalid gain
    }
    
    response = client.put('/api/camera/settings',
                         data=json.dumps(invalid_settings),
                         content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'error' in data


def test_invalid_json_config_update(client):
    """Test that invalid JSON returns 400 error for config update"""
    # Send invalid JSON
    response = client.put('/api/config',
                         data='{"capture": {"interval": 30,}',  # Invalid JSON
                         content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'Invalid JSON' in data['error']


def test_invalid_json_capture_start(client):
    """Test that invalid JSON returns 400 error for capture start"""
    # Send invalid JSON
    response = client.post('/api/capture/start',
                          data='{"interval": 30,}',  # Invalid JSON
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'Invalid JSON' in data['error']


def test_invalid_interval_validation(client):
    """Test that invalid interval returns 400 error"""
    # Send valid JSON but invalid interval
    invalid_data = {"interval": 9999}  # Invalid interval
    
    response = client.post('/api/capture/start',
                          data=json.dumps(invalid_data),
                          content_type='application/json')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'Invalid interval' in data['error']


def test_missing_content_type(client):
    """Test that missing Content-Type returns 400 error"""
    # Send data without Content-Type header
    response = client.put('/api/camera/settings',
                         data='{"exposure_mode": "auto"}')
    
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data['success'] is False
    assert 'Content-Type must be application/json' in data['error']


if __name__ == '__main__':
    pytest.main([__file__]) 
