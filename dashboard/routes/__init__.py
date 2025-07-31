"""
CinePi Dashboard Routes Package

This package contains all route definitions and blueprints for the dashboard.
"""

from flask import Blueprint

# Import route modules
from .main import main_bp
from .api import api_bp
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
    app.register_blueprint(websocket_bp, url_prefix='/ws')
    app.register_blueprint(editor_bp)
    
    print(f"Registered blueprints: {list(app.blueprints.keys())}") 
