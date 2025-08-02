#!/usr/bin/env python3
"""
PiLab Web Dashboard

Flask-SocketIO web dashboard for monitoring PiLab storage, captures, and metrics
with real-time updates and comprehensive error handling.
"""

import os
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
from local_db_client import LocalDBClient, create_local_client

# Import our utilities
from utils.logging_utils import get_logger, setup_flask_logging, setup_socketio_logging
from utils.retry import retry_on_supabase_error, RetryError
from utils.chunked_processing import process_bulk_data, DEFAULT_CHUNK_SIZE

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'pilab-dashboard-secret-key')

# Initialize SocketIO
socketio = SocketIO(app, cors_allowed_origins="*", logger=True, engineio_logger=True, async_mode='threading')

# Setup logging
logger = get_logger('pilab.dashboard')
setup_flask_logging(app, 'pilab.dashboard')
setup_socketio_logging(socketio, 'pilab.socketio')

# Initialize local database client
client: Optional[LocalDBClient] = None


def initialize_client() -> bool:
    """Initialize the local database client."""
    global client
    
    try:
        client = create_local_client()
        if client.test_connection():
            logger.info("Successfully connected to local PiLab database")
            return True
        else:
            logger.error("Failed to connect to local database")
            return False
    except Exception as e:
        logger.error(f"Unexpected error initializing client: {e}")
        return False


@app.route('/')
def index():
    """Main dashboard page."""
    return render_template('dashboard.html')


@app.route('/api/storage/usage')
def get_storage_usage():
    """Get storage usage statistics."""
    if not client:
        return jsonify({'error': 'Client not initialized'}), 500
    
    try:
        usage = client.get_storage_usage('pilab-dev')
        return jsonify(usage)
    except Exception as e:
        logger.error(f"Error getting storage usage: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/upload/metrics')
def get_upload_metrics():
    """Get upload metrics for the last 24 hours."""
    if not client:
        return jsonify({'error': 'Client not initialized'}), 500
    
    try:
        metrics = client.get_upload_metrics_24h()
        return jsonify(metrics)
    except Exception as e:
        logger.error(f"Error getting upload metrics: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/captures/recent')
def get_recent_captures():
    """Get recent captures with chunked processing."""
    if not client:
        return jsonify({'error': 'Client not initialized'}), 500
    
    limit = request.args.get('limit', 10, type=int)
    
    try:
        captures = client.get_recent_captures(limit)
        return jsonify({'captures': captures})
    except Exception as e:
        logger.error(f"Error getting recent captures: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/alerts')
def get_alerts():
    """Get system alerts and warnings."""
    if not client:
        return jsonify({'error': 'Client not initialized'}), 500
    
    try:
        alerts = client.get_alerts()
        return jsonify({'alerts': alerts})
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/audit/logs')
def get_audit_logs():
    """Get recent audit logs with chunked processing."""
    if not client:
        return jsonify({'error': 'Client not initialized'}), 500
    
    limit = request.args.get('limit', 20, type=int)
    
    try:
        logs = client.get_audit_logs(limit)
        return jsonify({'logs': logs})
    except Exception as e:
        logger.error(f"Error getting audit logs: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/health')
def health_check():
    """Health check endpoint."""
    try:
        health_status = client.get_health_status() if client else {
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'supabase_connected': False,
            'error': 'Client not initialized'
        }
        return jsonify(health_status)
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'timestamp': datetime.utcnow().isoformat(),
            'supabase_connected': False,
            'error': str(e)
        }), 503


@app.route('/api/metrics')
def get_metrics():
    """Get system metrics in Prometheus format."""
    if not client:
        return jsonify({'error': 'Client not initialized'}), 500
    
    @retry_on_supabase_error(max_attempts=3)
    def _get_metrics():
        # Get basic metrics
        metrics = {
            'pilab_storage_files_total': 0,
            'pilab_storage_size_bytes': 0,
            'pilab_uploads_total': 0,
            'pilab_uploads_success_total': 0,
            'pilab_uploads_failed_total': 0,
            'pilab_captures_total': 0
        }
        
        # Storage metrics
        usage = client.get_storage_usage('pilab-dev')
        if not usage.get('error'):
            metrics['pilab_storage_files_total'] = usage.get('total_files', 0)
            metrics['pilab_storage_size_bytes'] = int(usage.get('total_size_mb', 0) * 1024 * 1024)
        
        # Upload metrics
        query = """
            SELECT 
                COUNT(*) as total_uploads,
                COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_uploads,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_uploads
            FROM upload_logs
        """
        
        result = client.client.rpc('exec_sql', {
            'query': query, 
            'params': []
        }).execute()
        
        if result.data:
            data = result.data[0]
            metrics['pilab_uploads_total'] = data['total_uploads']
            metrics['pilab_uploads_success_total'] = data['successful_uploads']
            metrics['pilab_uploads_failed_total'] = data['failed_uploads']
        
        # Capture metrics
        query = "SELECT COUNT(*) as total_captures FROM captures"
        result = client.client.rpc('exec_sql', {
            'query': query, 
            'params': []
        }).execute()
        
        if result.data:
            metrics['pilab_captures_total'] = result.data[0]['total_captures']
        
        return metrics
    
    try:
        metrics = _get_metrics()
        
        # Format as Prometheus metrics
        prometheus_metrics = []
        for name, value in metrics.items():
            prometheus_metrics.append(f"{name} {value}")
        
        return '\n'.join(prometheus_metrics), 200, {'Content-Type': 'text/plain'}
    except RetryError as e:
        logger.error(f"Failed to get metrics after retries: {e}")
        return jsonify({'error': 'Failed to retrieve metrics'}), 500
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        return jsonify({'error': str(e)}), 500


@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    logger.info(f"Client connected: {request.sid}")
    emit('status', {'message': 'Connected to PiLab Dashboard'})


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    logger.info(f"Client disconnected: {request.sid}")


@socketio.on('request_update')
def handle_update_request(data):
    """Handle real-time update requests."""
    try:
        update_type = data.get('type', 'all')
        
        if update_type in ['all', 'storage']:
            usage = client.get_storage_usage('pilab-dev') if client else {}
            emit('storage_update', usage)
        
        if update_type in ['all', 'metrics']:
            if client:
                metrics = client.get_upload_metrics_24h()
                emit('metrics_update', {
                    'total_uploads': metrics.get('total_uploads_24h', 0),
                    'successful_uploads': metrics.get('successful_uploads_24h', 0),
                    'failed_uploads': metrics.get('failed_uploads_24h', 0),
                    'success_rate': metrics.get('success_rate_24h', 0)
                })
        
        if update_type in ['all', 'alerts']:
            alerts = client.get_alerts() if client else []
            emit('alerts_update', {'alerts': alerts})
            
    except Exception as e:
        logger.error(f"Error handling update request: {e}")
        emit('error', {'message': 'Failed to update data'})


def start_background_tasks():
    """Start background tasks for real-time updates."""
    def send_periodic_updates():
        while True:
            try:
                socketio.sleep(30)  # Update every 30 seconds
                socketio.emit('periodic_update', {
                    'timestamp': datetime.utcnow().isoformat()
                })
            except Exception as e:
                logger.error(f"Error in periodic updates: {e}")
    
    socketio.start_background_task(send_periodic_updates)


if __name__ == '__main__':
    # Initialize client
    if not initialize_client():
        logger.error("Failed to initialize local database client")
        sys.exit(1)
    
    # Start background tasks
    start_background_tasks()
    
    # Run the app
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting PiLab Dashboard on port {port}")
    socketio.run(app, host='0.0.0.0', port=port, debug=debug) 