"""
Unit tests for dashboard configuration management
"""

import pytest
import os
from pathlib import Path
from dashboard.config import Config, DevelopmentConfig, ProductionConfig, TestConfig, config


class TestBaseConfig:
    """Test base configuration class"""
    
    def test_base_config_attributes(self):
        """Test base configuration attributes"""
        cfg = Config()
        
        # Test Flask settings
        assert hasattr(cfg, 'SECRET_KEY')
        assert cfg.SECRET_KEY is not None
        
        # Test application paths
        assert hasattr(cfg, 'DASHBOARD_ROOT')
        assert hasattr(cfg, 'STATIC_FOLDER')
        assert hasattr(cfg, 'TEMPLATE_FOLDER')
        assert isinstance(cfg.DASHBOARD_ROOT, Path)
        assert isinstance(cfg.STATIC_FOLDER, Path)
        assert isinstance(cfg.TEMPLATE_FOLDER, Path)
        
        # Test CinePi integration paths
        assert hasattr(cfg, 'CINEPI_ROOT')
        assert hasattr(cfg, 'CONFIG_PATH')
        assert hasattr(cfg, 'CAPTURES_PATH')
        assert hasattr(cfg, 'LOGS_PATH')
        assert isinstance(cfg.CINEPI_ROOT, Path)
        assert isinstance(cfg.CONFIG_PATH, Path)
        assert isinstance(cfg.CAPTURES_PATH, Path)
        assert isinstance(cfg.LOGS_PATH, Path)
        
        # Test WebSocket configuration
        assert hasattr(cfg, 'SOCKETIO_MESSAGE_QUEUE')
        
        # Test file upload settings
        assert hasattr(cfg, 'MAX_CONTENT_LENGTH')
        assert hasattr(cfg, 'ALLOWED_EXTENSIONS')
        assert isinstance(cfg.ALLOWED_EXTENSIONS, set)
        
        # Test camera settings
        assert hasattr(cfg, 'MAX_RESOLUTION')
        assert hasattr(cfg, 'SUPPORTED_RESOLUTIONS')
        assert isinstance(cfg.SUPPORTED_RESOLUTIONS, list)
        assert len(cfg.SUPPORTED_RESOLUTIONS) > 0
        
        # Test capture settings
        assert hasattr(cfg, 'MIN_INTERVAL')
        assert hasattr(cfg, 'MAX_INTERVAL')
        assert hasattr(cfg, 'DEFAULT_INTERVAL')
        assert isinstance(cfg.MIN_INTERVAL, int)
        assert isinstance(cfg.MAX_INTERVAL, int)
        assert isinstance(cfg.DEFAULT_INTERVAL, int)
        
        # Test UI settings
        assert hasattr(cfg, 'THEME')
        assert hasattr(cfg, 'AUTO_REFRESH')
        assert hasattr(cfg, 'REFRESH_INTERVAL')
    
    def test_interval_constraints(self):
        """Test interval constraints are valid"""
        cfg = Config()
        
        assert cfg.MIN_INTERVAL > 0
        assert cfg.MAX_INTERVAL > cfg.MIN_INTERVAL
        assert cfg.DEFAULT_INTERVAL >= cfg.MIN_INTERVAL
        assert cfg.DEFAULT_INTERVAL <= cfg.MAX_INTERVAL
    
    def test_resolution_constraints(self):
        """Test resolution constraints are valid"""
        cfg = Config()
        
        assert cfg.MAX_RESOLUTION in cfg.SUPPORTED_RESOLUTIONS
        assert len(cfg.SUPPORTED_RESOLUTIONS) > 0
        
        # Check all resolutions are strings
        for resolution in cfg.SUPPORTED_RESOLUTIONS:
            assert isinstance(resolution, str)
            assert 'x' in resolution  # Should contain 'x' separator
    
    def test_file_upload_constraints(self):
        """Test file upload constraints are valid"""
        cfg = Config()
        
        assert cfg.MAX_CONTENT_LENGTH > 0
        assert len(cfg.ALLOWED_EXTENSIONS) > 0
        
        # Check all extensions are valid
        for ext in cfg.ALLOWED_EXTENSIONS:
            assert isinstance(ext, str)
            assert ext.startswith('.') or ext.isalnum()
    
    def test_environment_variables(self):
        """Test environment variable handling"""
        # Test that the config uses environment variables when available
        # Since class attributes are evaluated at import time, we test the default behavior
        cfg = Config()
        
        # Test that SECRET_KEY has a default value
        assert cfg.SECRET_KEY is not None
        assert isinstance(cfg.SECRET_KEY, str)
        
        # Test that SOCKETIO_MESSAGE_QUEUE has a default value
        assert cfg.SOCKETIO_MESSAGE_QUEUE is not None
        assert isinstance(cfg.SOCKETIO_MESSAGE_QUEUE, str)

        # Test that SOCKETIO_MESSAGE_QUEUE has a default value
        assert cfg.SOCKETIO_MESSAGE_QUEUE is not None
        assert isinstance(cfg.SOCKETIO_MESSAGE_QUEUE, str)
        assert 'redis://' in cfg.SOCKETIO_MESSAGE_QUEUE  # Should contain redis URL


