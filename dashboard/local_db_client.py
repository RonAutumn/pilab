#!/usr/bin/env python3
"""
Local Database Client for PiLab Dashboard

This module provides a simple database client that works directly with the local
PostgreSQL database, bypassing the Supabase client for local development.
"""

import os
import logging
import psycopg2
from psycopg2.extras import RealDictCursor
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class LocalDBClient:
    """
    Local database client for PiLab dashboard.
    """
    
    def __init__(self):
        """Initialize the local database client."""
        self.connection = None
        self._connect()
    
    def _connect(self):
        """Connect to the local PostgreSQL database."""
        try:
            self.connection = psycopg2.connect(
                host="localhost",
                port=54322,
                database="pilab_dev",
                user="postgres",
                password="pilab_dev_password_2024"
            )
            logger.info("✅ Connected to local PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to local database: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test the database connection."""
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def get_storage_usage(self, bucket_name: str) -> Dict[str, Any]:
        """Get storage usage statistics."""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # For now, return mock data since we don't have storage.objects table
                cursor.execute("SELECT COUNT(*) as total_files FROM captures")
                result = cursor.fetchone()
                total_files = result['total_files'] if result else 0
                
                return {
                    'total_files': total_files,
                    'total_size_mb': 0,  # Mock data
                    'oldest_file': None,
                    'newest_file': None
                }
        except Exception as e:
            logger.error(f"Failed to get storage usage: {e}")
            return {'error': str(e)}
    
    def get_upload_metrics_24h(self) -> Dict[str, Any]:
        """Get upload metrics for the last 24 hours."""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT 
                        COUNT(*) as total_uploads,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_uploads,
                        COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_uploads,
                        AVG(CASE WHEN status = 'success' THEN file_size END) as avg_file_size,
                        MAX(created_at) as last_upload
                    FROM upload_logs
                    WHERE created_at >= NOW() - INTERVAL '24 hours'
                """
                cursor.execute(query)
                result = cursor.fetchone()
                
                if result:
                    total_uploads = result['total_uploads'] or 0
                    successful_uploads = result['successful_uploads'] or 0
                    failed_uploads = result['failed_uploads'] or 0
                    success_rate = (successful_uploads / total_uploads * 100) if total_uploads > 0 else 0
                    avg_file_size = result['avg_file_size'] or 0
                    
                    return {
                        'total_uploads_24h': total_uploads,
                        'successful_uploads_24h': successful_uploads,
                        'failed_uploads_24h': failed_uploads,
                        'success_rate_24h': round(success_rate, 2),
                        'avg_file_size_mb': round(avg_file_size / (1024 * 1024), 2) if avg_file_size > 0 else 0,
                        'last_upload': result['last_upload']
                    }
                else:
                    return {
                        'total_uploads_24h': 0,
                        'successful_uploads_24h': 0,
                        'failed_uploads_24h': 0,
                        'success_rate_24h': 0,
                        'avg_file_size_mb': 0,
                        'last_upload': None
                    }
        except Exception as e:
            logger.error(f"Failed to get upload metrics: {e}")
            return {'error': str(e)}
    
    def get_recent_captures(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent captures."""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT 
                        id, file_path, shot_type,
                        brightness, sharpness, contrast, exposure, iso,
                        temperature, focus_position, frame_hash,
                        metadata, created_at
                    FROM captures
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                cursor.execute(query, (limit,))
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Failed to get recent captures: {e}")
            return []
    
    def get_alerts(self) -> List[Dict[str, Any]]:
        """Get system alerts."""
        alerts = []
        
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                # Check for failed uploads in last hour
                query = """
                    SELECT COUNT(*) as failed_count
                    FROM upload_logs
                    WHERE status = 'failed' 
                    AND created_at >= NOW() - INTERVAL '1 hour'
                """
                cursor.execute(query)
                result = cursor.fetchone()
                
                if result and result['failed_count'] > 0:
                    alerts.append({
                        'type': 'warning',
                        'message': f"{result['failed_count']} upload failures in the last hour",
                        'timestamp': datetime.utcnow().isoformat()
                    })
                
                # Check storage usage (mock for now)
                alerts.append({
                    'type': 'info',
                    'message': "Local development mode - using mock storage data",
                    'timestamp': datetime.utcnow().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            alerts.append({
                'type': 'error',
                'message': f"Failed to check system status: {e}",
                'timestamp': datetime.utcnow().isoformat()
            })
        
        return alerts
    
    def get_audit_logs(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent audit logs."""
        try:
            with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT 
                        id, action, object_id, bucket_id, user_id,
                        details, created_at
                    FROM storage_audit_log
                    ORDER BY created_at DESC
                    LIMIT %s
                """
                cursor.execute(query, (limit,))
                results = cursor.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status."""
        try:
            is_connected = self.test_connection()
            return {
                'status': 'healthy' if is_connected else 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'supabase_connected': is_connected
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                'status': 'unhealthy',
                'timestamp': datetime.utcnow().isoformat(),
                'supabase_connected': False,
                'error': str(e)
            }
    
    def close(self):
        """Close the database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")
    
    def insert_capture(self, capture_data: Dict[str, Any]) -> bool:
        """Insert a new capture record."""
        try:
            query = """
                INSERT INTO captures (
                    id, file_path, shot_type, brightness, sharpness, contrast,
                    exposure, iso, temperature, focus_position, frame_hash,
                    metadata, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, (
                    capture_data['id'],
                    capture_data['file_path'],
                    capture_data['shot_type'],
                    capture_data['brightness'],
                    capture_data['sharpness'],
                    capture_data['contrast'],
                    capture_data['exposure'],
                    capture_data['iso'],
                    capture_data['temperature'],
                    capture_data['focus_position'],
                    capture_data['frame_hash'],
                    capture_data['metadata'],
                    capture_data['created_at']
                ))
                self.connection.commit()
                return True
        except Exception as e:
            logger.error(f"Error inserting capture: {e}")
            self.connection.rollback()
            return False
    
    def insert_upload_log(self, upload_data: Dict[str, Any]) -> bool:
        """Insert a new upload log record."""
        try:
            query = """
                INSERT INTO upload_logs (
                    id, filename, file_path, file_size, status, bucket_id,
                    object_id, user_id, error_message, upload_duration_ms,
                    created_at, updated_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, (
                    upload_data['id'],
                    upload_data['filename'],
                    upload_data['file_path'],
                    upload_data['file_size'],
                    upload_data['status'],
                    upload_data['bucket_id'],
                    upload_data['object_id'],
                    upload_data['user_id'],
                    upload_data['error_message'],
                    upload_data['upload_duration_ms'],
                    upload_data['created_at'],
                    upload_data['updated_at']
                ))
                self.connection.commit()
                return True
        except Exception as e:
            logger.error(f"Error inserting upload log: {e}")
            self.connection.rollback()
            return False
    
    def insert_audit_log(self, audit_data: Dict[str, Any]) -> bool:
        """Insert a new audit log record."""
        try:
            query = """
                INSERT INTO storage_audit_log (
                    id, action, object_id, bucket_id, user_id, details, created_at
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s
                )
            """
            
            with self.connection.cursor() as cursor:
                cursor.execute(query, (
                    audit_data['id'],
                    audit_data['action'],
                    audit_data['object_id'],
                    audit_data['bucket_id'],
                    audit_data['user_id'],
                    audit_data['details'],
                    audit_data['created_at']
                ))
                self.connection.commit()
                return True
        except Exception as e:
            logger.error(f"Error inserting audit log: {e}")
            self.connection.rollback()
            return False


def create_local_client() -> LocalDBClient:
    """Create a local database client."""
    return LocalDBClient() 