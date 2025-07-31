"""
CinePi Dashboard Capture Service

This service handles timelapse capture control and session management.
"""

import subprocess
import json
from pathlib import Path
from datetime import datetime


class CaptureService:
    """Service for timelapse capture control"""
    
    def __init__(self):
        self.session = None
        self.captures_path = Path('/opt/cinepi/captures')
    
    def start_session(self, interval):
        """
        Start timelapse capture session
        
        Args:
            interval (int): Capture interval in seconds
        
        Returns:
            dict: Operation result
        """
        try:
            # Check if session is already active
            if self.session and self.session.get('status') == 'active':
                return {
                    'success': False,
                    'error': 'Capture session is already active'
                }
            
            # Integration with existing CinePi timing controller
            result = subprocess.run([
                'python3', '-m', 'cinepi.timing', 'start', 
                '--interval', str(interval)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.session = {
                    'start_time': datetime.now(),
                    'interval': interval,
                    'status': 'active'
                }
                return {
                    'success': True,
                    'message': f'Session started with {interval}s interval',
                    'session': self.session
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or 'Failed to start capture session'
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Start session request timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def stop_session(self):
        """
        Stop timelapse capture session
        
        Returns:
            dict: Operation result
        """
        try:
            # Check if session is not active
            if not self.session or self.session.get('status') != 'active':
                return {
                    'success': False,
                    'error': 'No active capture session to stop'
                }
            
            # Integration with existing CinePi timing controller
            result = subprocess.run([
                'python3', '-m', 'cinepi.timing', 'stop'
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.session['status'] = 'stopped'
                self.session['end_time'] = datetime.now()
                
                return {
                    'success': True,
                    'message': 'Session stopped',
                    'session': self.session
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or 'Failed to stop capture session'
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Stop session request timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def update_interval(self, new_interval):
        """
        Update capture interval during active session
        
        Args:
            new_interval (int): New capture interval in seconds
        
        Returns:
            dict: Operation result
        """
        try:
            # Check if session is active
            if not self.session or self.session.get('status') != 'active':
                return {
                    'success': False,
                    'error': 'No active capture session to update'
                }
            
            # Integration with existing CinePi timing controller
            result = subprocess.run([
                'python3', '-m', 'cinepi.timing', 'update-interval',
                '--interval', str(new_interval)
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                self.session['interval'] = new_interval
                return {
                    'success': True,
                    'message': f'Interval updated to {new_interval}s',
                    'session': self.session
                }
            else:
                return {
                    'success': False,
                    'error': result.stderr or 'Failed to update interval'
                }
                
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': 'Update interval request timed out'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_session_info(self):
        """
        Get current session information
        
        Returns:
            dict: Session information
        """
        if not self.session:
            return {
                'status': 'inactive',
                'captures': 0,
                'start_time': None,
                'interval': None,
                'elapsed_time': 0
            }
        
        # Get capture count from file system
        try:
            if self.captures_path.exists():
                capture_count = len(list(self.captures_path.glob('*.jpg')))
            else:
                capture_count = 0
        except Exception:
            capture_count = 0
        
        # Calculate elapsed time
        elapsed_time = 0
        if self.session.get('start_time'):
            elapsed_time = (datetime.now() - self.session['start_time']).total_seconds()
        
        return {
            'status': self.session.get('status', 'unknown'),
            'start_time': self.session.get('start_time'),
            'interval': self.session.get('interval'),
            'captures': capture_count,
            'elapsed_time': elapsed_time
        }
    
    def get_capture_list(self, limit=50):
        """
        Get list of recent captures
        
        Args:
            limit (int): Maximum number of captures to return
        
        Returns:
            list: List of capture metadata
        """
        try:
            if not self.captures_path.exists():
                return []
            
            captures = []
            for file_path in sorted(
                self.captures_path.glob('*.jpg'),
                key=lambda x: x.stat().st_mtime,
                reverse=True
            )[:limit]:
                stat = file_path.stat()
                captures.append({
                    'filename': file_path.name,
                    'size': stat.st_size,
                    'timestamp': datetime.fromtimestamp(stat.st_mtime),
                    'path': str(file_path)
                })
            
            return captures
            
        except Exception as e:
            return []
    
    def delete_capture(self, filename):
        """
        Delete a specific capture file
        
        Args:
            filename (str): Name of the file to delete
        
        Returns:
            dict: Operation result
        """
        try:
            file_path = self.captures_path / filename
            
            if not file_path.exists():
                return {
                    'success': False,
                    'error': 'File not found'
                }
            
            file_path.unlink()
            
            return {
                'success': True,
                'message': f'Deleted {filename}'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            } 
