"""
CinePi Dashboard Flask Application Factory

This module contains the Flask application factory pattern for creating
the CinePi dashboard application with proper configuration and extensions.
"""

from flask import Flask
from flask_socketio import SocketIO
from pathlib import Path
from logging.handlers import RotatingFileHandler
import logging
import os

from dashboard.extensions import init_extensions
from dashboard.routes import init_routes
from dashboard.services import init_services
# Ensure websocket handlers (including /ws namespace) are registered
import dashboard.routes.websocket  # noqa: F401


def create_app(config_name='development'):
    """
    Application factory pattern for Flask app creation
    
    Args:
        config_name (str): Configuration name ('development', 'production', 'testing')
    
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration
    if config_name == 'testing':
        app.config.from_object('dashboard.config.TestConfig')
    else:
        app.config.from_object(f'dashboard.config.{config_name.capitalize()}Config')
    
    # Initialize extensions (SocketIO, etc.)
    init_extensions(app)
    
    # Initialize services
    init_services(app)
    
    # Register routes and blueprints
    init_routes(app)
    
    # Register error handlers
    register_error_handlers(app)

    # Setup rotating file logging (logs/dashboard.log)
    setup_logging(app)
    
    return app


def register_error_handlers(app):
    """Register error handlers for the application"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return {'error': 'Internal server error'}, 500


def setup_logging(app):
    """Configure rotating file logging at logs/dashboard.log"""
    try:
        logs_dir = Path('logs')
        logs_dir.mkdir(exist_ok=True)
        log_path = logs_dir / 'dashboard.log'

        handler = RotatingFileHandler(str(log_path), maxBytes=2 * 1024 * 1024, backupCount=5)
        formatter = logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s - %(message)s'
        )
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)

        root_logger = logging.getLogger()
        # Avoid duplicate handlers if reloaded
        if not any(isinstance(h, RotatingFileHandler) and getattr(h, 'baseFilename', '') == str(log_path) for h in root_logger.handlers):
            root_logger.addHandler(handler)

        app.logger.addHandler(handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('Logging initialized. Writing to %s', log_path)
    except Exception as e:
        print(f'Failed to configure logging: {e}')


def create_socketio_app(app):
    """
    Create SocketIO instance for the Flask app
    
    Args:
        app (Flask): Flask application instance
    
    Returns:
        SocketIO: Configured SocketIO instance
    """
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",
        async_mode='threading',
        logger=True,
        engineio_logger=True
    )
    return socketio


if __name__ == '__main__':
    # Development server
    app = create_app('development')
    socketio = create_socketio_app(app)
    
    print("Starting CinePi Dashboard...")
    print(f"Dashboard URL: http://localhost:5000")
    print(f"SocketIO URL: http://localhost:5000")
    
    socketio.run(
        app,
        host='0.0.0.0',
        port=5000,
        debug=True,
        use_reloader=True
    )
