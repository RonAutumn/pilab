"""
CinePi Dashboard Flask Extensions

This module initializes and configures Flask extensions used by the dashboard.
"""

from flask_socketio import SocketIO
from flask_compress import Compress

# Initialize extensions
socketio = SocketIO()
compress = Compress()


def init_extensions(app):
    """
    Initialize Flask extensions with the application
    
    Args:
        app (Flask): Flask application instance
    """
    # Initialize SocketIO for real-time communication
    socketio.init_app(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        logger=app.debug,
        engineio_logger=app.debug
    )
    
    # Initialize compression for static assets
    compress.init_app(app)
    
    # Store socketio instance on app for access in routes
    app.socketio = socketio 