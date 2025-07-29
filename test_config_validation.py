#!/usr/bin/env python3
"""
Test script for Task 11: Configuration Validation
Tests the comprehensive configuration validation functionality.
"""

import os
import sys
import tempfile
import yaml
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config_manager import ConfigManager


def test_valid_configuration():
    """Test that a valid configuration passes validation."""
    print("Testing valid configuration...")
    
    config = ConfigManager()
    
    # Set valid configuration values
    config.set('camera.resolution', [4056, 3040])
    config.set('camera.quality', 95)
    config.set('camera.iso', 100)
    config.set('camera.shutter_speed', 0)
    config.set('camera.exposure_mode', 'auto')
    config.set('camera.awb_mode', 'auto')
    
    config.set('timelapse.interval_seconds', 30)
    config.set('timelapse.duration_hours', 24)
    config.set('timelapse.output_dir', 'output/images')
    config.set('timelapse.filename_prefix', 'timelapse')
    config.set('timelapse.image_format', 'jpg')
    config.set('timelapse.add_timestamp', True)
    config.set('timelapse.create_daily_dirs', True)
    
    config.set('logging.log_level', 'INFO')
    config.set('logging.log_dir', 'logs')
    config.set('logging.csv_filename', 'timelapse_metadata.csv')
    
    # Validate configuration
    assert config.validate_config() == True
    assert len(config.get_validation_errors()) == 0
    
    print("✓ Valid configuration passes validation")
    return True


def test_invalid_resolution():
    """Test invalid resolution values."""
    print("Testing invalid resolution values...")
    
    config = ConfigManager()
    
    # Test various invalid resolution values
    invalid_resolutions = [
        None,  # Missing
        "not_a_list",  # String instead of list
        [4056],  # Only one value
        [4056, 3040, 1000],  # Too many values
        [4056, "not_an_int"],  # Non-integer height
        [0, 3040],  # Zero width
        [-100, 3040],  # Negative width
        [50000, 3040],  # Too large width
    ]
    
    for resolution in invalid_resolutions:
        config.set('camera.resolution', resolution)
        assert config.validate_config() == False
        errors = config.get_validation_errors()
        assert any("camera.resolution" in error for error in errors)
    
    print("✓ Invalid resolution values properly rejected")
    return True


def test_invalid_iso_values():
    """Test invalid ISO values."""
    print("Testing invalid ISO values...")
    
    config = ConfigManager()
    
    # Test various invalid ISO values
    invalid_iso_values = [
        "not_an_int",  # String
        50,  # Too low
        150,  # Not in valid range
        6400,  # Too high
        -100,  # Negative
        0,  # Zero
    ]
    
    for iso in invalid_iso_values:
        config.set('camera.iso', iso)
        assert config.validate_config() == False
        errors = config.get_validation_errors()
        assert any("camera.iso" in error for error in errors)
    
    # Test valid ISO values
    valid_iso_values = [100, 200, 400, 800, 1600, 3200]
    for iso in valid_iso_values:
        config.set('camera.iso', iso)
        # Should pass validation (assuming other settings are valid)
        config.set('camera.resolution', [4056, 3040])
        config.set('timelapse.interval_seconds', 30)
        config.set('logging.log_level', 'INFO')
        assert config.validate_config() == True
    
    print("✓ Invalid ISO values properly rejected")
    return True


def test_invalid_interval_values():
    """Test invalid interval values."""
    print("Testing invalid interval values...")
    
    config = ConfigManager()
    config.set('camera.resolution', [4056, 3040])  # Set valid resolution
    
    # Test various invalid interval values
    invalid_intervals = [
        "not_an_int",  # String
        0,  # Zero
        -1,  # Negative
        -100,  # Large negative
        0.5,  # Float (should be int)
    ]
    
    for interval in invalid_intervals:
        config.set('timelapse.interval_seconds', interval)
        assert config.validate_config() == False
        errors = config.get_validation_errors()
        assert any("timelapse.interval_seconds" in error for error in errors)
    
    # Test valid interval values
    valid_intervals = [1, 30, 60, 300, 3600]
    for interval in valid_intervals:
        config.set('timelapse.interval_seconds', interval)
        assert config.validate_config() == True
    
    print("✓ Invalid interval values properly rejected")
    return True


def test_invalid_exposure_modes():
    """Test invalid exposure mode values."""
    print("Testing invalid exposure mode values...")
    
    config = ConfigManager()
    config.set('camera.resolution', [4056, 3040])
    config.set('timelapse.interval_seconds', 30)
    
    # Test various invalid exposure modes
    invalid_modes = [
        "invalid_mode",  # Non-existent mode
        "AUTO",  # Wrong case
        "auto ",  # Extra space
        "",  # Empty string
        123,  # Number
        True,  # Boolean
    ]
    
    for mode in invalid_modes:
        config.set('camera.exposure_mode', mode)
        assert config.validate_config() == False
        errors = config.get_validation_errors()
        assert any("camera.exposure_mode" in error for error in errors)
    
    # Test valid exposure modes
    valid_modes = ['auto', 'night', 'backlight', 'spotlight', 'sports', 'snow', 'beach', 'verylong', 'fixedfps', 'antishake', 'fireworks']
    for mode in valid_modes:
        config.set('camera.exposure_mode', mode)
        assert config.validate_config() == True
    
    print("✓ Invalid exposure mode values properly rejected")
    return True


