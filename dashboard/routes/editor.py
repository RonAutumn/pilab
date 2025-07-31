"""
CinePi Dashboard YAML Editor Routes

This module contains routes for the YAML configuration editor interface.
"""

from flask import Blueprint, request, jsonify, render_template, current_app
from dashboard.services.config_service import ConfigService
import yaml
import json
from datetime import datetime

# Create editor blueprint
editor_bp = Blueprint('editor', __name__)


@editor_bp.route('/editor', methods=['GET'])
def yaml_editor():
    """
    Render the YAML configuration editor page
    
    Returns:
        str: Rendered HTML template
    """
    return render_template('editor.html')


@editor_bp.route('/api/editor/config', methods=['GET'])
def get_config_for_editor():
    """
    Get current configuration as YAML string for the editor
    
    Returns:
        dict: JSON response with YAML content
    """
    try:
        config_service = ConfigService()
        config_data = config_service.get_config()
        
        if 'error' in config_data:
            return jsonify({'error': config_data['error']}), 500
        
        # Convert to YAML string
        yaml_content = yaml.dump(config_data, default_flow_style=False, sort_keys=False)
        
        return jsonify({
            'success': True,
            'content': yaml_content,
            'last_modified': datetime.now().isoformat()
        })
        
    except Exception as e:
        current_app.logger.error(f"Error loading config for editor: {e}")
        return jsonify({'error': str(e)}), 500


@editor_bp.route('/api/editor/config', methods=['POST'])
def save_config_from_editor():
    """
    Save configuration from editor YAML content
    
    Expected JSON payload:
    {
        "content": "# YAML content string"
    }
    
    Returns:
        dict: JSON response with operation result
    """
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({
                'success': False,
                'error': 'YAML content is required'
            }), 400
        
        yaml_content = data['content']
        
        # Validate YAML content before saving
        config_service = ConfigService()
        validation_result = config_service.validate_yaml_content(yaml_content)
        
        if not validation_result['valid']:
            return jsonify({
                'success': False,
                'error': validation_result.get('error', 'Validation failed'),
                'errors': validation_result.get('errors', [])
            }), 400
        
        # Parse validated YAML
        config_data = yaml.safe_load(yaml_content)
        
        # Save configuration
        config_service = ConfigService()
        result = config_service.update_config(config_data)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error saving config from editor: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@editor_bp.route('/api/editor/validate', methods=['POST'])
def validate_yaml():
    """
    Validate YAML content without saving
    
    Expected JSON payload:
    {
        "content": "# YAML content string"
    }
    
    Returns:
        dict: JSON response with validation result
    """
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({
                'valid': False,
                'error': 'YAML content is required'
            }), 400
        
        yaml_content = data['content']
        
        # Use config service validation
        config_service = ConfigService()
        validation_result = config_service.validate_yaml_content(yaml_content)
        
        return jsonify(validation_result), 200
        
    except Exception as e:
        current_app.logger.error(f"Error validating YAML: {e}")
        return jsonify({'valid': False, 'error': str(e)}), 500


@editor_bp.route('/api/editor/backups', methods=['GET'])
def list_backups_for_editor():
    """
    Get list of configuration backups for the editor
    
    Returns:
        dict: JSON response with list of backups
    """
    try:
        config_service = ConfigService()
        backups = config_service.list_backups()
        
        # Transform backup format to match frontend expectations
        formatted_backups = []
        for backup in backups:
            formatted_backups.append({
                'name': backup['filename'],
                'date': backup['timestamp'].isoformat(),
                'size': backup['size'],
                'path': backup['path']
            })
        
        return jsonify({
            'success': True,
            'backups': formatted_backups
        })
        
    except Exception as e:
        current_app.logger.error(f"Error listing backups: {e}")
        return jsonify({'error': str(e)}), 500


@editor_bp.route('/api/editor/backup', methods=['POST'])
def create_backup_from_editor():
    """
    Create a new configuration backup from the editor
    
    Returns:
        dict: JSON response with backup operation result
    """
    try:
        config_service = ConfigService()
        result = config_service.create_backup()
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error creating backup: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@editor_bp.route('/api/editor/restore/<backup_name>', methods=['POST'])
def restore_backup_from_editor(backup_name):
    """
    Restore configuration from a backup file
    
    Args:
        backup_name (str): Name of the backup file to restore
    
    Returns:
        dict: JSON response with restore operation result
    """
    try:
        config_service = ConfigService()
        result = config_service.restore_backup(backup_name)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error restoring backup: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@editor_bp.route('/api/editor/backup/<backup_name>', methods=['GET'])
def get_backup_content(backup_name):
    """
    Get the content of a specific backup file
    
    Args:
        backup_name (str): Name of the backup file
    
    Returns:
        dict: JSON response with backup content
    """
    try:
        config_service = ConfigService()
        result = config_service.get_backup_content(backup_name)
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error getting backup content: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@editor_bp.route('/api/editor/compare', methods=['POST'])
def compare_backups():
    """
    Compare two backup files
    
    Expected JSON payload:
    {
        "backup1": "backup1_name.yaml",
        "backup2": "backup2_name.yaml"
    }
    
    Returns:
        dict: JSON response with comparison result
    """
    try:
        data = request.get_json()
        if not data or 'backup1' not in data or 'backup2' not in data:
            return jsonify({
                'success': False,
                'error': 'Both backup1 and backup2 are required'
            }), 400
        
        config_service = ConfigService()
        result = config_service.compare_backups(data['backup1'], data['backup2'])
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.error(f"Error comparing backups: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@editor_bp.route('/api/editor/backup/<backup_name>', methods=['DELETE'])
def delete_backup(backup_name):
    """
    Delete a backup file
    
    Args:
        backup_name (str): Name of the backup file to delete
    
    Returns:
        dict: JSON response with delete operation result
    """
    try:
        config_service = ConfigService()
        backup_path = config_service.backup_path / backup_name
        
        if not backup_path.exists():
            return jsonify({
                'success': False,
                'error': 'Backup file not found'
            }), 404
        
        # Validate backup name to prevent directory traversal
        if not backup_name.startswith('cinepi_backup_') or not backup_name.endswith('.yaml'):
            return jsonify({
                'success': False,
                'error': 'Invalid backup filename'
            }), 400
        
        backup_path.unlink()
        
        return jsonify({
            'success': True,
            'message': f'Backup {backup_name} deleted successfully'
        })
        
    except Exception as e:
        current_app.logger.error(f"Error deleting backup: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500 
