"""
CinePi Dashboard Configuration Management

This module contains configuration classes for different environments
(development, production, testing) and manages application settings.
"""

import os
from pathlib import Path


class Config:
    """Base configuration class with common settings"""
    
    # Flask settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Application paths
    DASHBOARD_ROOT = Path(__file__).parent.parent
    STATIC_FOLDER = DASHBOARD_ROOT / 'dashboard' / 'static'
    TEMPLATE_FOLDER = DASHBOARD_ROOT / 'dashboard' / 'templates'
    
    # CinePi integration paths
    CINEPI_ROOT = Path('/opt/cinepi')
    CONFIG_PATH = CINEPI_ROOT / 'config' / 'cinepi.yaml'
    CAPTURES_PATH = CINEPI_ROOT / 'captures'
    LOGS_PATH = CINEPI_ROOT / 'logs'
    
    # WebSocket configuration
    SOCKETIO_MESSAGE_QUEUE = os.environ.get('SOCKETIO_MESSAGE_QUEUE') or 'redis://localhost:6379/0'
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'yaml', 'yml'}
    
    # Camera settings
    MAX_RESOLUTION = "4056x3040"
    SUPPORTED_RESOLUTIONS = [
        "4056x3040",
        "2028x1520", 
        "1014x760"
    ]
    
    # Capture settings
    MIN_INTERVAL = 5  # seconds
    MAX_INTERVAL = 3600  # seconds (1 hour)
    DEFAULT_INTERVAL = 30  # seconds
    
    # UI settings
    THEME = "light"
    AUTO_REFRESH = True
    REFRESH_INTERVAL = 1000  # milliseconds


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # Development-specific settings
    CINEPI_ROOT = Path(__file__).parent.parent / 'cinepi'  # Local development path
    CONFIG_PATH = CINEPI_ROOT / 'config' / 'cinepi.yaml'
    CAPTURES_PATH = CINEPI_ROOT / 'captures'
    LOGS_PATH = CINEPI_ROOT / 'logs'
    
    # Create directories if they don't exist
    def __init__(self):
        super().__init__()
        self.CAPTURES_PATH.mkdir(parents=True, exist_ok=True)
        self.LOGS_PATH.mkdir(parents=True, exist_ok=True)


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Production-specific settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'prod-secret-key-change-in-production'


class TestConfig(Config):
    """Testing configuration"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    
    # Testing-specific settings
    CINEPI_ROOT = Path(__file__).parent.parent / 'test_cinepi'
    CONFIG_PATH = CINEPI_ROOT / 'config' / 'test_cinepi.yaml'
    CAPTURES_PATH = CINEPI_ROOT / 'captures'
    LOGS_PATH = CINEPI_ROOT / 'logs'
    
    def __init__(self):
        super().__init__()
        # Create test directories
        self.CAPTURES_PATH.mkdir(parents=True, exist_ok=True)
        self.LOGS_PATH.mkdir(parents=True, exist_ok=True)


# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestConfig,
    'default': DevelopmentConfig
} 