def test_invalid_log_levels():
    """Test invalid log level values."""
    print("Testing invalid log level values...")
    
    # Test various invalid log levels
    invalid_levels = [
        "invalid_level",  # Non-existent level
        "INFO ",  # Extra space
        "",  # Empty string
        123,  # Number
        True,  # Boolean
    ]
    
    for level in invalid_levels:
        config = ConfigManager()
        config.set('camera.resolution', [4056, 3040])
        config.set('timelapse.interval_seconds', 30)
        config.set('logging.log_level', level)
        assert config.validate_config() == False
        errors = config.get_validation_errors()
        assert any("logging.log_level" in error for error in errors)
    
    # Test valid log levels (case insensitive)
    valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
    case_variations = ['debug', 'info', 'warning', 'error', 'critical']
    
    for level in valid_levels:
        config = ConfigManager()
        config.set('camera.resolution', [4056, 3040])
        config.set('timelapse.interval_seconds', 30)
        config.set('logging.log_level', level)
        result = config.validate_config()
        if not result:
            errors = config.get_validation_errors()
            print(f"  Debug: Log level '{level}' failed validation with errors: {errors}")
        assert result == True
    
    # Test case insensitive variations
    for level in case_variations:
        config = ConfigManager()
        config.set('camera.resolution', [4056, 3040])
        config.set('timelapse.interval_seconds', 30)
        config.set('logging.log_level', level)
        result = config.validate_config()
        if not result:
            errors = config.get_validation_errors()
            print(f"  Debug: Log level '{level}' failed validation with errors: {errors}")
        assert result == True
    
    print("✓ Invalid log level values properly rejected")
    return True


def test_invalid_string_values():
    """Test invalid string values for required string fields."""
    print("Testing invalid string values...")
    
    config = ConfigManager()
    config.set('camera.resolution', [4056, 3040])
    config.set('timelapse.interval_seconds', 30)
    config.set('logging.log_level', 'INFO')
    
    # Test invalid string values
    invalid_strings = [
        "",  # Empty string
        "   ",  # Whitespace only
        123,  # Number
        True,  # Boolean
        None,  # None
    ]
    
    string_fields = [
        'timelapse.output_dir',
        'timelapse.filename_prefix',
        'logging.log_dir',
        'logging.csv_filename'
    ]
    
    for field in string_fields:
        for invalid_value in invalid_strings:
            config.set(field, invalid_value)
            assert config.validate_config() == False
            errors = config.get_validation_errors()
            assert any(field.replace('.', '.') in error for error in errors)
    
    print("✓ Invalid string values properly rejected")
    return True


def test_invalid_boolean_values():
    """Test invalid boolean values."""
    print("Testing invalid boolean values...")
    
    # Test invalid boolean values
    invalid_booleans = [
        "true",  # String
        "false",  # String
        1,  # Number
        0,  # Number
        "yes",  # String
        "no",  # String
        None,  # None
    ]
    
    boolean_fields = [
        'timelapse.add_timestamp',
        'timelapse.create_daily_dirs'
    ]
    
    for field in boolean_fields:
        for invalid_value in invalid_booleans:
            config = ConfigManager()
            config.set('camera.resolution', [4056, 3040])
            config.set('timelapse.interval_seconds', 30)
            config.set('logging.log_level', 'INFO')
            config.set(field, invalid_value)
            assert config.validate_config() == False
            errors = config.get_validation_errors()
            assert any(field.replace('.', '.') in error for error in errors)
    
    # Test valid boolean values
    for field in boolean_fields:
        for valid_value in [True, False]:
            config = ConfigManager()
            config.set('camera.resolution', [4056, 3040])
            config.set('timelapse.interval_seconds', 30)
            config.set('logging.log_level', 'INFO')
            config.set(field, valid_value)
            assert config.validate_config() == True
    
    print("✓ Invalid boolean values properly rejected")
    return True


def test_validation_error_messages():
    """Test that validation provides helpful error messages."""
    print("Testing validation error messages...")
    
    config = ConfigManager()
    
    # Create an invalid configuration
    config.set('camera.resolution', "invalid")
    config.set('camera.iso', 150)
    config.set('timelapse.interval_seconds', 0)
    config.set('logging.log_level', "invalid_level")
    
    # Get validation errors
    errors = config.get_validation_errors()
    
    # Check that we have the expected number of errors
    assert len(errors) >= 4
    
    # Check that error messages are helpful
    error_text = " ".join(errors).lower()
    assert "resolution" in error_text
    assert "iso" in error_text
    assert "interval_seconds" in error_text
    assert "log_level" in error_text
    
    print("✓ Validation provides helpful error messages")
    return True


