"""
CinePi Dashboard Configuration Service

This service handles YAML configuration management and backup/restore operations.
"""

import yaml
from pathlib import Path
from datetime import datetime


class ConfigService:
    """Service for configuration management"""
    
    def __init__(self):
        self.config_path = Path('/opt/cinepi/config/cinepi.yaml')
        self.backup_path = Path('/opt/cinepi/config/backups')
        self.backup_path.mkdir(parents=True, exist_ok=True)
    
    def get_config(self):
        """
        Load configuration from file
        
        Returns:
            dict: Configuration data
        """
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r') as f:
                    return yaml.safe_load(f)
            else:
                return {
                    'camera': {
                        'exposure': 'auto',
                        'iso': 400,
                        'resolution': '4056x3040',
                        'gain': 2.0
                    },
                    'capture': {
                        'interval': 30,
                        'format': 'jpg',
                        'quality': 95
                    },
                    'storage': {
                        'path': '/opt/cinepi/captures',
                        'max_files': 10000
                    }
                }
        except Exception as e:
            return {'error': str(e)}
    
    def update_config(self, new_config):
        """
        Update configuration file
        
        Args:
            new_config (dict): New configuration data
        
        Returns:
            dict: Operation result
        """
        try:
            # Validate configuration structure
            if not isinstance(new_config, dict):
                return {
                    'success': False,
                    'error': 'Configuration must be a dictionary'
                }
            
            # Create backup
            backup_result = self._create_backup()
            if not backup_result['success']:
                return backup_result
            
            # Save new configuration
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w') as f:
                yaml.dump(new_config, f, default_flow_style=False)
            
            return {
                'success': True,
                'message': 'Configuration updated successfully',
                'backup_file': backup_result.get('backup_file')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_backup(self):
        """
        Create configuration backup
        
        Returns:
            dict: Backup operation result
        """
        return self._create_backup()
    
    def validate_yaml_content(self, yaml_content):
        """
        Validate YAML content for syntax and structure
        
        Args:
            yaml_content (str): YAML content to validate
        
        Returns:
            dict: Validation result
        """
        try:
            # Parse YAML
            config_data = yaml.safe_load(yaml_content)
            
            if config_data is None:
                return {
                    'valid': False,
                    'error': 'YAML content is empty or invalid'
                }
            
            if not isinstance(config_data, dict):
                return {
                    'valid': False,
                    'error': 'Configuration must be a valid YAML object'
                }
            
            # Basic structure validation
            validation_errors = []
            
            # Check for required sections
            required_sections = ['camera', 'capture', 'storage']
            for section in required_sections:
                if section not in config_data:
                    validation_errors.append(f"Missing required section: {section}")
            
            # Check camera settings
            if 'camera' in config_data:
                camera = config_data['camera']
                if not isinstance(camera, dict):
                    validation_errors.append("Camera section must be an object")
                else:
                    required_camera_settings = ['exposure', 'iso', 'resolution']
                    for setting in required_camera_settings:
                        if setting not in camera:
                            validation_errors.append(f"Camera section missing '{setting}' setting")
            
            # Check capture settings
            if 'capture' in config_data:
                capture = config_data['capture']
                if not isinstance(capture, dict):
                    validation_errors.append("Capture section must be an object")
                else:
                    if 'interval' not in capture:
                        validation_errors.append("Capture section missing 'interval' setting")
            
            # Check storage settings
            if 'storage' in config_data:
                storage = config_data['storage']
                if not isinstance(storage, dict):
                    validation_errors.append("Storage section must be an object")
                else:
                    if 'path' not in storage:
                        validation_errors.append("Storage section missing 'path' setting")
            
            if validation_errors:
                return {
                    'valid': False,
                    'errors': validation_errors
                }
            
            return {
                'valid': True,
                'message': 'YAML configuration is valid'
            }
            
        except yaml.YAMLError as e:
            return {
                'valid': False,
                'error': f'Invalid YAML syntax: {str(e)}'
            }
        except Exception as e:
            return {
                'valid': False,
                'error': f'Validation error: {str(e)}'
            }
    
    def restore_backup(self, backup_file):
        """
        Restore configuration from backup
        
        Args:
            backup_file (str): Name of the backup file
        
        Returns:
            dict: Restore operation result
        """
        try:
            backup_path = self.backup_path / backup_file
            
            if not backup_path.exists():
                return {
                    'success': False,
                    'error': 'Backup file not found'
                }
            
            # Create backup of current config
            current_backup = self._create_backup()
            if not current_backup['success']:
                return current_backup
            
            # Restore from backup
            with open(backup_path, 'r') as src, open(self.config_path, 'w') as dst:
                dst.write(src.read())
            
            return {
                'success': True,
                'message': 'Configuration restored successfully',
                'backup_file': backup_file,
                'current_backup': current_backup.get('backup_file')
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def list_backups(self):
        """
        List available backup files
        
        Returns:
            list: List of backup files with metadata
        """
        try:
            backups = []
            for backup_file in sorted(
                self.backup_path.glob('cinepi_backup_*.yaml'),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            ):
                stat = backup_file.stat()
                
                # Load backup content for preview
                try:
                    with open(backup_file, 'r') as f:
                        content = f.read()
                        config_data = yaml.safe_load(content) if content.strip() else {}
                except:
                    config_data = {}
                
                backups.append({
                    'filename': backup_file.name,
                    'size': stat.st_size,
                    'timestamp': datetime.fromtimestamp(stat.st_mtime),
                    'path': str(backup_file),
                    'preview': config_data
                })
            
            return backups
            
        except Exception as e:
            return []
    
    def get_backup_content(self, backup_file):
        """
        Get the content of a specific backup file
        
        Args:
            backup_file (str): Name of the backup file
        
        Returns:
            dict: Backup content and metadata
        """
        try:
            backup_path = self.backup_path / backup_file
            
            if not backup_path.exists():
                return {
                    'success': False,
                    'error': 'Backup file not found'
                }
            
            with open(backup_path, 'r') as f:
                content = f.read()
            
            stat = backup_path.stat()
            
            return {
                'success': True,
                'content': content,
                'filename': backup_file,
                'size': stat.st_size,
                'timestamp': datetime.fromtimestamp(stat.st_mtime).isoformat()
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def compare_backups(self, backup1, backup2):
        """
        Compare two backup files
        
        Args:
            backup1 (str): Name of first backup file
            backup2 (str): Name of second backup file
        
        Returns:
            dict: Comparison result
        """
        try:
            # Get content of both backups
            backup1_content = self.get_backup_content(backup1)
            backup2_content = self.get_backup_content(backup2)
            
            if not backup1_content['success']:
                return backup1_content
            
            if not backup2_content['success']:
                return backup2_content
            
            # Parse YAML content
            config1 = yaml.safe_load(backup1_content['content'])
            config2 = yaml.safe_load(backup2_content['content'])
            
            # Compare configurations
            differences = self._compare_configs(config1, config2)
            
            return {
                'success': True,
                'backup1': {
                    'filename': backup1,
                    'timestamp': backup1_content['timestamp']
                },
                'backup2': {
                    'filename': backup2,
                    'timestamp': backup2_content['timestamp']
                },
                'differences': differences
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _compare_configs(self, config1, config2, path=""):
        """
        Recursively compare two configuration dictionaries
        
        Args:
            config1 (dict): First configuration
            config2 (dict): Second configuration
            path (str): Current path in configuration
        
        Returns:
            list: List of differences
        """
        differences = []
        
        # Get all keys from both configs
        all_keys = set(config1.keys()) | set(config2.keys())
        
        for key in all_keys:
            current_path = f"{path}.{key}" if path else key
            
            if key not in config1:
                differences.append({
                    'type': 'added',
                    'path': current_path,
                    'value': config2[key]
                })
            elif key not in config2:
                differences.append({
                    'type': 'removed',
                    'path': current_path,
                    'value': config1[key]
                })
            elif isinstance(config1[key], dict) and isinstance(config2[key], dict):
                # Recursively compare nested dictionaries
                nested_diffs = self._compare_configs(config1[key], config2[key], current_path)
                differences.extend(nested_diffs)
            elif config1[key] != config2[key]:
                differences.append({
                    'type': 'changed',
                    'path': current_path,
                    'old_value': config1[key],
                    'new_value': config2[key]
                })
        
        return differences
    
    def _create_backup(self):
        """
        Create automatic backup
        
        Returns:
            dict: Backup operation result
        """
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = self.backup_path / f'cinepi_backup_{timestamp}.yaml'
            
            if self.config_path.exists():
                with open(self.config_path, 'r') as src, open(backup_file, 'w') as dst:
                    dst.write(src.read())
            else:
                # Create empty backup if no config exists
                with open(backup_file, 'w') as f:
                    yaml.dump({}, f)
            
            return {
                'success': True,
                'backup_file': backup_file.name
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            } 
