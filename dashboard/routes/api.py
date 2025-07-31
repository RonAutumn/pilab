"""
CinePi Dashboard API Routes

This module contains REST API endpoints for camera control and configuration.
"""

from flask import Blueprint, request, jsonify, current_app
from werkzeug.exceptions import BadRequest
from dashboard.services.capture_service import CaptureService
from dashboard.services.camera_service import CameraService
from dashboard.services.config_service import ConfigService
from dashboard.utils.validators import validate_interval, validate_camera_settings, validate_filename
import json
from datetime import datetime

# Create API blueprint
api_bp = Blueprint('api', __name__)


def validate_json_request():
    """
    Validate that the request contains valid JSON
    Returns the parsed JSON data or raises appropriate error
    """
    if not request.is_json:
        raise BadRequest("Content-Type must be application/json")
    
    try:
        return request.get_json()
    except BadRequest:
        raise BadRequest("Invalid JSON format")
    except Exception as e:
        raise BadRequest(f"JSON parsing error: {str(e)}")


@api_bp.route('/capture/start', methods=['POST'])
def start_capture():
    """
    Start timelapse capture session
    
    Expected JSON payload:
    {
        "interval": 30  // seconds, optional (default: 30)
    }
    
    Returns:
        dict: JSON response with operation result
    """
    try:
        data = validate_json_request() or {}
        interval = data.get('interval', current_app.config['DEFAULT_INTERVAL'])
        
        # Validate interval
        if not validate_interval(interval):
            return jsonify({
                'success': False,
                'error': f'Invalid interval. Must be between {current_app.config["MIN_INTERVAL"]} and {current_app.config["MAX_INTERVAL"]} seconds'
            }), 400
        
        capture_service = CaptureService()
        result = capture_service.start_session(interval)
        
        return jsonify(result)
        
    except BadRequest as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error starting capture: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/capture/stop', methods=['POST'])