def test_validation_report():
    """Test the validation report functionality."""
    print("Testing validation report...")
    
    config = ConfigManager()
    
    # Create an invalid configuration
    config.set('camera.resolution', "invalid")
    config.set('camera.iso', 150)
    
    # Test that print_validation_report doesn't crash
    try:
        config.print_validation_report()
        print("✓ Validation report generated successfully")
    except Exception as e:
        print(f"✗ Validation report failed: {e}")
        return False
    
    return True


def test_config_file_validation():
    """Test validation with actual config files."""
    print("Testing config file validation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Test valid config file
        valid_config = {
            'camera': {
                'resolution': [4056, 3040],
                'quality': 95,
                'iso': 100,
                'exposure_mode': 'auto',
                'awb_mode': 'auto'
            },
            'timelapse': {
                'interval_seconds': 30,
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
        
        valid_config_file = temp_path / 'valid_config.yaml'
        with open(valid_config_file, 'w') as f:
            yaml.dump(valid_config, f)
        
        config = ConfigManager(str(valid_config_file))
        assert config.validate_config() == True
        
        # Test invalid config file
        invalid_config = {
            'camera': {
                'resolution': "invalid",
                'iso': 150
            },
            'timelapse': {
                'interval_seconds': 0
            }
        }
        
        invalid_config_file = temp_path / 'invalid_config.yaml'
        with open(invalid_config_file, 'w') as f:
            yaml.dump(invalid_config, f)
        
        config = ConfigManager(str(invalid_config_file))
        assert config.validate_config() == False
        errors = config.get_validation_errors()
        assert len(errors) >= 3
    
    print("✓ Config file validation working correctly")
    return True


def test_edge_cases():
    """Test edge cases and boundary conditions."""
    print("Testing edge cases...")
    
    config = ConfigManager()
    
    # Test boundary conditions
    config.set('camera.resolution', [4056, 3040])
    config.set('timelapse.interval_seconds', 30)
    config.set('logging.log_level', 'INFO')
    
    # Test minimum valid values
    config.set('camera.quality', 1)
    config.set('timelapse.interval_seconds', 1)
    config.set('timelapse.duration_hours', 0)  # Indefinite
    assert config.validate_config() == True
    
    # Test maximum valid values
    config.set('camera.quality', 100)
    config.set('timelapse.interval_seconds', 86400)  # 24 hours
    config.set('timelapse.duration_hours', 8760)  # 1 year
    assert config.validate_config() == True
    
    # Test boundary violations
    config.set('camera.quality', 0)  # Too low
    assert config.validate_config() == False
    
    config.set('camera.quality', 101)  # Too high
    assert config.validate_config() == False
    
    config.set('timelapse.interval_seconds', 0)  # Too low
    assert config.validate_config() == False
    
    print("✓ Edge cases handled correctly")
    return True


def main():
    """Run all configuration validation tests."""
    print("=== Task 11: Configuration Validation Tests ===\n")
    
    tests = [
        ("Valid Configuration", test_valid_configuration),
        ("Invalid Resolution", test_invalid_resolution),
        ("Invalid ISO Values", test_invalid_iso_values),
        ("Invalid Interval Values", test_invalid_interval_values),
        ("Invalid Exposure Modes", test_invalid_exposure_modes),
        ("Invalid Log Levels", test_invalid_log_levels),
        ("Invalid String Values", test_invalid_string_values),
        ("Invalid Boolean Values", test_invalid_boolean_values),
        ("Validation Error Messages", test_validation_error_messages),
        ("Validation Report", test_validation_report),
        ("Config File Validation", test_config_file_validation),
        ("Edge Cases", test_edge_cases),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            print(f"✗ {test_name} FAILED with exception: {e}")
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 All configuration validation tests passed!")
        print("✅ Task 11 requirements are complete:")
        print("   - Comprehensive validate_config() function implemented")
        print("   - Type checking for all configuration parameters")
        print("   - Range validation for numeric values")
        print("   - Enum validation for string values")
        print("   - Helpful error messages for invalid configurations")
        print("   - Resolution validation (positive integers)")
        print("   - ISO validation (100-3200 range)")
        print("   - Interval validation (>= 1)")
        print("   - Exposure mode and AWB mode validation")
        print("   - Log level validation")
        print("   - String and boolean validation")
        print("   - Boundary condition testing")
        print("   - Config file validation")
        return 0
    else:
        print("⚠️  Some configuration validation tests failed.")
        print("   Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 