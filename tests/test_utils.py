"""
Unit tests for dashboard utility functions
"""

import pytest
from dashboard.utils.validators import (
    validate_interval,
    validate_camera_settings,
    validate_config_structure,
    validate_filename
)


class TestValidateInterval:
    """Test interval validation function"""
    
    def test_valid_intervals(self):
        """Test valid interval values"""
        valid_intervals = [5, 30, 60, 300, 1800, 3600]
        for interval in valid_intervals:
            assert validate_interval(interval) is True
    
    def test_invalid_intervals(self):
        """Test invalid interval values"""
        invalid_intervals = [0, 1, 4, 3601, 7200, -1, -30]
        for interval in invalid_intervals:
            assert validate_interval(interval) is False
    
    def test_string_intervals(self):
        """Test string interval values"""
        assert validate_interval("30") is True
        assert validate_interval("5") is True
        assert validate_interval("3600") is True
        assert validate_interval("invalid") is False
        assert validate_interval("0") is False
    
    def test_none_and_empty(self):
        """Test None and empty values"""
        assert validate_interval(None) is False
        assert validate_interval("") is False
        assert validate_interval([]) is False


class TestValidateCameraSettings:
    """Test camera settings validation function"""
    
    def test_valid_settings(self):
        """Test valid camera settings"""
        config = {
            'SUPPORTED_RESOLUTIONS': ['4056x3040', '2028x1520', '1014x760']
        }
        
        valid_settings = [
            {'exposure_mode': 'auto'},
            {'iso': 400},
            {'resolution': '4056x3040'},
            {'gain': 2.0},
            {
                'exposure_mode': 'auto',
                'iso': 400,
                'resolution': '4056x3040',
                'gain': 2.0
            }
        ]
        
        for settings in valid_settings:
            result = validate_camera_settings(settings, config)
            assert result['valid'] is True
    
    def test_invalid_exposure_mode(self):
        """Test invalid exposure mode"""
        config = {'SUPPORTED_RESOLUTIONS': ['4056x3040']}
        settings = {'exposure_mode': 'invalid'}
        
        result = validate_camera_settings(settings, config)
        assert result['valid'] is False
        assert 'Exposure mode must be "auto" or "manual"' in result['error']
    
    def test_invalid_iso(self):
        """Test invalid ISO values"""
        config = {'SUPPORTED_RESOLUTIONS': ['4056x3040']}
        
        invalid_iso_settings = [
            {'iso': 50},   # Too low
            {'iso': 1000}, # Too high
            {'iso': 'invalid'}, # Not a number
            {'iso': None}  # None value
        ]
        
        for settings in invalid_iso_settings:
            result = validate_camera_settings(settings, config)
            assert result['valid'] is False
            assert 'ISO' in result['error']
    
    def test_invalid_resolution(self):
        """Test invalid resolution values"""
        config = {'SUPPORTED_RESOLUTIONS': ['4056x3040', '2028x1520']}
        settings = {'resolution': 'invalid_resolution'}
        
        result = validate_camera_settings(settings, config)
        assert result['valid'] is False
        assert 'Resolution must be one of' in result['error']
    
    def test_invalid_gain(self):
        """Test invalid gain values"""
        config = {'SUPPORTED_RESOLUTIONS': ['4056x3040']}
        
        invalid_gain_settings = [
            {'gain': 0.5},   # Too low
            {'gain': 10.0},  # Too high
            {'gain': 'invalid'}, # Not a number
            {'gain': None}   # None value
        ]
        
        for settings in invalid_gain_settings:
            result = validate_camera_settings(settings, config)
            assert result['valid'] is False
            assert 'Gain' in result['error']
    
    def test_non_dict_settings(self):
        """Test non-dictionary settings"""
        config = {'SUPPORTED_RESOLUTIONS': ['4056x3040']}
        
        invalid_settings = [None, "string", 123, [], True]
        
        for settings in invalid_settings:
            result = validate_camera_settings(settings, config)
            assert result['valid'] is False
            assert 'Settings must be a dictionary' in result['error']
    
    def test_empty_settings(self):
        """Test empty settings dictionary"""
        config = {'SUPPORTED_RESOLUTIONS': ['4056x3040']}
        settings = {}
        
        result = validate_camera_settings(settings, config)
        assert result['valid'] is True


class TestValidateConfigStructure:
    """Test configuration structure validation function"""
    
    def test_valid_config(self):
        """Test valid configuration structure"""
        valid_config = {
            'camera': {'exposure': 'auto', 'iso': 400},
            'capture': {'interval': 30},
            'storage': {'path': '/opt/cinepi/captures'}
        }
        
        result = validate_config_structure(valid_config)
        assert result['valid'] is True
    
    def test_missing_sections(self):
        """Test configuration with missing required sections"""
        incomplete_configs = [
            {},  # Empty config
            {'camera': {}},  # Missing capture and storage
            {'camera': {}, 'capture': {}},  # Missing storage
            {'capture': {}, 'storage': {}}  # Missing camera
        ]
        
        for config in incomplete_configs:
            result = validate_config_structure(config)
            assert result['valid'] is False
            assert 'Missing required section' in result['error']
    
    def test_non_dict_config(self):
        """Test non-dictionary configuration"""
        invalid_configs = [None, "string", 123, [], True]
        
        for config in invalid_configs:
            result = validate_config_structure(config)
            assert result['valid'] is False
            assert 'Configuration must be a dictionary' in result['error']


class TestValidateFilename:
    """Test filename validation function"""
    
    def test_valid_filenames(self):
        """Test valid filenames"""
        valid_filenames = [
            'capture_001.jpg',
            'image.jpeg',
            'photo.png',
            'config.yaml',
            'settings.yml',
            'test_file.JPG',
            'UPPERCASE.PNG'
        ]
        
        for filename in valid_filenames:
            assert validate_filename(filename) is True
    
    def test_invalid_filenames(self):
        """Test invalid filenames"""
        invalid_filenames = [
            '',  # Empty string
            None,  # None value
            'file.txt',  # Wrong extension
            'image.gif',  # Wrong extension
            'config.xml',  # Wrong extension
            '../capture.jpg',  # Path traversal
            'capture/../image.jpg',  # Path traversal
            '/absolute/path.jpg',  # Absolute path
            'C:\\Windows\\file.jpg',  # Windows path
        ]

        for filename in invalid_filenames:
            if filename is not None:  # Skip None for path traversal check
                assert validate_filename(filename) is False
    
    def test_path_traversal_attempts(self):
        """Test path traversal attempts"""
        traversal_attempts = [
            '../capture.jpg',
            '..\\capture.jpg',
            'capture/../image.jpg',
            'capture\\..\\image.jpg',
            '....//capture.jpg',
            '....\\\\capture.jpg'
        ]
        
        for filename in traversal_attempts:
            assert validate_filename(filename) is False
    
    def test_allowed_extensions(self):
        """Test all allowed extensions"""
        allowed_extensions = ['.jpg', '.jpeg', '.png', '.yaml', '.yml']
        
        for ext in allowed_extensions:
            filename = f'test{ext}'
            assert validate_filename(filename) is True
    
    def test_case_insensitive_extensions(self):
        """Test case insensitive extensions"""
        case_variations = [
            'test.JPG',
            'test.JPEG',
            'test.PNG',
            'test.YAML',
            'test.YML',
            'test.Jpg',
            'test.Png'
        ]
        
        for filename in case_variations:
            assert validate_filename(filename) is True 