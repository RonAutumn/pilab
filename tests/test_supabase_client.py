#!/usr/bin/env python3
"""
Unit tests for PiLab Supabase Client

Tests the supabase_client.py module with mocked Supabase API responses
to ensure proper error handling, retry logic, and data processing.
"""

import os
import sys
import unittest
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'utils'))

from supabase_client import PiLabSupabaseClient, AuditLogEntry, create_pilab_client
from logging_utils import get_logger
from retry import RetryError, ValidationError, TransientError, PermanentError


class MockSupabaseResponse:
    """Mock Supabase API response."""
    
    def __init__(self, data=None, error=None, status_code=200):
        self.data = data or []
        self.error = error
        self.status_code = status_code
    
    def execute(self):
        return self


class TestSupabaseClient(unittest.TestCase):
    """Unit tests for PiLabSupabaseClient."""
    
    def setUp(self):
        """Set up test environment."""
        self.logger = get_logger('pilab.test.supabase_client')
        
        # Create mock Supabase client
        self.mock_supabase = Mock()
        self.mock_storage = Mock()
        self.mock_supabase.storage.return_value = self.mock_storage
        
        # Create test client
        with patch('supabase_client.create_client', return_value=self.mock_supabase):
            self.client = create_pilab_client()
    
    def test_01_client_initialization(self):
        """Test client initialization with environment variables."""
        with patch.dict(os.environ, {
            'SUPABASE_URL': 'http://localhost:54321',
            'SUPABASE_SERVICE_ROLE_KEY': 'test_service_key'
        }):
            with patch('supabase_client.create_client') as mock_create:
                mock_create.return_value = self.mock_supabase
                client = create_pilab_client()
                
                self.assertIsNotNone(client)
                self.assertEqual(client.client, self.mock_supabase)
                mock_create.assert_called_once()
    
    def test_02_client_initialization_missing_env(self):
        """Test client initialization with missing environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                create_pilab_client()
    
    def test_03_test_connection_success(self):
        """Test successful connection test."""
        # Mock successful connection
        mock_response = MockSupabaseResponse(data=[{'test': 'success'}])
        self.mock_supabase.rpc.return_value = mock_response
        
        result = self.client.test_connection()
        self.assertTrue(result)
    
    def test_04_test_connection_failure(self):
        """Test failed connection test."""
        # Mock failed connection
        mock_response = MockSupabaseResponse(error="Connection failed", status_code=500)
        self.mock_supabase.rpc.return_value = mock_response
        
        result = self.client.test_connection()
        self.assertFalse(result)
    
    def test_05_upload_and_log_success(self):
        """Test successful image upload and logging."""
        # Create temporary test file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'test image data')
            temp_file_path = temp_file.name
        
        try:
            # Mock successful upload
            mock_upload_response = MockSupabaseResponse(data={
                'id': 'test_file_id',
                'name': 'test_image.jpg',
                'size': 1024
            })
            self.mock_storage.from_.return_value.upload.return_value = mock_upload_response
            
            # Mock successful database insert
            mock_db_response = MockSupabaseResponse(data=[{
                'id': 'test_capture_id',
                'filename': 'test_image.jpg'
            }])
            self.mock_supabase.rpc.return_value = mock_db_response
            
            # Test upload
            result = self.client.upload_and_log(
                file_path=temp_file_path,
                shot_type='timelapse',
                metadata={
                    'brightness': 0.75,
                    'sharpness': 0.82,
                    'contrast': 0.68
                }
            )
            
            # Verify result
            self.assertIsNotNone(result)
            self.assertIn('filename', result)
            self.assertEqual(result['filename'], 'test_image.jpg')
            
            # Verify upload was called
            self.mock_storage.from_.assert_called_once_with('pilab-dev')
            
        finally:
            # Clean up
            os.unlink(temp_file_path)
    
    def test_06_upload_and_log_file_not_found(self):
        """Test upload with non-existent file."""
        with self.assertRaises(FileNotFoundError):
            self.client.upload_and_log(
                file_path='/non/existent/file.jpg',
                shot_type='timelapse',
                metadata={}
            )
    
    def test_07_upload_and_log_upload_failure(self):
        """Test upload with storage failure."""
        # Create temporary test file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'test image data')
            temp_file_path = temp_file.name
        
        try:
            # Mock upload failure
            mock_upload_response = MockSupabaseResponse(
                error="Storage quota exceeded",
                status_code=413
            )
            self.mock_storage.from_.return_value.upload.return_value = mock_upload_response
            
            # Test upload
            result = self.client.upload_and_log(
                file_path=temp_file_path,
                shot_type='timelapse',
                metadata={}
            )
            
            # Verify error result
            self.assertIsNotNone(result)
            self.assertIn('error', result)
            self.assertIn('Storage quota exceeded', result['error'])
            
        finally:
            # Clean up
            os.unlink(temp_file_path)
    
    def test_08_upload_and_log_database_failure(self):
        """Test upload with database insert failure."""
        # Create temporary test file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'test image data')
            temp_file_path = temp_file.name
        
        try:
            # Mock successful upload
            mock_upload_response = MockSupabaseResponse(data={
                'id': 'test_file_id',
                'name': 'test_image.jpg',
                'size': 1024
            })
            self.mock_storage.from_.return_value.upload.return_value = mock_upload_response
            
            # Mock database failure
            mock_db_response = MockSupabaseResponse(
                error="Database constraint violation",
                status_code=400
            )
            self.mock_supabase.rpc.return_value = mock_db_response
            
            # Test upload
            result = self.client.upload_and_log(
                file_path=temp_file_path,
                shot_type='timelapse',
                metadata={}
            )
            
            # Verify error result
            self.assertIsNotNone(result)
            self.assertIn('error', result)
            self.assertIn('Database constraint violation', result['error'])
            
        finally:
            # Clean up
            os.unlink(temp_file_path)
    
    def test_09_get_storage_usage_success(self):
        """Test successful storage usage retrieval."""
        # Mock storage usage response
        mock_response = MockSupabaseResponse(data=[{
            'total_files': 150,
            'total_size_mb': 1024.5,
            'oldest_file': '2024-01-01T00:00:00Z',
            'newest_file': '2024-08-01T12:00:00Z'
        }])
        self.mock_supabase.rpc.return_value = mock_response
        
        result = self.client.get_storage_usage('pilab-dev')
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(result['total_files'], 150)
        self.assertEqual(result['total_size_mb'], 1024.5)
        self.assertIn('oldest_file', result)
        self.assertIn('newest_file', result)
    
    def test_10_get_storage_usage_failure(self):
        """Test storage usage retrieval failure."""
        # Mock failure response
        mock_response = MockSupabaseResponse(
            error="Bucket not found",
            status_code=404
        )
        self.mock_supabase.rpc.return_value = mock_response
        
        result = self.client.get_storage_usage('non-existent-bucket')
        
        # Verify error result
        self.assertIsNotNone(result)
        self.assertIn('error', result)
        self.assertIn('Bucket not found', result['error'])
    
    def test_11_log_audit_event_success(self):
        """Test successful audit event logging."""
        # Mock successful audit log insert
        mock_response = MockSupabaseResponse(data=[{
            'id': 'test_audit_id',
            'action': 'test_action',
            'created_at': datetime.utcnow().isoformat()
        }])
        self.mock_supabase.rpc.return_value = mock_response
        
        # Create test audit entry
        audit_entry = AuditLogEntry(
            action='test_action',
            object_id='test_object',
            bucket_id='pilab-dev',
            user_id=None,
            details={'test': 'data'}
        )
        
        result = self.client.log_audit_event(audit_entry)
        
        # Verify success
        self.assertTrue(result)
    
    def test_12_log_audit_event_failure(self):
        """Test audit event logging failure."""
        # Mock failure response
        mock_response = MockSupabaseResponse(
            error="Audit log table not found",
            status_code=500
        )
        self.mock_supabase.rpc.return_value = mock_response
        
        # Create test audit entry
        audit_entry = AuditLogEntry(
            action='test_action',
            object_id='test_object',
            bucket_id='pilab-dev',
            user_id=None,
            details={'test': 'data'}
        )
        
        result = self.client.log_audit_event(audit_entry)
        
        # Verify failure
        self.assertFalse(result)
    
    def test_13_get_files_for_retention_check(self):
        """Test retrieval of files for retention check."""
        # Mock files response
        mock_files = [
            {
                'id': 'file_1',
                'name': 'old_file_1.jpg',
                'size': 1024,
                'created_at': (datetime.utcnow() - timedelta(days=31)).isoformat()
            },
            {
                'id': 'file_2',
                'name': 'old_file_2.jpg',
                'size': 2048,
                'created_at': (datetime.utcnow() - timedelta(days=32)).isoformat()
            }
        ]
        mock_response = MockSupabaseResponse(data=mock_files)
        self.mock_supabase.rpc.return_value = mock_response
        
        result = self.client.get_files_for_retention_check('pilab-dev', 30)
        
        # Verify result
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['id'], 'file_1')
        self.assertEqual(result[1]['id'], 'file_2')
    
    def test_14_soft_delete_file_success(self):
        """Test successful soft delete of file."""
        # Mock successful soft delete
        mock_response = MockSupabaseResponse(data=[{
            'id': 'test_file_id',
            'deleted_at': datetime.utcnow().isoformat()
        }])
        self.mock_supabase.rpc.return_value = mock_response
        
        result = self.client.soft_delete_file('test_file_id', 'retention_policy')
        
        # Verify success
        self.assertTrue(result)
    
    def test_15_soft_delete_file_failure(self):
        """Test soft delete failure."""
        # Mock failure response
        mock_response = MockSupabaseResponse(
            error="File not found",
            status_code=404
        )
        self.mock_supabase.rpc.return_value = mock_response
        
        result = self.client.soft_delete_file('non_existent_file_id', 'retention_policy')
        
        # Verify failure
        self.assertFalse(result)
    
    def test_16_validate_file_type_valid(self):
        """Test file type validation with valid file."""
        # Create temporary valid file
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'test image data')
            temp_file_path = temp_file.name
        
        try:
            result = self.client._validate_file_type(temp_file_path)
            self.assertTrue(result)
        finally:
            os.unlink(temp_file_path)
    
    def test_17_validate_file_type_invalid(self):
        """Test file type validation with invalid file."""
        # Create temporary invalid file
        with tempfile.NamedTemporaryFile(suffix='.txt', delete=False) as temp_file:
            temp_file.write(b'text data')
            temp_file_path = temp_file.name
        
        try:
            with self.assertRaises(ValidationError):
                self.client._validate_file_type(temp_file_path)
        finally:
            os.unlink(temp_file_path)
    
    def test_18_compute_file_hash(self):
        """Test file hash computation."""
        # Create temporary test file
        test_data = b'test image data for hashing'
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(test_data)
            temp_file_path = temp_file.name
        
        try:
            # Compute hash
            file_hash = self.client._compute_file_hash(temp_file_path)
            
            # Verify hash is computed
            self.assertIsNotNone(file_hash)
            self.assertEqual(len(file_hash), 64)  # SHA-256 hash length
            
            # Verify hash is consistent
            file_hash2 = self.client._compute_file_hash(temp_file_path)
            self.assertEqual(file_hash, file_hash2)
            
        finally:
            os.unlink(temp_file_path)
    
    def test_19_generate_filename(self):
        """Test filename generation."""
        # Test filename generation
        filename = self.client._generate_filename(
            original_name='test_image.jpg',
            shot_type='timelapse',
            timestamp=datetime(2024, 8, 1, 12, 0, 0)
        )
        
        # Verify filename format
        self.assertIn('timelapse', filename)
        self.assertIn('20240801', filename)
        self.assertIn('120000', filename)
        self.assertIn('.jpg', filename)
    
    def test_20_retry_logic_integration(self):
        """Test retry logic integration with client methods."""
        from retry import retry_on_supabase_error
        
        # Mock transient failure followed by success
        call_count = 0
        
        def mock_rpc(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                return MockSupabaseResponse(error="Temporary error", status_code=503)
            else:
                return MockSupabaseResponse(data=[{'test': 'success'}])
        
        self.mock_supabase.rpc.side_effect = mock_rpc
        
        # Test with retry decorator
        @retry_on_supabase_error(max_attempts=3)
        def test_method():
            return self.client.test_connection()
        
        result = test_method()
        
        # Verify retry behavior
        self.assertTrue(result)
        self.assertEqual(call_count, 3)
    
    def test_21_error_taxonomy(self):
        """Test error taxonomy and classification."""
        # Test validation error
        with self.assertRaises(ValidationError):
            raise ValidationError("Invalid input data")
        
        # Test transient error
        with self.assertRaises(TransientError):
            raise TransientError("Network timeout")
        
        # Test permanent error
        with self.assertRaises(PermanentError):
            raise PermanentError("Invalid credentials")
    
    def test_22_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Test with empty metadata
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp_file:
            temp_file.write(b'test data')
            temp_file_path = temp_file.name
        
        try:
            # Mock successful upload
            mock_upload_response = MockSupabaseResponse(data={
                'id': 'test_file_id',
                'name': 'test_image.jpg',
                'size': 1024
            })
            self.mock_storage.from_.return_value.upload.return_value = mock_upload_response
            
            # Mock successful database insert
            mock_db_response = MockSupabaseResponse(data=[{
                'id': 'test_capture_id',
                'filename': 'test_image.jpg'
            }])
            self.mock_supabase.rpc.return_value = mock_db_response
            
            # Test with empty metadata
            result = self.client.upload_and_log(
                file_path=temp_file_path,
                shot_type='timelapse',
                metadata={}
            )
            
            self.assertIsNotNone(result)
            self.assertIn('filename', result)
            
        finally:
            os.unlink(temp_file_path)
    
    def test_23_performance_metrics(self):
        """Test performance metrics collection."""
        # Test that performance logging doesn't break functionality
        with patch('logging_utils.PerformanceLogger') as mock_perf:
            mock_perf.return_value.__enter__.return_value = Mock()
            mock_perf.return_value.__exit__.return_value = None
            
            # Mock successful connection
            mock_response = MockSupabaseResponse(data=[{'test': 'success'}])
            self.mock_supabase.rpc.return_value = mock_response
            
            result = self.client.test_connection()
            
            self.assertTrue(result)
            mock_perf.assert_called()


class TestAuditLogEntry(unittest.TestCase):
    """Unit tests for AuditLogEntry class."""
    
    def test_01_audit_entry_creation(self):
        """Test AuditLogEntry creation."""
        audit_entry = AuditLogEntry(
            action='test_action',
            object_id='test_object',
            bucket_id='pilab-dev',
            user_id='test_user',
            details={'test': 'data'}
        )
        
        self.assertEqual(audit_entry.action, 'test_action')
        self.assertEqual(audit_entry.object_id, 'test_object')
        self.assertEqual(audit_entry.bucket_id, 'pilab-dev')
        self.assertEqual(audit_entry.user_id, 'test_user')
        self.assertEqual(audit_entry.details, {'test': 'data'})
    
    def test_02_audit_entry_serialization(self):
        """Test AuditLogEntry serialization."""
        audit_entry = AuditLogEntry(
            action='test_action',
            object_id='test_object',
            bucket_id='pilab-dev',
            user_id=None,
            details={'test': 'data', 'timestamp': datetime.utcnow().isoformat()}
        )
        
        # Test that it can be converted to dict
        entry_dict = audit_entry.__dict__
        self.assertIn('action', entry_dict)
        self.assertIn('object_id', entry_dict)
        self.assertIn('bucket_id', entry_dict)
        self.assertIn('details', entry_dict)
    
    def test_03_audit_entry_validation(self):
        """Test AuditLogEntry validation."""
        # Test with required fields
        audit_entry = AuditLogEntry(
            action='test_action',
            object_id='test_object',
            bucket_id='pilab-dev',
            user_id=None,
            details={}
        )
        
        self.assertIsNotNone(audit_entry)
        
        # Test with None user_id (should be allowed)
        audit_entry = AuditLogEntry(
            action='test_action',
            object_id='test_object',
            bucket_id='pilab-dev',
            user_id=None,
            details={}
        )
        
        self.assertIsNone(audit_entry.user_id)


def run_supabase_client_tests():
    """Run all supabase client tests."""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Run tests
    unittest.main(verbosity=2)


if __name__ == '__main__':
    run_supabase_client_tests() 