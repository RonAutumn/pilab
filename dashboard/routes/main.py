"""
CinePi Dashboard Main Routes

This module contains the main dashboard routes for the web interface.
"""

from flask import Blueprint, render_template, current_app, jsonify
from dashboard.services.camera_service import CameraService
from dashboard.services.capture_service import CaptureService

# Create main blueprint
main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def dashboard():
    """
    Main dashboard page
    
    Returns:
        str: Rendered dashboard template
    """
    try:
        # Get initial data for dashboard
        camera_service = CameraService()
        capture_service = CaptureService()
        
        context = {
            'camera_status': camera_service.get_status(),
            'session_info': capture_service.get_session_info(),
            'config': {
                'supported_resolutions': current_app.config['SUPPORTED_RESOLUTIONS'],
                'min_interval': current_app.config['MIN_INTERVAL'],
                'max_interval': current_app.config['MAX_INTERVAL'],
                'default_interval': current_app.config['DEFAULT_INTERVAL']
            }
        }
        
        return render_template('dashboard.html', **context)
        
    except Exception as e:
        current_app.logger.error(f"Error loading dashboard: {e}")
        return render_template('error.html', error=str(e)), 500


@main_bp.route('/stream')
def mjpeg_stream():
    """
    MJPEG stream endpoint for live camera preview
    
    Returns:
        Response: MJPEG stream response
    """
    try:
        camera_service = CameraService()
        return camera_service.get_mjpeg_stream()
    except Exception as e:
        current_app.logger.error(f"Error in MJPEG stream: {e}")
        return jsonify({'error': str(e)}), 500


@main_bp.route('/snapshot')
def snapshot():
    """
    Manual snapshot endpoint
    
    Returns:
        Response: Snapshot image or JSON response
    """
    try:
        camera_service = CameraService()
        return camera_service.take_snapshot()
    except Exception as e:
        current_app.logger.error(f"Error taking snapshot: {e}")
        return jsonify({'error': str(e)}), 500


@main_bp.route('/status')
def status():
    """
    Current system status endpoint
    
    Returns:
        dict: JSON response with current status
    """
    try:
        camera_service = CameraService()
        capture_service = CaptureService()
        
        status_data = {
            'camera': camera_service.get_status(),
            'session': capture_service.get_session_info(),
            'system': {
                'uptime': '2h 15m',  # TODO: Implement actual uptime
                'version': '1.0.0'
            }
        }
        
        return jsonify(status_data)
        
    except Exception as e:
        current_app.logger.error(f"Error getting status: {e}")
        return jsonify({'error': str(e)}), 500


@main_bp.route('/health')
def health():
    """
    Health check endpoint
    
    Returns:
        dict: JSON response with health status
    """
    return jsonify({
        'status': 'healthy',
        'service': 'cinepi-dashboard',
        'version': '1.0.0',
        'uptime': '2h 15m'  # TODO: Implement actual uptime calculation
    }) 