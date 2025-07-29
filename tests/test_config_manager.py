"""Tests for the ConfigManager class."""

import pytest
import tempfile
import os
from pathlib import Path
import yaml

from src.config_manager import ConfigManager, ConfigValidationError


class TestConfigManager:
    """Test cases for ConfigManager."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_path = Path(self.temp_dir) / "test_config.yaml"
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            import shutil
            shutil.rmtree(self.temp_dir)
    
    def test_init_with_nonexistent_config(self):
        """Test initialization with non-existent config file."""
        config_path = Path(self.temp_dir) / "nonexistent.yaml"
        manager = ConfigManager(str(config_path))
        assert manager.config != {}
        assert config_path.exists()
    
    def test_init_with_existing_config(self):
        """Test initialization with existing config file."""
        config_path = Path(self.temp_dir) / "test_config.yaml"
        test_config = {
            'camera': {'resolution': [1920, 1080]},
            'timelapse': {'interval_seconds': 60}
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        manager = ConfigManager(str(config_path))
        assert manager.config == test_config
    
    def test_init_with_empty_config_file(self):
        """Test initialization with empty config file."""
        config_path = Path(self.temp_dir) / "empty_config.yaml"
        with open(config_path, 'w') as f:
            f.write("")
        
        manager = ConfigManager(str(config_path))
        assert manager.config == {}
    
    def test_init_with_invalid_yaml(self):
        """Test initialization with invalid YAML file."""
        config_path = Path(self.temp_dir) / "invalid_config.yaml"
        with open(config_path, 'w') as f:
            f.write("invalid: yaml: content: [")
        
        # Should handle invalid YAML gracefully
        manager = ConfigManager(str(config_path))
        assert manager.config == {}
    
    def test_get_with_dot_notation(self):
        """Test getting values with dot notation."""
        config_path = Path(self.temp_dir) / "test_config.yaml"
        test_config = {
            'camera': {'resolution': [1920, 1080]},
            'timelapse': {'interval_seconds': 60}
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        manager = ConfigManager(str(config_path))
        assert manager.get('camera.resolution') == [1920, 1080]
        assert manager.get('timelapse.interval_seconds') == 60
        assert manager.get('nonexistent.key') is None
        assert manager.get('nonexistent.key', 'default') == 'default'
    
    def test_get_nested_dot_notation(self):
        """Test getting deeply nested values with dot notation."""
        config_path = Path(self.temp_dir) / "test_config.yaml"
        test_config = {
            'camera': {
                'settings': {
                    'advanced': {
                        'feature': 'enabled'
                    }
                }
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        manager = ConfigManager(str(config_path))
        assert manager.get('camera.settings.advanced.feature') == 'enabled'
        assert manager.get('camera.settings.advanced.nonexistent', 'default') == 'default'
    
    def test_set_with_dot_notation(self):
        """Test setting values with dot notation."""
        config_path = Path(self.temp_dir) / "test_config.yaml"
        manager = ConfigManager(str(config_path))
        
        # Set new values
        assert manager.set('camera.resolution', [1920, 1080]) is True
        assert manager.set('timelapse.interval_seconds', 60) is True
        
        # Verify values were set
        assert manager.get('camera.resolution') == [1920, 1080]
        assert manager.get('timelapse.interval_seconds') == 60
    
    def test_set_nested_dot_notation(self):
        """Test setting deeply nested values with dot notation."""
        config_path = Path(self.temp_dir) / "test_config.yaml"
        manager = ConfigManager(str(config_path))
        
        # Set nested value
        assert manager.set('camera.settings.advanced.feature', 'enabled') is True
        
        # Verify nested structure was created
        assert manager.get('camera.settings.advanced.feature') == 'enabled'
    
    def test_validate_config_valid(self):
        """Test configuration validation with valid config."""
        config_path = Path(self.temp_dir) / "test_config.yaml"
        test_config = {
            'camera': {
                'resolution': [1920, 1080],
                'quality': 95,
                'iso': 100,
                'shutter_speed': 0,
                'exposure_mode': 'auto',
                'awb_mode': 'auto'
            },
            'timelapse': {
                'interval_seconds': 60,
                'duration_hours': 24,
                'output_dir': 'output/images',
                'filename_prefix': 'timelapse',
                'image_format': 'jpg',
                'add_timestamp': True,
                'create_daily_dirs': True
            },
            'logging': {
                'log_level': 'INFO',
                'log_dir': 'logs',
                'csv_filename': 'timelapse_metadata.csv'
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        manager = ConfigManager(str(config_path))
        assert manager.validate_config() is True
    
    def test_validate_config_missing_required(self):
        """Test validation with missing required fields."""
        config_path = Path(self.temp_dir) / "test_config.yaml"
        test_config = {
            'camera': {},  # Missing resolution
            'timelapse': {}  # Missing interval_seconds
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        manager = ConfigManager(str(config_path))
        assert manager.validate_config() is False
    
    def test_validate_config_invalid_resolution(self):
        """Test validation with invalid resolution."""
        config_path = Path(self.temp_dir) / "test_config.yaml"
        test_config = {
            'camera': {
                'resolution': [1920],  # Missing height
                'iso': 100
            },
            'timelapse': {
                'interval_seconds': 60
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        manager = ConfigManager(str(config_path))
        assert manager.validate_config() is False
    
    def test_validate_config_invalid_iso(self):
        """Test validation with invalid ISO value."""
        config_path = Path(self.temp_dir) / "test_config.yaml"
        test_config = {
            'camera': {
                'resolution': [1920, 1080],
                'iso': 150  # Invalid ISO value
            },
            'timelapse': {
                'interval_seconds': 60
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        manager = ConfigManager(str(config_path))
        assert manager.validate_config() is False
    
    def test_validate_config_invalid_interval(self):
        """Test validation with invalid interval."""
        config_path = Path(self.temp_dir) / "test_config.yaml"
        test_config = {
            'camera': {
                'resolution': [1920, 1080]
            },
            'timelapse': {
                'interval_seconds': 0  # Invalid interval
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        manager = ConfigManager(str(config_path))
        assert manager.validate_config() is False
    
    def test_validate_config_invalid_exposure_mode(self):
        """Test validation with invalid exposure mode."""
        config_path = Path(self.temp_dir) / "test_config.yaml"
        test_config = {
            'camera': {
                'resolution': [1920, 1080],
                'exposure_mode': 'invalid_mode'
            },
            'timelapse': {
                'interval_seconds': 60
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        manager = ConfigManager(str(config_path))
        assert manager.validate_config() is False
    
    def test_validate_config_invalid_awb_mode(self):
        """Test validation with invalid AWB mode."""
        config_path = Path(self.temp_dir) / "test_config.yaml"
        test_config = {
            'camera': {
                'resolution': [1920, 1080],
                'awb_mode': 'invalid_awb'
            },
            'timelapse': {
                'interval_seconds': 60
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        manager = ConfigManager(str(config_path))
        assert manager.validate_config() is False
    
    def test_validate_config_invalid_image_format(self):
        """Test validation with invalid image format."""
        config_path = Path(self.temp_dir) / "test_config.yaml"
        test_config = {
            'camera': {
                'resolution': [1920, 1080]
            },
            'timelapse': {
                'interval_seconds': 60,
                'image_format': 'invalid_format'
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        manager = ConfigManager(str(config_path))
        assert manager.validate_config() is False
    
    def test_validate_config_invalid_log_level(self):
        """Test validation with invalid log level."""
        config_path = Path(self.temp_dir) / "test_config.yaml"
        test_config = {
            'camera': {
                'resolution': [1920, 1080]
            },
            'timelapse': {
                'interval_seconds': 60
            },
            'logging': {
                'log_level': 'INVALID_LEVEL'
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        manager = ConfigManager(str(config_path))
        assert manager.validate_config() is False
    
    def test_validate_resolution_valid(self):
        """Test resolution validation with valid values."""
        config_path = Path(self.temp_dir) / "test_config.yaml"
        manager = ConfigManager(str(config_path))
        
        assert manager._validate_resolution([1920, 1080]) is True
        assert manager._validate_resolution([4056, 3040]) is True
        assert manager._validate_resolution([640, 480]) is True
    
    def test_validate_resolution_invalid(self):
        """Test resolution validation with invalid values."""
        config_path = Path(self.temp_dir) / "test_config.yaml"
        manager = ConfigManager(str(config_path))
        
        # Invalid types
        assert manager._validate_resolution("1920x1080") is False
        assert manager._validate_resolution(1920) is False
        assert manager._validate_resolution([1920]) is False
        assert manager._validate_resolution([1920, 1080, 60]) is False
        
        # Invalid values
        assert manager._validate_resolution([0, 1080]) is False
        assert manager._validate_resolution([1920, 0]) is False
        assert manager._validate_resolution([-1920, 1080]) is False
        assert manager._validate_resolution([1920, -1080]) is False
        
        # Too large values
        assert manager._validate_resolution([20000, 1080]) is False
        assert manager._validate_resolution([1920, 20000]) is False
    
    def test_get_validation_errors(self):
        """Test getting validation errors."""
        config_path = Path(self.temp_dir) / "test_config.yaml"
        test_config = {
            'camera': {
                'resolution': [1920],  # Invalid
                'iso': 150  # Invalid
            },
            'timelapse': {
                'interval_seconds': 0  # Invalid
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        manager = ConfigManager(str(config_path))
        errors = manager.get_validation_errors()
        
        assert len(errors) > 0
        assert any("resolution" in error for error in errors)
        assert any("iso" in error for error in errors)
        assert any("interval_seconds" in error for error in errors)
    
    def test_print_validation_report_valid(self, capsys):
        """Test printing validation report with valid config."""
        config_path = Path(self.temp_dir) / "test_config.yaml"
        test_config = {
            'camera': {
                'resolution': [1920, 1080],
                'iso': 100
            },
            'timelapse': {
                'interval_seconds': 60
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        manager = ConfigManager(str(config_path))
        manager.print_validation_report()
        
        captured = capsys.readouterr()
        assert "✅ Configuration validation passed successfully!" in captured.out
    
    def test_print_validation_report_invalid(self, capsys):
        """Test printing validation report with invalid config."""
        config_path = Path(self.temp_dir) / "test_config.yaml"
        test_config = {
            'camera': {
                'resolution': [1920],  # Invalid
                'iso': 150  # Invalid
            },
            'timelapse': {
                'interval_seconds': 0  # Invalid
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(test_config, f)
        
        manager = ConfigManager(str(config_path))
        manager.print_validation_report()
        
        captured = capsys.readouterr()
        assert "❌ Configuration validation failed" in captured.out
        assert "Please fix these errors" in captured.out
    
    def test_save_config_success(self):
        """Test successful configuration saving."""
        config_path = Path(self.temp_dir) / "test_config.yaml"
        manager = ConfigManager(str(config_path))
        
        # Set some values
        manager.set('camera.resolution', [1920, 1080])
        manager.set('timelapse.interval_seconds', 60)
        
        # Save configuration
        assert manager.save_config() is True
        
        # Verify file was written
        assert config_path.exists()
        
        # Verify content
        with open(config_path, 'r') as f:
            saved_config = yaml.safe_load(f)
        
        assert saved_config['camera']['resolution'] == [1920, 1080]
        assert saved_config['timelapse']['interval_seconds'] == 60
    
    def test_save_config_permission_error(self):
        """Test configuration saving with permission error."""
        # On Windows, we need to use a different approach to test permission failures
        # Try to write to a system directory that requires admin privileges
        import platform
        
        if platform.system() == "Windows":
            # Use a system directory that should be protected
            config_path = Path("C:/Windows/System32/test_config.yaml")
            manager = ConfigManager(str(config_path))
            
            # Try to save configuration - should fail due to permission error
            assert manager.save_config() is False
        else:
            # Unix-style permission test
            readonly_dir = Path(self.temp_dir) / "readonly"
            readonly_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(readonly_dir, 0o444)  # Read-only
            
            config_path = readonly_dir / "test_config.yaml"
            manager = ConfigManager(str(config_path))
            
            # Try to save configuration
            assert manager.save_config() is False
            
            # Restore permissions for cleanup
            os.chmod(readonly_dir, 0o755)
    
    def test_load_config_file_not_found(self):
        """Test loading configuration when file doesn't exist."""
        config_path = Path(self.temp_dir) / "nonexistent.yaml"
        manager = ConfigManager(str(config_path))
        
        # Should create default config
        assert manager.load_config() is True
        assert config_path.exists()
    
    def test_load_config_permission_error(self):
        """Test loading configuration with permission error."""
        import platform
        
        if platform.system() == "Windows":
            # On Windows, try to read from a system file that should be protected
            config_path = Path("C:/Windows/System32/drivers/etc/hosts")
            manager = ConfigManager(str(config_path))
            
            # Try to load configuration - should fail due to permission error
            assert manager.load_config() is False
        else:
            # Unix-style permission test
            # Create file but make it unreadable
            config_path = Path(self.temp_dir) / "test_config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump({'test': 'data'}, f)
            
            os.chmod(config_path, 0o000)  # No permissions
            
            manager = ConfigManager(str(config_path))
            assert manager.load_config() is False
            
            # Restore permissions for cleanup
            os.chmod(config_path, 0o644)
    
    def test_create_default_config_success(self):
        """Test successful default configuration creation."""
        config_path = Path(self.temp_dir) / "default_config.yaml"
        manager = ConfigManager(str(config_path))
        
        assert manager.create_default_config() is True
        assert config_path.exists()
        
        # Verify default content
        with open(config_path, 'r') as f:
            default_config = yaml.safe_load(f)
        
        assert 'camera' in default_config
        assert 'timelapse' in default_config
        assert 'logging' in default_config
        assert default_config['camera']['resolution'] == [4056, 3040]
        assert default_config['timelapse']['interval_seconds'] == 30
    
    def test_create_default_config_permission_error(self):
        """Test default configuration creation with permission error."""
        import platform
        
        if platform.system() == "Windows":
            # On Windows, try to create in a system directory that should be protected
            config_path = Path("C:/Windows/System32/default_config.yaml")
            manager = ConfigManager(str(config_path))
            
            # Try to create default configuration - should fail due to permission error
            assert manager.create_default_config() is False
        else:
            # Unix-style permission test
            # Create read-only directory
            readonly_dir = Path(self.temp_dir) / "readonly"
            readonly_dir.mkdir(parents=True, exist_ok=True)
            os.chmod(readonly_dir, 0o444)  # Read-only
            
            config_path = readonly_dir / "default_config.yaml"
            manager = ConfigManager(str(config_path))
            
            assert manager.create_default_config() is False
            
            # Restore permissions for cleanup
            os.chmod(readonly_dir, 0o755)


if __name__ == "__main__":
    pytest.main([__file__])