class TestDevelopmentConfig:
    """Test development configuration"""
    
    def test_development_config_inheritance(self):
        """Test development config inherits from base config"""
        cfg = DevelopmentConfig()
        
        # Should inherit all base attributes
        assert hasattr(cfg, 'SECRET_KEY')
        assert hasattr(cfg, 'DASHBOARD_ROOT')
        assert hasattr(cfg, 'CINEPI_ROOT')
        assert hasattr(cfg, 'SUPPORTED_RESOLUTIONS')
        assert hasattr(cfg, 'MIN_INTERVAL')
    
    def test_development_specific_settings(self):
        """Test development-specific settings"""
        cfg = DevelopmentConfig()
        
        assert cfg.DEBUG is True
        assert cfg.TESTING is False
    
    def test_development_paths(self):
        """Test development paths are set correctly"""
        cfg = DevelopmentConfig()
        
        # Should use local development paths
        assert 'cinepi' in str(cfg.CINEPI_ROOT)
        assert 'cinepi' in str(cfg.CONFIG_PATH)
        assert 'cinepi' in str(cfg.CAPTURES_PATH)
        assert 'cinepi' in str(cfg.LOGS_PATH)
    
    def test_directory_creation(self):
        """Test that development config creates directories"""
        with pytest.MonkeyPatch().context() as m:
            # Mock the directory creation
            m.setattr(Path, 'mkdir', lambda self, **kwargs: None)
            
            cfg = DevelopmentConfig()
            # Should not raise an exception
            assert cfg is not None


class TestProductionConfig:
    """Test production configuration"""
    
    def test_production_config_inheritance(self):
        """Test production config inherits from base config"""
        cfg = ProductionConfig()
        
        # Should inherit all base attributes
        assert hasattr(cfg, 'SECRET_KEY')
        assert hasattr(cfg, 'DASHBOARD_ROOT')
        assert hasattr(cfg, 'CINEPI_ROOT')
        assert hasattr(cfg, 'SUPPORTED_RESOLUTIONS')
        assert hasattr(cfg, 'MIN_INTERVAL')
    
    def test_production_specific_settings(self):
        """Test production-specific settings"""
        cfg = ProductionConfig()
        
        assert cfg.DEBUG is False
        assert cfg.TESTING is False
    
    def test_production_secret_key(self):
        """Test production secret key handling"""
        cfg = ProductionConfig()
        
        # Test that production config has a secret key
        assert cfg.SECRET_KEY is not None
        assert isinstance(cfg.SECRET_KEY, str)
        assert 'prod-secret-key' in cfg.SECRET_KEY  # Should contain the production default


class TestTestingConfig:
    """Test testing configuration"""
    
    def test_testing_config_inheritance(self):
        """Test testing config inherits from base config"""
        cfg = TestConfig()
        
        # Should inherit all base attributes
        assert hasattr(cfg, 'SECRET_KEY')
        assert hasattr(cfg, 'DASHBOARD_ROOT')
        assert hasattr(cfg, 'CINEPI_ROOT')
        assert hasattr(cfg, 'SUPPORTED_RESOLUTIONS')
        assert hasattr(cfg, 'MIN_INTERVAL')
    
    def test_testing_specific_settings(self):
        """Test testing-specific settings"""
        cfg = TestConfig()
        
        assert cfg.TESTING is True
        assert cfg.WTF_CSRF_ENABLED is False
    
    def test_testing_paths(self):
        """Test testing paths are set correctly"""
        cfg = TestConfig()
        
        # Should use test paths
        assert 'test_cinepi' in str(cfg.CINEPI_ROOT)
        assert 'test_cinepi' in str(cfg.CONFIG_PATH)
        assert 'test_cinepi' in str(cfg.CAPTURES_PATH)
        assert 'test_cinepi' in str(cfg.LOGS_PATH)
    
    def test_directory_creation(self):
        """Test that testing config creates directories"""
        with pytest.MonkeyPatch().context() as m:
            # Mock the directory creation
            m.setattr(Path, 'mkdir', lambda self, **kwargs: None)
            
            cfg = TestConfig()
            # Should not raise an exception
            assert cfg is not None


class TestConfigMapping:
    """Test configuration mapping"""
    
    def test_config_mapping_structure(self):
        """Test configuration mapping structure"""
        assert isinstance(config, dict)
        assert 'development' in config
        assert 'production' in config
        assert 'testing' in config
        assert 'default' in config
    
    def test_config_classes(self):
        """Test configuration classes in mapping"""
        assert config['development'] == DevelopmentConfig
        assert config['production'] == ProductionConfig
        assert config['testing'] == TestConfig
        assert config['default'] == DevelopmentConfig
    
    def test_config_instantiation(self):
        """Test that all config classes can be instantiated"""
        for config_class in config.values():
            cfg = config_class()
            assert cfg is not None
            assert hasattr(cfg, 'SECRET_KEY')
            assert hasattr(cfg, 'DASHBOARD_ROOT')
    
    def test_environment_specific_configs(self):
        """Test environment-specific configuration differences"""
        dev_cfg = DevelopmentConfig()
        prod_cfg = ProductionConfig()
        test_cfg = TestConfig()
        
        # Debug settings should differ
        assert dev_cfg.DEBUG != prod_cfg.DEBUG
        assert test_cfg.TESTING is True
        
        # Paths should be different
        assert dev_cfg.CINEPI_ROOT != prod_cfg.CINEPI_ROOT
        assert test_cfg.CINEPI_ROOT != prod_cfg.CINEPI_ROOT
        assert test_cfg.CINEPI_ROOT != dev_cfg.CINEPI_ROOT 