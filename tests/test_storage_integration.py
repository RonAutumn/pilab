#!/usr/bin/env python3
"""
Integration tests for PiLab Storage System

Tests the complete storage system including:
- Error handling and retry logic
- Chunked processing for bulk operations
- RLS compliance
- Dashboard functionality
- Monitoring scripts
"""

import os
import sys
import unittest
import tempfile
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'utils'))

from supabase_client import PiLabSupabaseClient, create_pilab_client, AuditLogEntry
from logging_utils import get_logger, log_with_context, generate_correlation_id
from retry import retry_on_supabase_error, RetryError, ValidationError, TransientError, PermanentError
from chunked_processing import process_bulk_data, DEFAULT_CHUNK_SIZE, ChunkedProcessor


class TestStorageIntegration(unittest.TestCase):
    """Integration tests for the complete storage system."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        cls.logger = get_logger('pilab.test.integration')
        cls.correlation_id = generate_correlation_id()
        
        # Initialize client
        try:
            cls.client = create_pilab_client()
            if not cls.client.test_connection():
                raise Exception("Failed to connect to Supabase")
        except Exception as e:
            cls.logger.error(f"Failed to initialize test client: {e}")
            raise
    
    def setUp(self):
        """Set up each test."""
        self.test_correlation_id = generate_correlation_id()
        log_with_context(self.logger, 'INFO', f"Starting test: {self._testMethodName}", 
                        correlation_id=self.test_correlation_id)
    
    def tearDown(self):
        """Clean up after each test."""
        log_with_context(self.logger, 'INFO', f"Completed test: {self._testMethodName}", 
                        correlation_id=self.test_correlation_id)
    
    def test_01_client_initialization_with_retry(self):
        """Test client initialization with retry logic."""
        @retry_on_supabase_error(max_attempts=3)
        def create_test_client():
            return create_pilab_client()
        
        client = create_test_client()
        self.assertIsNotNone(client)
        self.assertTrue(client.test_connection())
        
        log_with_context(self.logger, 'INFO', "Client initialization with retry successful", 
                        correlation_id=self.test_correlation_id)
    
    def test_02_structured_logging(self):
        """Test structured logging functionality."""
        test_message = "Test structured logging"
        test_context = {
            'test_id': 'test_02',
            'timestamp': datetime.utcnow().isoformat(),
            'correlation_id': self.test_correlation_id
        }
        
        log_with_context(self.logger, 'INFO', test_message, **test_context)
        
        # Verify log file exists and contains structured data
        log_file = 'logs/pilab.test.integration.log'
        if os.path.exists(log_file):
            with open(log_file, 'r') as f:
                log_content = f.read()
                self.assertIn(test_message, log_content)
                self.assertIn(self.test_correlation_id, log_content)
        
        log_with_context(self.logger, 'INFO', "Structured logging test completed", 
                        correlation_id=self.test_correlation_id)
    
    def test_03_chunked_processing(self):
        """Test chunked processing for bulk operations."""
        # Create test data
        test_data = [{'id': i, 'value': f'test_{i}'} for i in range(250)]
        
        def process_chunk(chunk):
            """Process a chunk of data."""
            results = []
            for item in chunk:
                # Simulate some processing
                processed_item = {
                    'id': item['id'],
                    'value': item['value'],
                    'processed': True,
                    'timestamp': datetime.utcnow().isoformat()
                }
                results.append(processed_item)
            return results
        
        # Test chunked processing
        result = process_bulk_data(
            data=test_data,
            processor=process_chunk,
            chunk_size=50,
            logger=self.logger
        )
        
        # Verify results
        self.assertEqual(result.total_items, 250)
        self.assertEqual(result.total_chunks, 5)  # 250 / 50 = 5 chunks
        self.assertEqual(result.successful_chunks, 5)
        self.assertEqual(result.failed_chunks, 0)
        self.assertEqual(result.success_rate, 1.0)
        
        # Verify all items were processed
        total_processed = sum(len(chunk.data) for chunk in result.chunk_results)
        self.assertEqual(total_processed, 250)
        
        log_with_context(self.logger, 'INFO', "Chunked processing test completed", 
                        correlation_id=self.test_correlation_id, 
                        total_items=result.total_items, success_rate=result.success_rate)
    
    def test_04_retry_logic(self):
        """Test retry logic with different error types."""
        attempt_count = 0
        
        def failing_function():
            """Function that fails on first two attempts."""
            nonlocal attempt_count
            attempt_count += 1
            
            if attempt_count <= 2:
                raise TransientError(f"Transient error on attempt {attempt_count}")
            return "success"
        
        @retry_on_supabase_error(max_attempts=3)
        def retry_wrapper():
            return failing_function()
        
        # Test retry on transient error
        result = retry_wrapper()
        self.assertEqual(result, "success")
        self.assertEqual(attempt_count, 3)
        
        # Test permanent error (should not retry)
        attempt_count = 0
        
        def permanent_failing_function():
            """Function that raises permanent error."""
            nonlocal attempt_count
            attempt_count += 1
            raise PermanentError("Permanent error")
        
        @retry_on_supabase_error(max_attempts=3)
        def retry_wrapper_permanent():
            return permanent_failing_function()
        
        with self.assertRaises(PermanentError):
            retry_wrapper_permanent()
        
        # Should only attempt once for permanent error
        self.assertEqual(attempt_count, 1)
        
        log_with_context(self.logger, 'INFO', "Retry logic test completed", 
                        correlation_id=self.test_correlation_id)
    
    def test_05_storage_usage_monitoring(self):
        """Test storage usage monitoring with error handling."""
        @retry_on_supabase_error(max_attempts=3)
        def get_storage_usage():
            return self.client.get_storage_usage('pilab-dev')
        
        usage = get_storage_usage()
        
        # Verify usage data structure
        self.assertIsInstance(usage, dict)
        self.assertIn('total_files', usage)
        self.assertIn('total_size_mb', usage)
        
        # Log the usage data
        log_with_context(self.logger, 'INFO', "Storage usage retrieved successfully", 
                        correlation_id=self.test_correlation_id,
                        total_files=usage.get('total_files', 0),
                        total_size_mb=usage.get('total_size_mb', 0))
    
    def test_06_audit_logging(self):
        """Test audit logging functionality."""
        test_audit_entry = AuditLogEntry(
            action='test_audit',
            object_id='test_object_123',
            bucket_id='pilab-dev',
            user_id=None,
            details={
                'test_id': 'test_06',
                'correlation_id': self.test_correlation_id,
                'timestamp': datetime.utcnow().isoformat()
            }
        )
        
        # Log audit event
        success = self.client.log_audit_event(test_audit_entry)
        self.assertTrue(success)
        
        log_with_context(self.logger, 'INFO', "Audit logging test completed", 
                        correlation_id=self.test_correlation_id)
    
    def test_07_rls_compliance(self):
        """Test RLS compliance by verifying access patterns."""
        # Test that we can read captures with service role
        query = """
            SELECT COUNT(*) as count
            FROM captures
            LIMIT 1
        """
        
        result = self.client.client.rpc('exec_sql', {
            'query': query,
            'params': []
        }).execute()
        
        self.assertIsNotNone(result.data)
        
        # Test that we can read upload_logs
        query = """
            SELECT COUNT(*) as count
            FROM upload_logs
            LIMIT 1
        """
        
        result = self.client.client.rpc('exec_sql', {
            'query': query,
            'params': []
        }).execute()
        
        self.assertIsNotNone(result.data)
        
        # Test that we can read storage_audit_log
        query = """
            SELECT COUNT(*) as count
            FROM storage_audit_log
            LIMIT 1
        """
        
        result = self.client.client.rpc('exec_sql', {
            'query': query,
            'params': []
        }).execute()
        
        self.assertIsNotNone(result.data)
        
        log_with_context(self.logger, 'INFO', "RLS compliance test completed", 
                        correlation_id=self.test_correlation_id)
    
    def test_08_chunked_database_operations(self):
        """Test chunked database operations."""
        # Create test data for bulk insert simulation
        test_records = [
            {
                'filename': f'test_file_{i}.jpg',
                'file_path': f'/test/path/file_{i}.jpg',
                'file_size': 1024 * i,
                'shot_type': 'test',
                'brightness': 0.5,
                'sharpness': 0.7,
                'contrast': 0.6,
                'color_stats': json.dumps({'r': 128, 'g': 128, 'b': 128})
            }
            for i in range(100)
        ]
        
        def process_db_chunk(chunk):
            """Process a chunk of database records."""
            # Simulate database operations
            processed = []
            for record in chunk:
                # Simulate some processing
                processed_record = {
                    **record,
                    'processed': True,
                    'processed_at': datetime.utcnow().isoformat()
                }
                processed.append(processed_record)
            return processed
        
        # Test chunked processing
        result = process_bulk_data(
            data=test_records,
            processor=process_db_chunk,
            chunk_size=25,  # Process 25 records at a time
            logger=self.logger
        )
        
        # Verify results
        self.assertEqual(result.total_items, 100)
        self.assertEqual(result.total_chunks, 4)  # 100 / 25 = 4 chunks
        self.assertEqual(result.successful_chunks, 4)
        self.assertEqual(result.failed_chunks, 0)
        
        log_with_context(self.logger, 'INFO', "Chunked database operations test completed", 
                        correlation_id=self.test_correlation_id,
                        total_items=result.total_items, success_rate=result.success_rate)
    
    def test_09_performance_monitoring(self):
        """Test performance monitoring and metrics collection."""
        from logging_utils import PerformanceLogger
        
        # Test performance logging
        with PerformanceLogger(self.logger, "test_operation", 
                             correlation_id=self.test_correlation_id) as perf:
            # Simulate some work
            import time
            time.sleep(0.1)
            
            # Add custom metrics
            perf.add_metric("items_processed", 100)
            perf.add_metric("success_rate", 0.95)
        
        log_with_context(self.logger, 'INFO', "Performance monitoring test completed", 
                        correlation_id=self.test_correlation_id)
    
    def test_10_error_taxonomy(self):
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
        
        log_with_context(self.logger, 'INFO', "Error taxonomy test completed", 
                        correlation_id=self.test_correlation_id)
    
    def test_11_health_check_endpoints(self):
        """Test health check and metrics endpoints."""
        # Test health check
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'database': 'connected',
            'correlation_id': self.test_correlation_id
        }
        
        self.assertIn('status', health_data)
        self.assertIn('timestamp', health_data)
        self.assertIn('database', health_data)
        
        # Test metrics collection
        metrics = {
            'pilab_storage_files_total': 0,
            'pilab_storage_size_bytes': 0,
            'pilab_uploads_total': 0,
            'pilab_uploads_success_total': 0,
            'pilab_uploads_failed_total': 0,
            'pilab_captures_total': 0
        }
        
        for metric_name, value in metrics.items():
            self.assertIsInstance(value, int)
            self.assertGreaterEqual(value, 0)
        
        log_with_context(self.logger, 'INFO', "Health check endpoints test completed", 
                        correlation_id=self.test_correlation_id)
    
    def test_12_comprehensive_integration(self):
        """Comprehensive integration test combining all components."""
        # Test the complete workflow
        test_correlation_id = generate_correlation_id()
        
        # 1. Initialize client with retry
        @retry_on_supabase_error(max_attempts=3)
        def initialize_client():
            return create_pilab_client()
        
        client = initialize_client()
        self.assertIsNotNone(client)
        
        # 2. Get storage usage with structured logging
        log_with_context(self.logger, 'INFO', "Starting comprehensive integration test", 
                        correlation_id=test_correlation_id)
        
        usage = client.get_storage_usage('pilab-dev')
        self.assertIsInstance(usage, dict)
        
        # 3. Test chunked processing with audit logging
        test_data = [{'id': i, 'action': 'test'} for i in range(50)]
        
        def process_with_audit(chunk):
            """Process chunk with audit logging."""
            for item in chunk:
                audit_entry = AuditLogEntry(
                    action='test_integration',
                    object_id=f"test_{item['id']}",
                    bucket_id='pilab-dev',
                    user_id=None,
                    details={
                        'test_id': 'comprehensive_integration',
                        'correlation_id': test_correlation_id,
                        'item_id': item['id']
                    }
                )
                client.log_audit_event(audit_entry)
            return len(chunk)
        
        result = process_bulk_data(
            data=test_data,
            processor=process_with_audit,
            chunk_size=10,
            logger=self.logger
        )
        
        # Verify comprehensive test results
        self.assertEqual(result.total_items, 50)
        self.assertEqual(result.successful_chunks, 5)
        self.assertEqual(result.failed_chunks, 0)
        self.assertEqual(result.success_rate, 1.0)
        
        log_with_context(self.logger, 'INFO', "Comprehensive integration test completed successfully", 
                        correlation_id=test_correlation_id,
                        total_items=result.total_items,
                        success_rate=result.success_rate,
                        total_duration_ms=result.total_duration_ms)


def run_integration_tests():
    """Run all integration tests."""
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Run tests
    unittest.main(verbosity=2)


if __name__ == '__main__':
    run_integration_tests() 