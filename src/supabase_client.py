"""
PiLab Supabase Client

This module provides a robust Supabase client with storage monitoring,
retention policy enforcement, and audit logging capabilities.
"""

import os
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

try:
    from supabase import create_client, Client
    from supabase.lib.client_options import ClientOptions
except ImportError:
    raise ImportError("Supabase Python client not installed. Run: pip install supabase")

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class StorageObject:
    """Represents a storage object with metadata."""
    id: str
    name: str
    bucket_id: str
    size: int
    created_at: datetime
    updated_at: datetime
    last_accessed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class AuditLogEntry:
    """Represents an audit log entry."""
    action: str
    object_id: str
    bucket_id: str
    user_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class PiLabSupabaseClient:
    """
    PiLab-specific Supabase client with enhanced storage capabilities.
    """
    
    def __init__(self, url: str, key: str):
        """
        Initialize the PiLab Supabase client.
        
        Args:
            url: Supabase project URL
            key: Supabase service role key
        """
        self.url = url
        self.key = key
        self.client: Optional[Client] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the Supabase client with retry logic."""
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                options = ClientOptions(
                    schema='public',
                    headers={
                        'X-Client-Info': 'pilab-storage-client/1.0.0'
                    }
                )
                
                self.client = create_client(
                    supabase_url=self.url,
                    supabase_key=self.key,
                    options=options
                )
                
                logger.info("✅ Supabase client initialized successfully")
                return
                
            except Exception as e:
                logger.warning(f"Attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    retry_delay *= 2
                else:
                    logger.error("Failed to initialize Supabase client after all retries")
                    raise
    
    def test_connection(self) -> bool:
        """
        Test the connection to Supabase.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            if not self.client:
                return False
            
            # Try a simple query to test connection
            result = self.client.table('storage_audit_log').select('id').limit(1).execute()
            return True
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def get_storage_usage(self, bucket_name: str) -> Dict[str, Any]:
        """
        Get storage usage statistics for a bucket.
        
        Args:
            bucket_name: Name of the bucket to check
            
        Returns:
            Dictionary with usage statistics
        """
        try:
            # Query storage.objects table for usage statistics
            query = """
                SELECT 
                    COUNT(*) as total_files,
                    COALESCE(SUM(metadata->>'size')::bigint, 0) as total_size,
                    MIN(created_at) as oldest_file,
                    MAX(created_at) as newest_file
                FROM storage.objects 
                WHERE bucket_id = %s AND deleted_at IS NULL
            """
            
            result = self.client.rpc('exec_sql', {'query': query, 'params': [bucket_name]}).execute()
            
            if result.data:
                data = result.data[0]
                total_size_mb = round(data['total_size'] / (1024 * 1024), 2) if data['total_size'] else 0
                
                return {
                    'bucket_name': bucket_name,
                    'total_files': data['total_files'],
                    'total_size': data['total_size'],
                    'total_size_mb': total_size_mb,
                    'oldest_file': data['oldest_file'],
                    'newest_file': data['newest_file']
                }
            else:
                return {
                    'bucket_name': bucket_name,
                    'total_files': 0,
                    'total_size': 0,
                    'total_size_mb': 0,
                    'oldest_file': None,
                    'newest_file': None
                }
                
        except Exception as e:
            logger.error(f"Failed to get storage usage for bucket {bucket_name}: {e}")
            return {'error': str(e)}
    
    def get_files_for_retention_check(self, bucket_name: str, retention_days: int) -> List[StorageObject]:
        """
        Get files that exceed the retention period.
        
        Args:
            bucket_name: Name of the bucket to check
            retention_days: Number of days to retain files
            
        Returns:
            List of StorageObject instances that exceed retention
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            query = """
                SELECT 
                    id, name, bucket_id, 
                    COALESCE(metadata->>'size', '0')::bigint as size,
                    created_at, updated_at,
                    metadata->>'last_accessed_at' as last_accessed_at,
                    metadata
                FROM storage.objects 
                WHERE bucket_id = %s 
                AND deleted_at IS NULL 
                AND created_at < %s
                ORDER BY created_at ASC
            """
            
            result = self.client.rpc('exec_sql', {
                'query': query, 
                'params': [bucket_name, cutoff_date.isoformat()]
            }).execute()
            
            files = []
            for row in result.data:
                # Parse last_accessed_at
                last_accessed = None
                if row.get('last_accessed_at'):
                    try:
                        last_accessed = datetime.fromisoformat(row['last_accessed_at'].replace('Z', '+00:00'))
                    except:
                        pass
                
                # Parse metadata
                metadata = {}
                if row.get('metadata'):
                    try:
                        metadata = json.loads(row['metadata']) if isinstance(row['metadata'], str) else row['metadata']
                    except:
                        pass
                
                file_obj = StorageObject(
                    id=row['id'],
                    name=row['name'],
                    bucket_id=row['bucket_id'],
                    size=row['size'],
                    created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00')),
                    last_accessed_at=last_accessed,
                    metadata=metadata
                )
                files.append(file_obj)
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to get files for retention check: {e}")
            return []
    
    def soft_delete_file(self, file_id: str, reason: str = "retention_policy") -> bool:
        """
        Soft delete a file by setting deleted_at timestamp.
        
        Args:
            file_id: ID of the file to soft delete
            reason: Reason for deletion
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update the file to mark it as deleted
            query = """
                UPDATE storage.objects 
                SET 
                    deleted_at = NOW(),
                    metadata = COALESCE(metadata, '{}'::jsonb) || 
                              jsonb_build_object('deleted_reason', %s, 'deleted_at', NOW())
                WHERE id = %s AND deleted_at IS NULL
            """
            
            result = self.client.rpc('exec_sql', {
                'query': query, 
                'params': [reason, file_id]
            }).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to soft delete file {file_id}: {e}")
            return False
    
    def log_audit_event(self, entry: AuditLogEntry) -> bool:
        """
        Log an audit event to the storage_audit_log table.
        
        Args:
            entry: AuditLogEntry instance
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Use the convenience function we created in the migration
            result = self.client.rpc('log_storage_audit_event', {
                'p_action': entry.action,
                'p_object_id': entry.object_id,
                'p_bucket_id': entry.bucket_id,
                'p_user_id': entry.user_id,
                'p_details': json.dumps(entry.details) if entry.details else '{}'
            }).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to log audit event: {e}")
            return False
    
    def get_audit_logs(self, bucket_id: str = None, action: str = None, 
                      since: datetime = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve audit logs with optional filtering.
        
        Args:
            bucket_id: Filter by bucket ID
            action: Filter by action type
            since: Filter by timestamp (get logs since this time)
            limit: Maximum number of logs to return
            
        Returns:
            List of audit log entries
        """
        try:
            query = "SELECT * FROM storage_audit_log WHERE 1=1"
            params = []
            
            if bucket_id:
                query += " AND bucket_id = %s"
                params.append(bucket_id)
            
            if action:
                query += " AND action = %s"
                params.append(action)
            
            if since:
                query += " AND timestamp >= %s"
                params.append(since.isoformat())
            
            query += " ORDER BY timestamp DESC LIMIT %s"
            params.append(limit)
            
            result = self.client.rpc('exec_sql', {
                'query': query, 
                'params': params
            }).execute()
            
            return result.data if result.data else []
            
        except Exception as e:
            logger.error(f"Failed to get audit logs: {e}")
            return []
    
    def list_objects(self, bucket_name: str, prefix: str = "", limit: int = 100) -> List[StorageObject]:
        """
        List objects in a bucket.
        
        Args:
            bucket_name: Name of the bucket
            prefix: Optional prefix to filter objects
            limit: Maximum number of objects to return
            
        Returns:
            List of StorageObject instances
        """
        try:
            query = """
                SELECT 
                    id, name, bucket_id, 
                    COALESCE(metadata->>'size', '0')::bigint as size,
                    created_at, updated_at,
                    metadata->>'last_accessed_at' as last_accessed_at,
                    metadata
                FROM storage.objects 
                WHERE bucket_id = %s AND deleted_at IS NULL
            """
            params = [bucket_name]
            
            if prefix:
                query += " AND name LIKE %s"
                params.append(f"{prefix}%")
            
            query += " ORDER BY created_at DESC LIMIT %s"
            params.append(limit)
            
            result = self.client.rpc('exec_sql', {
                'query': query, 
                'params': params
            }).execute()
            
            objects = []
            for row in result.data:
                # Parse last_accessed_at
                last_accessed = None
                if row.get('last_accessed_at'):
                    try:
                        last_accessed = datetime.fromisoformat(row['last_accessed_at'].replace('Z', '+00:00'))
                    except:
                        pass
                
                # Parse metadata
                metadata = {}
                if row.get('metadata'):
                    try:
                        metadata = json.loads(row['metadata']) if isinstance(row['metadata'], str) else row['metadata']
                    except:
                        pass
                
                obj = StorageObject(
                    id=row['id'],
                    name=row['name'],
                    bucket_id=row['bucket_id'],
                    size=row['size'],
                    created_at=datetime.fromisoformat(row['created_at'].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(row['updated_at'].replace('Z', '+00:00')),
                    last_accessed_at=last_accessed,
                    metadata=metadata
                )
                objects.append(obj)
            
            return objects
            
        except Exception as e:
            logger.error(f"Failed to list objects in bucket {bucket_name}: {e}")
            return []


def create_pilab_client() -> PiLabSupabaseClient:
    """
    Create a PiLab Supabase client using environment variables.
    
    Returns:
        Configured PiLabSupabaseClient instance
    """
    # Load environment variables
    url = os.getenv('SUPABASE_URL', 'http://localhost:54321')
    key = os.getenv('SUPABASE_SERVICE_KEY')
    
    if not key:
        raise ValueError("SUPABASE_SERVICE_KEY environment variable is required")
    
    return PiLabSupabaseClient(url, key) 