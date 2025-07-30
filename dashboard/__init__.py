"""
CinePi Dashboard Application Package

This package contains the Flask-based web dashboard for CinePi camera control.
"""

from dashboard.app import create_app, create_socketio_app

__version__ = "1.0.0"
__author__ = "CinePi Team"
__description__ = "Web dashboard for CinePi timelapse camera control"

__all__ = ['create_app', 'create_socketio_app'] 