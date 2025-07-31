"""
CinePi Dashboard WebSocket Routes

This module contains WebSocket event handlers for real-time communication.
"""

from flask import Blueprint, current_app, request
from flask_socketio import emit, join_room, leave_room
from dashboard.extensions import socketio
from dashboard.services.websocket_service import WebSocketService

# Create WebSocket blueprint
websocket_bp = Blueprint('websocket', __name__)


@socketio.on('connect')
def handle_connect():
    """
    Handle client connection to WebSocket
    
    Emits:
        status: Connection confirmation message
    """
    print(f'Client connected: {request.sid}')
    emit('status', {
        'message': 'Connected to CinePi Dashboard',
        'type': 'success'
    })


@socketio.on('disconnect')
def handle_disconnect():
    """
    Handle client disconnection from WebSocket
    """
    print(f'Client disconnected: {request.sid}')


@socketio.on('join_dashboard')
def handle_join_dashboard():
    """
    Join dashboard room for real-time updates
    
    Emits:
        joined: Confirmation of room join
        status_update: Current system status
    """
    join_room('dashboard')
    emit('joined', {'room': 'dashboard'})
    
    # Send current status
    ws_service = WebSocketService()
    status = ws_service.get_current_status()
    emit('status_update', status)


@socketio.on('leave_dashboard')
def handle_leave_dashboard():
    """
    Leave dashboard room
    """
    leave_room('dashboard')
    emit('left', {'room': 'dashboard'})


@socketio.on('request_status')
def handle_status_request():
    """
    Handle status request from client
    
    Emits:
        status_update: Current system status
    """
    ws_service = WebSocketService()
    status = ws_service.get_current_status()
    emit('status_update', status)


@socketio.on('request_logs')
def handle_logs_request():
    """
    Handle logs request from client
    
    Emits:
        log_entries: Recent log entries
    """
    ws_service = WebSocketService()
    logs = ws_service.get_recent_logs()
    emit('log_entries', logs)


@socketio.on('capture_started')
def handle_capture_started(data):
    """
    Handle capture started event
    
    Args:
        data (dict): Capture start data
    
    Emits:
        capture_update: Capture status update to all clients
    """
    # Broadcast to all clients in dashboard room
    socketio.emit('capture_update', {
        'type': 'started',
        'interval': data.get('interval'),
        'timestamp': data.get('timestamp')
    }, room='dashboard')


@socketio.on('capture_stopped')
def handle_capture_stopped(data):
    """
    Handle capture stopped event
    
    Args:
        data (dict): Capture stop data
    
    Emits:
        capture_update: Capture status update to all clients
    """
    # Broadcast to all clients in dashboard room
    socketio.emit('capture_update', {
        'type': 'stopped',
        'timestamp': data.get('timestamp')
    }, room='dashboard')


@socketio.on('capture_taken')
def handle_capture_taken(data):
    """
    Handle capture taken event
    
    Args:
        data (dict): Capture data
    
    Emits:
        capture_update: Capture update to all clients
    """
    # Broadcast to all clients in dashboard room
    socketio.emit('capture_update', {
        'type': 'taken',
        'filename': data.get('filename'),
        'timestamp': data.get('timestamp'),
        'count': data.get('count')
    }, room='dashboard')


@socketio.on('settings_updated')
def handle_settings_updated(data):
    """
    Handle settings updated event
    
    Args:
        data (dict): Settings update data
    
    Emits:
        settings_update: Settings update to all clients
    """
    # Broadcast to all clients in dashboard room
    socketio.emit('settings_update', {
        'settings': data.get('settings'),
        'timestamp': data.get('timestamp')
    }, room='dashboard')


@socketio.on('error_occurred')
def handle_error_occurred(data):
    """
    Handle error occurred event
    
    Args:
        data (dict): Error data
    
    Emits:
        error_update: Error notification to all clients
    """
    # Broadcast to all clients in dashboard room
    socketio.emit('error_update', {
        'error': data.get('error'),
        'timestamp': data.get('timestamp'),
        'severity': data.get('severity', 'error')
    }, room='dashboard') 