def stop_capture():
    """
    Stop timelapse capture session
    
    Returns:
        dict: JSON response with operation result
    """
    try:
        capture_service = CaptureService()
        result = capture_service.stop_session()
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error stopping capture: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/capture/status', methods=['GET'])
def get_capture_status():
    """
    Get current capture session status
    
    Returns:
        dict: JSON response with session status
    """
    try:
        capture_service = CaptureService()
        status = capture_service.get_session_info()
        
        return jsonify(status)
        
    except Exception as e:
        current_app.logger.error(f"Error getting capture status: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/capture/list', methods=['GET'])
def list_captures():
    """
    Get list of recent captures
    
    Query parameters:
        limit (int): Maximum number of captures to return (default: 50)
    
    Returns:
        dict: JSON response with list of captures
    """
    try:
        limit = request.args.get('limit', 50, type=int)
        if limit <= 0 or limit > 1000:
            return jsonify({
                'success': False,
                'error': 'Limit must be between 1 and 1000'
            }), 400
        
        capture_service = CaptureService()
        captures = capture_service.get_capture_list(limit)
        
        return jsonify({
            'success': True,
            'captures': captures,
            'count': len(captures)
        })
        
    except Exception as e:
        current_app.logger.error(f"Error listing captures: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/capture/delete/<filename>', methods=['DELETE'])
def delete_capture(filename):
    """
    Delete a specific capture file
    
    Args:
        filename (str): Name of the file to delete
    
    Returns:
        dict: JSON response with operation result
    """
    try:
        # Validate filename for security
        if not validate_filename(filename):
            return jsonify({
                'success': False,
                'error': 'Invalid filename'
            }), 400
        
        capture_service = CaptureService()
        result = capture_service.delete_capture(filename)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error deleting capture: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/capture/interval', methods=['PUT'])
def update_interval():
    """
    Update capture interval during active session
    
    Expected JSON payload:
    {
        "interval": 60  // new interval in seconds
    }
    
    Returns:
        dict: JSON response with operation result
    """
    try:
        data = validate_json_request()
        if not data or 'interval' not in data:
            return jsonify({
                'success': False,
                'error': 'Interval parameter is required'
            }), 400
        
        interval = data['interval']
        
        # Validate interval
        if not validate_interval(interval):
            return jsonify({
                'success': False,
                'error': f'Invalid interval. Must be between {current_app.config["MIN_INTERVAL"]} and {current_app.config["MAX_INTERVAL"]} seconds'
            }), 400
        
        capture_service = CaptureService()
        result = capture_service.update_interval(interval)
        
        return jsonify(result)
        
    except BadRequest as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error updating interval: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/capture/manual', methods=['POST'])
def manual_capture():
    """
    Take manual snapshot
    
    Returns:
        dict: JSON response with operation result
    """
    try:
        camera_service = CameraService()
        result = camera_service.take_snapshot()
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error taking manual capture: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/camera/settings', methods=['GET'])
def get_camera_settings():
    """
    Get current camera settings
    
    Returns:
        dict: JSON response with camera settings
    """
    try:
        camera_service = CameraService()
        settings = camera_service.get_settings()
        
        return jsonify(settings)
        
    except Exception as e:
        current_app.logger.error(f"Error getting camera settings: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/camera/parameters', methods=['GET'])
def get_camera_parameters():
    """
    Get supported camera parameters and ranges
    
    Returns:
        dict: JSON response with supported parameters
    """
    try:
        camera_service = CameraService()
        parameters = camera_service.get_supported_parameters()
        
        return jsonify(parameters)
        
    except Exception as e:
        current_app.logger.error(f"Error getting camera parameters: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/camera/settings', methods=['PUT'])
def update_camera_settings():
    """
    Update camera settings
    
    Expected JSON payload:
    {
        "exposure_mode": "auto",  // "auto" or "manual"
        "iso": 400,          // 100-800
        "resolution": "4056x3040",  // from supported resolutions
        "gain": 2.0          // 1.0-8.0
    }
    
    Returns:
        dict: JSON response with operation result
    """
    try:
        data = validate_json_request()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate camera settings
        validation_result = validate_camera_settings(data, current_app.config)
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'error': validation_result['error']
            }), 400
        
        camera_service = CameraService()
        result = camera_service.update_settings(data)
        
        return jsonify(result)
        
    except BadRequest as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error updating camera settings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/status', methods=['GET'])
def get_system_status():
    """
    Get real-time system status including camera, session, and system information
    
    Returns:
        dict: JSON response with comprehensive system status
    """
    try:
        from dashboard.services.websocket_service import WebSocketService
        
        ws_service = WebSocketService()
        status = ws_service.get_current_status()
        
        return jsonify(status)
        
    except Exception as e:
        current_app.logger.error(f"Error getting system status: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/status/stream', methods=['GET'])
def stream_status():
    """
    Stream real-time status updates using Server-Sent Events (SSE)
    
    Returns:
        Response: Server-Sent Events stream
    """
    try:
        from flask import Response
        from dashboard.services.websocket_service import WebSocketService
        import time
        
        def generate():
            ws_service = WebSocketService()
            
            while True:
                try:
                    status = ws_service.get_current_status()
                    yield f"data: {json.dumps(status)}\n\n"
                    time.sleep(2)  # Update every 2 seconds
                except Exception as e:
                    error_data = {'error': str(e), 'timestamp': datetime.now().isoformat()}
                    yield f"data: {json.dumps(error_data)}\n\n"
                    time.sleep(5)  # Wait longer on error
        
        return Response(generate(), mimetype='text/event-stream')
        
    except Exception as e:
        current_app.logger.error(f"Error streaming status: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/logs', methods=['GET'])
def get_logs():
    """
    Get recent system logs
    
    Query Parameters:
        limit (int): Maximum number of log entries (default: 50)
        level (str): Filter by log level (info, warning, error)
    
    Returns:
        dict: JSON response with log entries
    """
    try:
        from dashboard.services.websocket_service import WebSocketService
        
        limit = request.args.get('limit', 50, type=int)
        level = request.args.get('level', None)
        
        ws_service = WebSocketService()
        logs = ws_service.get_recent_logs(limit)
        
        # Filter by level if specified
        if level:
            logs = [log for log in logs if log.get('level') == level]
        
        return jsonify({
            'logs': logs,
            'count': len(logs),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error getting logs: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/config', methods=['GET'])
def get_config():
    """
    Get current CinePi configuration
    
    Returns:
        dict: JSON response with configuration
    """
    try:
        config_service = ConfigService()
        config_data = config_service.get_config()
        
        return jsonify(config_data)
        
    except Exception as e:
        current_app.logger.error(f"Error getting config: {e}")
        return jsonify({'error': str(e)}), 500


@api_bp.route('/config', methods=['PUT'])
def update_config():
    """
    Update CinePi configuration
    
    Expected JSON payload:
    {
        // YAML configuration data
    }
    
    Returns:
        dict: JSON response with operation result
    """
    try:
        data = validate_json_request()
        if not data:
            return jsonify({'success': False, 'error': 'No configuration data provided'}), 400
        
        config_service = ConfigService()
        result = config_service.update_config(data)
        
        return jsonify(result)
        
    except BadRequest as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error updating config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/config/backup', methods=['POST'])
def create_backup():
    """
    Create configuration backup
    
    Returns:
        dict: JSON response with backup result
    """
    try:
        config_service = ConfigService()
        result = config_service.create_backup()
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error creating backup: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@api_bp.route('/config/restore', methods=['POST'])
def restore_backup():
    """
    Restore configuration from backup
    
    Expected JSON payload:
    {
        "backup_file": "cinepi_backup_20240115_143000.yaml"
    }
    
    Returns:
        dict: JSON response with restore result
    """
    try:
        data = validate_json_request()
        if not data or 'backup_file' not in data:
            return jsonify({'success': False, 'error': 'Backup file not specified'}), 400
        
        config_service = ConfigService()
        result = config_service.restore_backup(data['backup_file'])
        
        return jsonify(result)
        
    except BadRequest as e:
        return jsonify({'success': False, 'error': str(e)}), 400
    except Exception as e:
        current_app.logger.error(f"Error restoring backup: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500 
