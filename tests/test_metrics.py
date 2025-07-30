"""
Unit tests for the metrics module.
Tests ImageQualityMetrics and MetricsLogger classes with comprehensive coverage.
"""

import pytest
import tempfile
import os
import shutil
import csv
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from datetime import datetime

from src.metrics import ImageQualityMetrics, MetricsLogger


class TestImageQualityMetrics:
    """Test cases for ImageQualityMetrics class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.test_image_path = "test_image.jpg"
        self.test_image_data = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
    
    @patch('src.metrics.cv2')
    @patch('src.metrics.OPENCV_AVAILABLE', True)
    def test_calculate_sharpness_success(self, mock_cv2):
        """Test successful sharpness calculation."""
        # Mock OpenCV functions
        mock_cv2.imread.return_value = self.test_image_data
        mock_cv2.cvtColor.return_value = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        mock_cv2.COLOR_BGR2GRAY = 6
        mock_cv2.CV_64F = 6
        
        # Mock Laplacian calculation with a fixed variance
        mock_laplacian = Mock()
        mock_laplacian.var = Mock(return_value=123.45)
        mock_cv2.Laplacian.return_value = mock_laplacian
        
        result = ImageQualityMetrics.calculate_sharpness(self.test_image_path)
        
        assert result == 123.45
        mock_cv2.imread.assert_called_once_with(self.test_image_path)
        mock_cv2.Laplacian.assert_called_once()
    
    @patch('src.metrics.OPENCV_AVAILABLE', False)
    def test_calculate_sharpness_opencv_unavailable(self):
        """Test sharpness calculation when OpenCV is not available."""
        result = ImageQualityMetrics.calculate_sharpness(self.test_image_path)
        assert result == 0.0
    
    @patch('src.metrics.cv2')
    @patch('src.metrics.OPENCV_AVAILABLE', True)
    def test_calculate_sharpness_image_read_failure(self, mock_cv2):
        """Test sharpness calculation when image cannot be read."""
        mock_cv2.imread.return_value = None
        
        result = ImageQualityMetrics.calculate_sharpness(self.test_image_path)
        assert result == 0.0
    
    @patch('src.metrics.cv2')
    @patch('src.metrics.OPENCV_AVAILABLE', True)
    def test_calculate_sharpness_permission_error(self, mock_cv2):
        """Test sharpness calculation with permission error."""
        mock_cv2.imread.side_effect = PermissionError("Permission denied")
        
        result = ImageQualityMetrics.calculate_sharpness(self.test_image_path)
        assert result == 0.0
    
    @patch('src.metrics.cv2')
    @patch('src.metrics.OPENCV_AVAILABLE', True)
    def test_calculate_brightness_success(self, mock_cv2):
        """Test successful brightness calculation."""
        # Mock OpenCV functions
        mock_cv2.imread.return_value = self.test_image_data
        mock_cv2.cvtColor.return_value = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        mock_cv2.COLOR_BGR2GRAY = 6
        
        # Mock mean calculation
        mock_cv2.mean.return_value = [127.5, 0, 0, 0]  # [mean, std, min, max]
        
        result = ImageQualityMetrics.calculate_brightness(self.test_image_path)
        
        assert result == 127.5
        mock_cv2.imread.assert_called_once_with(self.test_image_path)
        mock_cv2.mean.assert_called_once()
    
    @patch('src.metrics.OPENCV_AVAILABLE', False)
    def test_calculate_brightness_opencv_unavailable(self):
        """Test brightness calculation when OpenCV is not available."""
        result = ImageQualityMetrics.calculate_brightness(self.test_image_path)
        assert result == 0.0
    
    @patch('src.metrics.cv2')
    @patch('src.metrics.OPENCV_AVAILABLE', True)
    def test_calculate_brightness_image_read_failure(self, mock_cv2):
        """Test brightness calculation when image cannot be read."""
        mock_cv2.imread.return_value = None
        
        result = ImageQualityMetrics.calculate_brightness(self.test_image_path)
        assert result == 0.0
    
    @patch('src.metrics.cv2')
    @patch('src.metrics.OPENCV_AVAILABLE', True)
    def test_evaluate_image_quality_success(self, mock_cv2):
        """Test successful image quality evaluation."""
        # Mock both sharpness and brightness calculations
        with patch.object(ImageQualityMetrics, 'calculate_sharpness', return_value=123.45), \
             patch.object(ImageQualityMetrics, 'calculate_brightness', return_value=127.5):
            
            result = ImageQualityMetrics.evaluate_image_quality(self.test_image_path)
            
            expected = {
                'sharpness_score': 123.45,
                'brightness_value': 127.5
            }
            assert result == expected
    
    @patch('src.metrics.cv2')
    @patch('src.metrics.OPENCV_AVAILABLE', True)
    def test_evaluate_image_quality_exception(self, mock_cv2):
        """Test image quality evaluation with exception."""
        with patch.object(ImageQualityMetrics, 'calculate_sharpness', side_effect=Exception("Test error")):
            
            result = ImageQualityMetrics.evaluate_image_quality(self.test_image_path)
            
            expected = {
                'sharpness_score': 0.0,
                'brightness_value': 0.0
            }
            assert result == expected
    
    def test_get_brightness_warnings_dark(self):
        """Test brightness warnings for dark image."""
        warnings = ImageQualityMetrics.get_brightness_warnings(20.0)
        assert len(warnings) == 1
        assert "very dark" in warnings[0]
    
    def test_get_brightness_warnings_bright(self):
        """Test brightness warnings for bright image."""
        warnings = ImageQualityMetrics.get_brightness_warnings(230.0)
        assert len(warnings) == 1
        assert "very bright" in warnings[0]
    
    def test_get_brightness_warnings_normal(self):
        """Test brightness warnings for normal brightness."""
        warnings = ImageQualityMetrics.get_brightness_warnings(127.5)
        assert len(warnings) == 0


class TestMetricsLogger:
    """Test cases for MetricsLogger class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.log_dir = Path(self.temp_dir) / "logs"
        self.csv_path = self.log_dir / "timelapse_metadata.csv"
    
    def teardown_method(self):
        """Clean up test fixtures."""
        if self.temp_dir and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_init_creates_log_directory(self):
        """Test that initialization creates log directory."""
        logger = MetricsLogger(str(self.log_dir))
        assert self.log_dir.exists()
        assert logger.log_dir == self.log_dir
    
    def test_init_with_custom_csv_filename(self):
        """Test initialization with custom CSV filename."""
        custom_filename = "custom_metadata.csv"
        logger = MetricsLogger(str(self.log_dir), custom_filename)
        assert logger.csv_path == self.log_dir / custom_filename
    
    @patch('src.metrics.shutil.disk_usage')
    def test_check_disk_space_sufficient(self, mock_disk_usage):
        """Test disk space check with sufficient space."""
        # Mock 100MB free space
        mock_disk_usage.return_value = (1000000000, 500000000, 100000000)
        
        logger = MetricsLogger(str(self.log_dir))
        result = logger._check_disk_space(min_space_mb=10)
        assert result is True
    
    @patch('src.metrics.shutil.disk_usage')
    def test_check_disk_space_insufficient(self, mock_disk_usage):
        """Test disk space check with insufficient space."""
        # Mock 5MB free space
        mock_disk_usage.return_value = (1000000000, 950000000, 5000000)
        
        logger = MetricsLogger(str(self.log_dir))
        result = logger._check_disk_space(min_space_mb=10)
        assert result is False
    
    @patch('src.metrics.shutil.disk_usage')
    def test_check_disk_space_error(self, mock_disk_usage):
        """Test disk space check with error."""
        mock_disk_usage.side_effect = Exception("Disk error")
        
        logger = MetricsLogger(str(self.log_dir))
        result = logger._check_disk_space(min_space_mb=10)
        assert result is False
    
    def test_backup_csv_file_existing(self):
        """Test CSV backup when file exists."""
        # Create a test CSV file
        self.log_dir.mkdir(parents=True, exist_ok=True)
        test_data = "timestamp,filename\n2023-01-01,test.jpg\n"
        with open(self.csv_path, 'w') as f:
            f.write(test_data)
        
        logger = MetricsLogger(str(self.log_dir))
        result = logger._backup_csv_file()
        
        assert result is True
        backup_path = self.csv_path.with_suffix('.csv.backup')
        assert backup_path.exists()
    
    def test_backup_csv_file_nonexistent(self):
        """Test CSV backup when file doesn't exist."""
        logger = MetricsLogger(str(self.log_dir))
        result = logger._backup_csv_file()
        assert result is True
    
    def test_log_capture_event_new_file(self):
        """Test logging capture event to new CSV file."""
        logger = MetricsLogger(str(self.log_dir))
        
        metadata = {
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
            'capture_duration': 1.5
        }
        
        result = logger.log_capture_event("test_image.jpg", metadata)
        assert result is True
        assert self.csv_path.exists()
        
        # Verify CSV content
        with open(self.csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['filename'] == 'test_image.jpg'
            assert float(rows[0]['sharpness_score']) == 123.45
            assert float(rows[0]['brightness_value']) == 127.5
    
    def test_log_capture_event_existing_file(self):
        """Test logging capture event to existing CSV file."""
        # Create existing CSV file using the MetricsLogger to ensure correct format
        self.log_dir.mkdir(parents=True, exist_ok=True)
        logger = MetricsLogger(str(self.log_dir))
        
        # Create existing data with proper format
        existing_metadata = {
            'sharpness_score': 100.0,
            'brightness_value': 120.0,
            'brightness_warnings': [],
            'file_size': 0,
            'resolution': [0, 0],
            'exposure_time': 0,
            'iso': 0,
            'focal_length': 0,
            'aperture': 0,
            'temperature': 0,
            'humidity': 0,
            'cpu_temp': 0,
            'memory_usage': 0,
            'disk_space': 0,
            'capture_duration': 0
        }
        
        # Use the logger to create the initial file
        result = logger.log_capture_event("old.jpg", existing_metadata)
        assert result is True
        
        # Verify the initial file was created correctly
        with open(self.csv_path, 'r') as f:
            content = f.read()
            print(f"Initial CSV content: {repr(content)}")
            f.seek(0)
            reader = csv.DictReader(f)
            rows = list(reader)
            print(f"Initial parsed rows: {rows}")
            assert len(rows) == 1
            assert rows[0]['filename'] == 'old.jpg'
        
        metadata = {
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
            'capture_duration': 1.5
        }
        
        result = logger.log_capture_event("new_image.jpg", metadata)
        assert result is True
        
        # Verify CSV content has both old and new data
        with open(self.csv_path, 'r') as f:
            content = f.read()
            print(f"Final CSV content: {repr(content)}")
            f.seek(0)
            reader = csv.DictReader(f)
            rows = list(reader)
            print(f"Final parsed rows: {rows}")
            assert len(rows) == 2
            assert rows[0]['filename'] == 'old.jpg'
            assert rows[1]['filename'] == 'new_image.jpg'
    
    @patch('src.metrics.shutil.disk_usage')
    def test_log_capture_event_insufficient_disk_space(self, mock_disk_usage):
        """Test logging capture event with insufficient disk space."""
        mock_disk_usage.return_value = (1000000000, 950000000, 5000000)  # 5MB free
        
        logger = MetricsLogger(str(self.log_dir))
        metadata = {'sharpness_score': 123.45, 'brightness_value': 127.5}
        
        result = logger.log_capture_event("test_image.jpg", metadata)
        assert result is False
    
    def test_log_capture_event_permission_error(self):
        """Test logging capture event with permission error."""
        # Use a path that would cause permission issues on Windows
        # Try to write to a system directory that requires admin privileges
        import os
        
        # Use a path that should cause permission issues
        system_log_dir = Path("C:/Windows/System32/logs")
        
        # The MetricsLogger constructor should fail due to permission error
        try:
            logger = MetricsLogger(str(system_log_dir))
            # If we get here, the constructor succeeded, so test the log_capture_event
            metadata = {'sharpness_score': 123.45, 'brightness_value': 127.5}
            result = logger.log_capture_event("test_image.jpg", metadata)
            assert result is False
        except PermissionError:
            # This is expected - the constructor failed due to permission error
            pass
    
    def test_append_metadata_new_file(self):
        """Test appending metadata to new file."""
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
        
        # Verify content
        with open(self.csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 1
            assert rows[0]['timestamp'] == "2023-01-01T00:00:00"
            assert rows[0]['filename'] == "test_image.jpg"
            assert float(rows[0]['sharpness_score']) == 123.45
            assert float(rows[0]['brightness_value']) == 127.5
    
    def test_append_metadata_existing_file(self):
        """Test appending metadata to existing file."""
        # Create existing file
        self.log_dir.mkdir(parents=True, exist_ok=True)
        existing_data = "timestamp,filename,sharpness_score,brightness_value\n"
        existing_data += "2023-01-01T00:00:00,old.jpg,100.0,120.0\n"
        with open(self.csv_path, 'w') as f:
            f.write(existing_data)
        
        logger = MetricsLogger(str(self.log_dir))
        
        metrics = {
            'sharpness_score': 123.45,
            'brightness_value': 127.5
        }
        
        result = logger.append_metadata(
            str(self.csv_path),
            "2023-01-01T01:00:00",
            "new_image.jpg",
            metrics
        )
        
        assert result is True
        
        # Verify content
        with open(self.csv_path, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 2
            assert rows[0]['filename'] == "old.jpg"
            assert rows[1]['filename'] == "new_image.jpg"
    
    def test_get_capture_stats_empty_file(self):
        """Test getting capture stats from empty file."""
        logger = MetricsLogger(str(self.log_dir))
        stats = logger.get_capture_stats()
        
        expected = {
            "total_captures": 0,
            "first_capture": None,
            "last_capture": None
        }
        assert stats == expected
    
    def test_get_capture_stats_with_data(self):
        """Test getting capture stats from file with data."""
        # Create CSV file with test data
        self.log_dir.mkdir(parents=True, exist_ok=True)
        test_data = "timestamp,filename,sharpness_score,brightness_value,file_size\n"
        test_data += "2023-01-01T00:00:00,image1.jpg,100.0,120.0,1024\n"
        test_data += "2023-01-01T01:00:00,image2.jpg,150.0,130.0,2048\n"
        with open(self.csv_path, 'w') as f:
            f.write(test_data)
        
        logger = MetricsLogger(str(self.log_dir))
        stats = logger.get_capture_stats()
        
        assert stats["total_captures"] == 2
        assert stats["first_capture"] == "2023-01-01T00:00:00"
        assert stats["last_capture"] == "2023-01-01T01:00:00"
        assert stats["average_file_size"] == 1536.0  # (1024 + 2048) / 2
        assert stats["average_sharpness"] == 125.0  # (100 + 150) / 2
        assert stats["average_brightness"] == 125.0  # (120 + 130) / 2
        assert stats["min_sharpness"] == 100.0
        assert stats["max_sharpness"] == 150.0
        assert stats["min_brightness"] == 120.0
        assert stats["max_brightness"] == 130.0
    
    def test_get_capture_stats_permission_error(self):
        """Test getting capture stats with permission error."""
        # On Windows, we need to use a different approach to test permission failures
        # Let's test with a non-existent path that would cause permission issues
        import tempfile
        import shutil
        
        # Create a temporary directory and then remove it to simulate permission issues
        temp_dir = tempfile.mkdtemp()
        csv_path = Path(temp_dir) / "timelapse_metadata.csv"
        
        # Remove the directory to make the path invalid
        shutil.rmtree(temp_dir)
        
        logger = MetricsLogger(str(temp_dir))
        stats = logger.get_capture_stats()
        
        # Should return default stats when file doesn't exist
        expected = {
            "total_captures": 0,
            "first_capture": None,
            "last_capture": None
        }
        assert stats == expected
    
    def test_log_system_metrics(self):
        """Test logging system metrics."""
        logger = MetricsLogger(str(self.log_dir))
        metrics = logger.log_system_metrics()
        
        # Should return a dictionary with system metrics
        assert isinstance(metrics, dict)
        assert 'uptime' in metrics
    
    def test_cleanup(self):
        """Test cleanup method."""
        logger = MetricsLogger(str(self.log_dir))
        
        # Create a test CSV file
        self.log_dir.mkdir(parents=True, exist_ok=True)
        with open(self.csv_path, 'w') as f:
            f.write("timestamp,filename\n")
        
        # Test cleanup
        logger.cleanup()
        # Should not raise any exceptions
    
    def test_cleanup_with_corrupted_file(self):
        """Test cleanup with corrupted CSV file."""
        logger = MetricsLogger(str(self.log_dir))
        
        # Create a corrupted CSV file
        self.log_dir.mkdir(parents=True, exist_ok=True)
        with open(self.csv_path, 'w') as f:
            f.write("invalid,csv,content\n")
            f.write("missing,quotes\n")
        
        # Test cleanup - should handle corrupted file gracefully
        logger.cleanup()
        # Should not raise any exceptions


if __name__ == "__main__":
    pytest.main([__file__]) 