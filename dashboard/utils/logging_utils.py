#!/usr/bin/env python3
"""
Logging utilities for PiLab Dashboard

This module provides logging configuration for Flask and SocketIO applications.
"""

import logging
import sys
from typing import Optional


def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """
    Get a configured logger for the given name.
    
    Args:
        name: Logger name
        level: Optional log level override
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:  # Only configure if not already configured
        logger.setLevel(level or logging.INFO)
        
        # Create console handler
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(handler)
    
    return logger


def setup_flask_logging(app, logger_name: str = 'pilab.flask'):
    """
    Setup logging for Flask application.
    
    Args:
        app: Flask application instance
        logger_name: Name for the Flask logger
    """
    logger = get_logger(logger_name)
    
    # Configure Flask logging
    app.logger.handlers = []  # Remove default handlers
    app.logger.addHandler(logging.StreamHandler(sys.stdout))
    app.logger.setLevel(logging.INFO)
    
    # Set Flask logger to use our logger
    app.logger = logger


def setup_socketio_logging(socketio, logger_name: str = 'pilab.socketio'):
    """
    Setup logging for SocketIO application.
    
    Args:
        socketio: SocketIO application instance
        logger_name: Name for the SocketIO logger
    """
    logger = get_logger(logger_name)
    
    # Configure SocketIO logging
    socketio.logger = logger 