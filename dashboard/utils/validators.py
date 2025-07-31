"""
CinePi Dashboard Input Validation

This module contains validation functions for user input and configuration data.
"""


def validate_interval(interval):
    """
    Validate capture interval
    
    Args:
        interval: Interval value to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        interval = int(interval)
        return 5 <= interval <= 3600  # 5 seconds to 1 hour
    except (ValueError, TypeError):
        return False


def validate_camera_settings(settings, config):
    """
    Validate camera settings
    
    Args:
        settings (dict): Camera settings to validate
        config (dict): Application configuration
    
    Returns:
        dict: Validation result with 'valid' boolean and optional 'error' message
    """
    if not isinstance(settings, dict):
        return {
            'valid': False,
            'error': 'Settings must be a dictionary'
        }
    
    # Validate exposure
    if 'exposure_mode' in settings:
        if settings['exposure_mode'] not in ['auto', 'manual']:
            return {
                'valid': False,
                'error': 'Exposure mode must be "auto" or "manual"'
            }
    
    # Validate ISO
    if 'iso' in settings:
        try:
            iso = int(settings['iso'])
            if not (100 <= iso <= 800):
                return {
                    'valid': False,
                    'error': 'ISO must be between 100 and 800'
                }
        except (ValueError, TypeError):
            return {
                'valid': False,
                'error': 'ISO must be a valid integer'
            }
    
    # Validate resolution
    if 'resolution' in settings:
        supported_resolutions = config.get('SUPPORTED_RESOLUTIONS', [])
        if settings['resolution'] not in supported_resolutions:
            return {
                'valid': False,
                'error': f'Resolution must be one of: {", ".join(supported_resolutions)}'
            }
    
    # Validate gain
    if 'gain' in settings:
        try:
            gain = float(settings['gain'])
            if not (1.0 <= gain <= 8.0):
                return {
                    'valid': False,
                    'error': 'Gain must be between 1.0 and 8.0'
                }
        except (ValueError, TypeError):
            return {
                'valid': False,
                'error': 'Gain must be a valid number'
            }
    
    return {'valid': True}


def validate_config_structure(config):
    """
    Validate configuration structure
    
    Args:
        config (dict): Configuration to validate
    
    Returns:
        dict: Validation result
    """
    if not isinstance(config, dict):
        return {
            'valid': False,
            'error': 'Configuration must be a dictionary'
        }
    
    # Check for required sections
    required_sections = ['camera', 'capture', 'storage']
    for section in required_sections:
        if section not in config:
            return {
                'valid': False,
                'error': f'Missing required section: {section}'
            }
    
    return {'valid': True}


def validate_filename(filename):
    """
    Validate filename for security
    
    Args:
        filename (str): Filename to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    if not filename:
        return False
    
    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # Check for allowed extensions
    allowed_extensions = {'.jpg', '.jpeg', '.png', '.yaml', '.yml'}
    if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
        return False
    
    return True 
