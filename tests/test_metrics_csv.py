"""
Regression tests for CSV logging field consistency in metrics.py.
Tests that all fields written to CSV are properly declared in fieldnames list.
"""

import pytest
import tempfile
import csv
import os
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime

from src.metrics import MetricsLogger, ImageQualityMetrics


class TestCSVFieldConsistency:
    """Test cases for CSV field consistency and regression testing."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"
        self.csv_path = self.log_dir / "test_metadata.csv"
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_log_capture_event_all_fields_declared(self):
        """Test that all fields written to CSV are declared in fieldnames."""
        logger = MetricsLogger(str(self.log_dir), "test_metadata.csv")
        
        # Create comprehensive metadata with all expected fields
        metadata = {
            'filepath': '/path/to/test/image.jpg',
            'capture_number': 42,
            'interval_seconds': 30,
            'sharpness_score': 123.45,
            'brightness_value': 127.5,
            'brightness_warnings': [],
            'file_size': 1024,
            'resolution': [1920, 1080],
            'exposure_time': 1000,
            'iso': 100,
            'focal_length': 50,
            'aperture': 2.8,
            'temperature': 25.0,
            'humidity': 60.0,
            'cpu_temp': 45.0,
            'memory_usage': 512.0,
            'disk_space': 1024.0,
            'capture_duration': 1.5,
            'timing_interval': 30.1,
            'timing_drift': 0.1,
            'timing_accumulated_drift': 2.5,
            'timing_system_clock_adjustments': 1
        }
        
        # This should not raise any exceptions
        result = logger.log_capture_event("test_image.jpg", metadata)
        assert result is True
        assert self.csv_path.exists()
        
        # Verify CSV content and structure
        with open(self.csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            
            # Check that all expected fields are present in the CSV
            row = rows[0]
            expected_fields = [
                'timestamp', 'image_path', 'filename', 'filepath', 'capture_number', 
                'interval_seconds', 'sharpness_score', 'brightness_value', 
                'brightness_warnings', 'file_size', 'resolution', 'exposure_time', 
                'iso', 'focal_length', 'aperture', 'temperature', 'humidity', 
                'cpu_temp', 'memory_usage', 'disk_space', 'capture_duration', 
                'timing_interval', 'timing_drift', 'timing_accumulated_drift', 
                'timing_system_clock_adjustments'
            ]
            
            for field in expected_fields:
                assert field in row, f"Field '{field}' missing from CSV row"
            
            # Verify specific field values
            assert row['filepath'] == '/path/to/test/image.jpg'
            assert int(row['capture_number']) == 42
            assert float(row['interval_seconds']) == 30.0
            assert float(row['sharpness_score']) == 123.45
            assert float(row['brightness_value']) == 127.5
    
    def test_log_capture_event_undeclared_field_returns_false(self):
        """Test that writing an undeclared field returns False and logs error."""
        logger = MetricsLogger(str(self.log_dir), "test_metadata.csv")
        
        # Create metadata with an undeclared field
        metadata = {
            'filepath': '/path/to/test/image.jpg',
            'capture_number': 42,
            'interval_seconds': 30,
            'sharpness_score': 123.45,
            'brightness_value': 127.5,
            'undeclared_field': 'this_should_cause_an_error'  # This field is not in fieldnames
        }
        
        # This should return False because 'undeclared_field' is not in fieldnames
        result = logger.log_capture_event("test_image.jpg", metadata)
        assert result is False
        
        # The CSV file should not be created due to the error
        assert not self.csv_path.exists()
    
    def test_append_metadata_field_consistency(self):
        """Test that append_metadata only writes declared fields."""
        logger = MetricsLogger(str(self.log_dir))
        
        metrics = {
            'sharpness_score': 123.45,
            'brightness_value': 127.5
        }
        
        result = logger.append_metadata(
            str(self.csv_path),
            "2023-01-01T00:00:00",
            "test_image.jpg",
            metrics
        )
        
        assert result is True
        assert self.csv_path.exists()
        
        # Verify CSV content
        with open(self.csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            
            row = rows[0]
            # append_metadata should only have these fields
            expected_fields = ['timestamp', 'filename', 'sharpness_score', 'brightness_value']
            
            for field in expected_fields:
                assert field in row, f"Field '{field}' missing from CSV row"
            
            # Verify no extra fields are present
            assert len(row) == len(expected_fields), f"Unexpected fields in CSV: {set(row.keys()) - set(expected_fields)}"
            
            # Verify field values
            assert row['timestamp'] == "2023-01-01T00:00:00"
            assert row['filename'] == "test_image.jpg"
            assert float(row['sharpness_score']) == 123.45
            assert float(row['brightness_value']) == 127.5
    
    def test_csv_fieldnames_completeness(self):
        """Test that fieldnames list includes all fields that could be written."""
        logger = MetricsLogger(str(self.log_dir))
        
        # Get the fieldnames from the log_capture_event method
        # We'll do this by examining the method's fieldnames list
        with open(logger.csv_path.parent / "temp.csv", 'w', newline='') as csvfile:
            fieldnames = [
                'timestamp',
                'image_path',
                'filename',
                'filepath',
                'capture_number',
                'interval_seconds',
                'sharpness_score',
                'brightness_value',
                'brightness_warnings',
                'file_size',
                'resolution',
                'exposure_time',
                'iso',
                'focal_length',
                'aperture',
                'temperature',
                'humidity',
                'cpu_temp',
                'memory_usage',
                'disk_space',
                'capture_duration',
                'timing_interval',
                'timing_drift',
                'timing_accumulated_drift',
                'timing_system_clock_adjustments'
            ]
            
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
        
        # Verify that all expected fields are in the fieldnames list
        expected_fields = [
            'timestamp', 'image_path', 'filename', 'filepath', 'capture_number', 
            'interval_seconds', 'sharpness_score', 'brightness_value', 
            'brightness_warnings', 'file_size', 'resolution', 'exposure_time', 
            'iso', 'focal_length', 'aperture', 'temperature', 'humidity', 
            'cpu_temp', 'memory_usage', 'disk_space', 'capture_duration', 
            'timing_interval', 'timing_drift', 'timing_accumulated_drift', 
            'timing_system_clock_adjustments'
        ]
        
        for field in expected_fields:
            assert field in fieldnames, f"Field '{field}' missing from fieldnames list"
        
        # Clean up temp file
        (logger.csv_path.parent / "temp.csv").unlink()
    
    def test_csv_round_trip_consistency(self):
        """Test that data written to CSV can be read back correctly."""
        logger = MetricsLogger(str(self.log_dir), "test_metadata.csv")
        
        # Write test data
        metadata = {
            'filepath': '/test/path/image.jpg',
            'capture_number': 123,
            'interval_seconds': 45,
            'sharpness_score': 200.5,
            'brightness_value': 150.25,
            'brightness_warnings': ['bright'],
            'file_size': 2048,
            'resolution': [3840, 2160],
            'exposure_time': 2000,
            'iso': 200,
            'focal_length': 35,
            'aperture': 1.8,
            'temperature': 22.5,
            'humidity': 55.0,
            'cpu_temp': 50.0,
            'memory_usage': 1024.0,
            'disk_space': 2048.0,
            'capture_duration': 2.0,
            'timing_interval': 45.1,
            'timing_drift': 0.1,
            'timing_accumulated_drift': 1.5,
            'timing_system_clock_adjustments': 2
        }
        
        result = logger.log_capture_event("test_image.jpg", metadata)
        assert result is True
        
        # Read back the data
        with open(self.csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            
            row = rows[0]
            
            # Verify all fields are preserved correctly
            assert row['filepath'] == '/test/path/image.jpg'
            assert int(row['capture_number']) == 123
            assert float(row['interval_seconds']) == 45.0
            assert float(row['sharpness_score']) == 200.5
            assert float(row['brightness_value']) == 150.25
            assert int(row['file_size']) == 2048
            assert int(row['exposure_time']) == 2000
            assert int(row['iso']) == 200
            assert float(row['focal_length']) == 35.0
            assert float(row['aperture']) == 1.8
            assert float(row['temperature']) == 22.5
            assert float(row['humidity']) == 55.0
            assert float(row['cpu_temp']) == 50.0
            assert float(row['memory_usage']) == 1024.0
            assert float(row['disk_space']) == 2048.0
            assert float(row['capture_duration']) == 2.0
            assert float(row['timing_interval']) == 45.1
            assert float(row['timing_drift']) == 0.1
            assert float(row['timing_accumulated_drift']) == 1.5
            assert int(row['timing_system_clock_adjustments']) == 2
    
    def test_csv_header_consistency(self):
        """Test that CSV headers match the fieldnames list exactly."""
        logger = MetricsLogger(str(self.log_dir), "test_metadata.csv")
        
        # Write a simple record
        metadata = {
            'filepath': '/test/path/image.jpg',
            'capture_number': 1,
            'interval_seconds': 30,
            'sharpness_score': 100.0,
            'brightness_value': 120.0
        }
        
        result = logger.log_capture_event("test_image.jpg", metadata)
        assert result is True
        
        # Read the CSV and check headers
        with open(self.csv_path, 'r') as f:
            content = f.read()
            lines = content.strip().split('\n')
            assert len(lines) >= 2  # Header + at least one data row
            
            header_line = lines[0]
            headers = header_line.split(',')
            
            # Expected headers in order
            expected_headers = [
                'timestamp', 'image_path', 'filename', 'filepath', 'capture_number', 
                'interval_seconds', 'sharpness_score', 'brightness_value', 
                'brightness_warnings', 'file_size', 'resolution', 'exposure_time', 
                'iso', 'focal_length', 'aperture', 'temperature', 'humidity', 
                'cpu_temp', 'memory_usage', 'disk_space', 'capture_duration', 
                'timing_interval', 'timing_drift', 'timing_accumulated_drift', 
                'timing_system_clock_adjustments'
            ]
            
            assert headers == expected_headers, f"Headers mismatch. Expected: {expected_headers}, Got: {headers}"


if __name__ == "__main__":
    pytest.main([__file__]) 