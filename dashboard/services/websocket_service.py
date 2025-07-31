"""
CinePi Dashboard WebSocket Service

This service handles WebSocket event broadcasting and real-time updates.
"""

import json
from datetime import datetime
from dashboard.extensions import socketio
from dashboard.services.camera_service import CameraService
from dashboard.services.capture_service import CaptureService
import time


class WebSocketService:
    """Service for WebSocket event handling and broadcasting"""
    
    def __init__(self):
        self.camera_service = CameraService()
        self.capture_service = CaptureService()
    
    def broadcast_status(self, status_data):
        """
        Broadcast status update to all connected clients
        
        Args:
            status_data (dict): Status data to broadcast
        """
        socketio.emit('status_update', status_data, room='dashboard')
    
    def broadcast_log(self, log_entry, level='info'):
        """
        Broadcast log entry to all connected clients
        
        Args:
            log_entry (str): Log message
            level (str): Log level (info, warning, error)
        """
        socketio.emit('log_entry', {
            'timestamp': datetime.now().isoformat(),
            'message': log_entry,
            'level': level
        }, room='dashboard')
    
    def broadcast_capture_update(self, capture_info):
        """
        Broadcast capture update to all connected clients
        
        Args:
            capture_info (dict): Capture information
        """
        socketio.emit('capture_update', capture_info, room='dashboard')
    
    def broadcast_settings_update(self, settings_info):
        """
        Broadcast settings update to all connected clients
        
        Args:
            settings_info (dict): Settings information
        """
        socketio.emit('settings_update', settings_info, room='dashboard')
    
    def broadcast_error(self, error_message, severity='error'):
        """
        Broadcast error notification to all connected clients
        
        Args:
            error_message (str): Error message
            severity (str): Error severity (error, warning, info)
        """
        socketio.emit('error_update', {
            'error': error_message,
            'timestamp': datetime.now().isoformat(),
            'severity': severity
        }, room='dashboard')
    
    def get_current_status(self):
        """
        Get current system status for new connections
        
        Returns:
            dict: Current system status
        """
        try:
            # Get camera status
            camera_status = self.camera_service.get_status()
            
            # Get session information
            session_info = self.capture_service.get_session_info()
            
            # Get system information
            system_info = self._get_system_info()
            
            return {
                'camera': camera_status,
                'session': session_info,
                'system': system_info,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _get_system_info(self):
        """
        Get system information including uptime, disk usage, etc.
        
        Returns:
            dict: System information
        """
        try:
            import psutil
            import platform
            from pathlib import Path
            
            # Get system uptime
            uptime_seconds = time.time() - psutil.boot_time()
            uptime_hours = int(uptime_seconds // 3600)
            uptime_minutes = int((uptime_seconds % 3600) // 60)
            uptime_str = f"{uptime_hours}h {uptime_minutes}m"
            
            # Get disk usage for captures directory
            captures_path = Path('/opt/cinepi/captures')
            disk_usage = {'total': 0, 'used': 0, 'free': 0, 'percent': 0}
            
            if captures_path.exists():
                try:
                    disk_stats = psutil.disk_usage(str(captures_path))
                    disk_usage = {
                        'total': disk_stats.total,
                        'used': disk_stats.used,
                        'free': disk_stats.free,
                        'percent': disk_stats.percent
                    }
                except Exception:
                    pass
            
            # Get memory usage
            memory = psutil.virtual_memory()
            
            # Get CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            
            return {
                'uptime': uptime_str,
                'version': '1.0.0',
                'platform': platform.system(),
                'disk': disk_usage,
                'memory': {
                    'total': memory.total,
                    'used': memory.used,
                    'free': memory.free,
                    'percent': memory.percent
                },
                'cpu': {
                    'percent': cpu_percent,
                    'count': psutil.cpu_count()
                }
            }
            
        except ImportError:
            # psutil not available, return basic info
            return {
                'uptime': 'Unknown',
                'version': '1.0.0',
                'platform': 'Unknown',
                'disk': {'total': 0, 'used': 0, 'free': 0, 'percent': 0},
                'memory': {'total': 0, 'used': 0, 'free': 0, 'percent': 0},
                'cpu': {'percent': 0, 'count': 0}
            }
        except Exception as e:
            return {
                'uptime': 'Error',
                'version': '1.0.0',
                'platform': 'Unknown',
                'error': str(e)
            }
    
    def get_recent_logs(self, limit=50):
        """
        Get recent log entries from CinePi log files
        
        Args:
            limit (int): Maximum number of log entries to return
        
        Returns:
            list: Recent log entries
        """
        try:
            from pathlib import Path
            import re
            
            logs = []
            log_paths = [
                Path('/var/log/cinepi/cinepi.log'),
                Path('/var/log/cinepi/capture.log'),
                Path('/var/log/cinepi/camera.log'),
                Path('/var/log/syslog')  # System logs
            ]
            
            # Read from each log file
            for log_path in log_paths:
                if log_path.exists():
                    try:
                        with open(log_path, 'r', encoding='utf-8', errors='ignore') as f:
                            lines = f.readlines()
                            
                            # Parse log lines (basic parsing)
                            for line in lines[-limit:]:  # Get last N lines
                                line = line.strip()
                                if line:
                                    # Try to parse timestamp and level
                                    timestamp_match = re.search(r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})', line)
                                    level_match = re.search(r'(ERROR|WARN|INFO|DEBUG)', line, re.IGNORECASE)
                                    
                                    timestamp = timestamp_match.group(1) if timestamp_match else datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    level = level_match.group(1).lower() if level_match else 'info'
                                    
                                    # Extract message (everything after timestamp and level)
                                    message = line
                                    if timestamp_match:
                                        message = line[timestamp_match.end():].strip()
                                    if level_match:
                                        message = re.sub(r'ERROR|WARN|INFO|DEBUG', '', message, flags=re.IGNORECASE).strip()
                                    
                                    logs.append({
                                        'timestamp': timestamp,
                                        'message': message,
                                        'level': level,
                                        'source': log_path.name
                                    })
                    except Exception as e:
                        # If we can't read a log file, continue with others
                        continue
            
            # Sort by timestamp (newest first) and limit results
            logs.sort(key=lambda x: x['timestamp'], reverse=True)
            return logs[:limit]
            
        except Exception as e:
            # Fallback to mock data if log reading fails
            return [
                {
                    'timestamp': datetime.now().isoformat(),
                    'message': f'Log reading error: {str(e)}',
                    'level': 'error',
                    'source': 'dashboard'
                },
                {
                    'timestamp': datetime.now().isoformat(),
                    'message': 'Dashboard started',
                    'level': 'info',
                    'source': 'dashboard'
                }
            ]
    
    def notify_capture_started(self, interval):
        """
        Notify clients that capture has started
        
        Args:
            interval (int): Capture interval
        """
        self.broadcast_capture_update({
            'type': 'started',
            'interval': interval,
            'timestamp': datetime.now().isoformat()
        })
        
        self.broadcast_log(f'Timelapse started with {interval}s interval', 'info')
    
    def notify_capture_stopped(self):
        """
        Notify clients that capture has stopped
        """
        self.broadcast_capture_update({
            'type': 'stopped',
            'timestamp': datetime.now().isoformat()
        })
        
        self.broadcast_log('Timelapse stopped', 'info')
    
    def notify_capture_taken(self, filename, count):
        """
        Notify clients that a capture was taken
        
        Args:
            filename (str): Captured file name
            count (int): Total capture count
        """
        self.broadcast_capture_update({
            'type': 'taken',
            'filename': filename,
            'count': count,
            'timestamp': datetime.now().isoformat()
        })
        
        self.broadcast_log(f'Capture #{count} saved: {filename}', 'info')
    
    def notify_settings_updated(self, settings):
        """
        Notify clients that settings were updated
        
        Args:
            settings (dict): Updated settings
        """
        self.broadcast_settings_update({
            'settings': settings,
            'timestamp': datetime.now().isoformat()
        })
        
        self.broadcast_log('Camera settings updated', 'info')
    
    def notify_error(self, error_message, severity='error'):
        """
        Notify clients of an error
        
        Args:
            error_message (str): Error message
            severity (str): Error severity
        """
        self.broadcast_error(error_message, severity) 
