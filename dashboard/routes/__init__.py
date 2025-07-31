"""
CinePi Dashboard Routes Package

This package contains all route definitions and blueprints for the dashboard.
"""

from flask import Blueprint

# Import route modules
from .main import main_bp
from .api import api_bp
# Note: WebSocket events are handled via Flask-SocketIO in dashboard/routes/websocket.py.
# We do not register a standard Flask blueprint at '/ws' because Socket.IO does not use HTTP GET /ws.
# Import ensures event handlers are registered when the app starts.
from .websocket import websocket_bp
from .editor import editor_bp


def init_routes(app):
    """
    Initialize and register all route blueprints with the Flask app
    
    Args:
        app (Flask): Flask application instance
    """
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')
    # Do NOT register websocket_bp as a Flask blueprint at '/ws'.
    # Socket.IO uses its own Engine.IO transport at '/socket.io'.
    # Importing dashboard.routes.websocket registers event handlers on the global socketio instance.
    # If a health endpoint is needed, expose it via /api/status/stream (SSE) which already exists.
    # app.register_blueprint(websocket_bp, url_prefix='/ws')  # removed
    app.register_blueprint(editor_bp)
    
    print(f"Registered blueprints: {list(app.blueprints.keys())}")
