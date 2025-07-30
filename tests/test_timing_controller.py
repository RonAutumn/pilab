"""
Tests for timing controller functionality.
Tests timing accuracy, drift correction, and system clock adjustment detection.
"""

import unittest
import time
import logging
from unittest.mock import patch, MagicMock
from pathlib import Path
import sys

# Add src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from timing_controller import TimingController, TimingStats


class TestTimingController(unittest.TestCase):
    """Test cases for TimingController class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Configure logging for tests
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)
        
        # Test parameters
        self.test_interval = 1.0  # 1 second interval for faster tests
        self.max_drift_threshold = 0.5
        
    def test_initialization(self):
        """Test timing controller initialization."""
        controller = TimingController(self.test_interval, self.max_drift_threshold)
        
        self.assertEqual(controller.interval_seconds, self.test_interval)
        self.assertEqual(controller.max_drift_threshold, self.max_drift_threshold)
        self.assertEqual(controller.capture_count, 0)
        self.assertEqual(controller.drift_accumulated, 0.0)
        self.assertEqual(controller.total_drift, 0.0)
        self.assertEqual(controller.system_clock_adjustments, 0)
        
        # Check that timing is initialized
        self.assertGreater(controller.start_time, 0)
        self.assertGreater(controller.last_capture_time, 0)
        self.assertGreater(controller.next_capture_time, controller.start_time)
        
    def test_basic_timing_accuracy(self):
        """Test basic timing accuracy over multiple captures."""
        controller = TimingController(0.1)  # 100ms intervals for quick testing
        
        # Simulate multiple captures
        for i in range(5):
            # Wait for next capture
            should_capture, time_until_next = controller.wait_for_next_capture()
            self.assertTrue(should_capture)
            self.assertLessEqual(time_until_next, 0.01)  # Should be very close to 0
            
            # Simulate capture completion
            controller.capture_completed()
            
            # Check capture count
            self.assertEqual(controller.capture_count, i + 1)
        
        # Check timing statistics
        stats = controller.get_timing_stats()
        self.assertEqual(stats.capture_count, 5)
        self.assertEqual(stats.expected_interval, 0.1)
        self.assertGreater(stats.avg_interval, 0.09)  # Should be close to expected
        self.assertLess(stats.avg_interval, 0.11)
        
    def test_drift_correction(self):
        """Test drift correction functionality."""
        controller = TimingController(0.1)
        
        # Simulate captures with intentional delays to create drift
        for i in range(3):
            should_capture, _ = controller.wait_for_next_capture()
            self.assertTrue(should_capture)
            
            # Simulate processing delay
            time.sleep(0.05)  # 50ms delay
            
            controller.capture_completed()
        
        # Check that drift is being tracked
        drift_info = controller.get_drift_info()
        self.assertGreater(drift_info['total_drift'], 0)
        self.assertGreater(drift_info['current_drift'], 0)
        
        # Check that correction is being applied
        stats = controller.get_timing_stats()
        self.assertGreater(stats.drift_accumulated, 0)
        
    def test_system_clock_adjustment_detection(self):
        """Test system clock adjustment detection."""
        # Mock time.time from the beginning to avoid real time interference
        with patch('time.time') as mock_time:
            # Set initial time
            mock_time.return_value = 1000.0
            
            # Create controller with mocked time
            controller = TimingController(1.0)
            
            # Reset the last system time to avoid the initial jump detection
            controller.last_system_time = 1000.0
            
            # Simulate clock adjustment (jump of more than 1 second)
            mock_time.return_value = 1002.0
            adjustment_detected = controller._detect_system_clock_adjustment()
            
            self.assertTrue(adjustment_detected)
            self.assertEqual(controller.system_clock_adjustments, 1)
            
            # Normal time progression (no adjustment)
            mock_time.return_value = 1002.5
            adjustment_detected = controller._detect_system_clock_adjustment()
            
            self.assertFalse(adjustment_detected)
            self.assertEqual(controller.system_clock_adjustments, 1)
    
    def test_timing_statistics(self):
        """Test timing statistics collection."""
        controller = TimingController(0.1)
        
        # Perform some captures
        for i in range(3):
            should_capture, _ = controller.wait_for_next_capture()
            controller.capture_completed()
        
        # Get statistics
        stats = controller.get_timing_stats()
        
        # Verify statistics
        self.assertEqual(stats.capture_count, 3)
        self.assertEqual(stats.expected_interval, 0.1)
        self.assertGreater(stats.avg_interval, 0)
        self.assertGreater(stats.min_interval, 0)
        self.assertGreater(stats.max_interval, 0)
        self.assertEqual(len(stats.interval_history), 3)
        
    def test_drift_info_calculation(self):
        """Test drift information calculation."""
        controller = TimingController(0.1)
        
        # Perform captures with delays to create drift
        for i in range(2):
            should_capture, _ = controller.wait_for_next_capture()
            time.sleep(0.05)  # Create drift
            controller.capture_completed()
        
        drift_info = controller.get_drift_info()
        
        # Verify drift information
        self.assertIn('current_drift', drift_info)
        self.assertIn('total_drift', drift_info)
        self.assertIn('avg_drift_per_capture', drift_info)
        self.assertIn('drift_percentage', drift_info)
        self.assertIn('system_clock_adjustments', drift_info)
        
        self.assertGreater(drift_info['total_drift'], 0)
        self.assertGreater(drift_info['avg_drift_per_capture'], 0)
        
    def test_interval_adjustment(self):
        """Test dynamic interval adjustment."""
        controller = TimingController(1.0)
        
        # Check initial interval
        self.assertEqual(controller.interval_seconds, 1.0)
        
        # Adjust interval
        controller.adjust_interval(2.0)
        
        # Check new interval
        self.assertEqual(controller.interval_seconds, 2.0)
        
        # Check that sleep interval is adjusted
        self.assertEqual(controller.sleep_interval, 0.2)  # min(1.0, 2.0/10)
        
    def test_drift_reset(self):
        """Test drift reset functionality."""
        controller = TimingController(0.1)
        
        # Create some drift
        for i in range(2):
            should_capture, _ = controller.wait_for_next_capture()
            time.sleep(0.05)
            controller.capture_completed()
        
        # Verify drift exists
        initial_drift = controller.drift_accumulated
        self.assertGreater(initial_drift, 0)
        
        # Reset drift
        controller.reset_drift()
        
        # Verify drift is reset
        self.assertEqual(controller.drift_accumulated, 0.0)
        
    def test_time_until_next_calculation(self):
        """Test time until next capture calculation."""
        controller = TimingController(1.0)
        
        # Initially should be close to interval
        time_until_next = controller.get_time_until_next()
        self.assertGreater(time_until_next, 0.9)
        self.assertLess(time_until_next, 1.1)
        
        # After waiting, should be less
        time.sleep(0.5)
        time_until_next = controller.get_time_until_next()
        self.assertGreater(time_until_next, 0.4)
        self.assertLess(time_until_next, 0.6)
        
    def test_elapsed_time_calculation(self):
        """Test elapsed time calculation."""
        controller = TimingController(1.0)
        
        # Initial elapsed time should be very small
        initial_elapsed = controller.get_elapsed_time()
        self.assertGreaterEqual(initial_elapsed, 0)
        self.assertLess(initial_elapsed, 0.1)
        
        # After some time, should increase
        time.sleep(0.1)
        elapsed = controller.get_elapsed_time()
        self.assertGreater(elapsed, initial_elapsed)
        
    def test_performance_optimization(self):
        """Test performance optimization features."""
        # Test with different intervals
        intervals = [0.1, 1.0, 10.0]
        
        for interval in intervals:
            controller = TimingController(interval)
            
            # Check sleep interval calculation
            expected_sleep = min(1.0, interval / 10)
            self.assertEqual(controller.sleep_interval, expected_sleep)
            
    def test_edge_cases(self):
        """Test edge cases and error conditions."""
        # Test with very small interval
        controller = TimingController(0.01)
        self.assertEqual(controller.sleep_interval, 0.001)
        
        # Test with very large interval
        controller = TimingController(100.0)
        self.assertEqual(controller.sleep_interval, 1.0)
        
        # Test zero interval (should handle gracefully)
        with self.assertRaises(ValueError):
            controller = TimingController(0.0)
            
    def test_concurrent_access_safety(self):
        """Test that timing controller is thread-safe for basic operations."""
        import threading
        
        controller = TimingController(0.1)
        results = []
        
        def capture_worker():
            """Worker function to simulate concurrent captures."""
            for i in range(3):
                should_capture, _ = controller.wait_for_next_capture()
                if should_capture:
                    controller.capture_completed()
                    results.append(controller.capture_count)
        
        # Create multiple threads
        threads = []
        for i in range(2):
            thread = threading.Thread(target=capture_worker)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify results
        self.assertGreater(len(results), 0)
        self.assertGreater(controller.capture_count, 0)
        
    def test_logging_functionality(self):
        """Test logging functionality."""
        controller = TimingController(0.1)
        
        # Perform some captures
        for i in range(2):
            should_capture, _ = controller.wait_for_next_capture()
            controller.capture_completed()
        
        # Test timing report logging (should not raise exceptions)
        try:
            controller.log_timing_report()
        except Exception as e:
            self.fail(f"Timing report logging failed: {e}")
            
    def test_memory_efficiency(self):
        """Test memory efficiency of interval history."""
        controller = TimingController(0.1)
        
        # Perform more captures than the history limit
        for i in range(150):  # More than maxlen=100
            should_capture, _ = controller.wait_for_next_capture()
            controller.capture_completed()
        
        # Check that history is limited
        stats = controller.get_timing_stats()
        self.assertEqual(len(stats.interval_history), 100)  # Should be limited to maxlen
        
    def test_precision_accuracy(self):
        """Test precision accuracy over extended periods."""
        controller = TimingController(0.1)
        
        # Mock time.sleep to avoid triggering signal handler
        with patch('time.sleep'):
            # Simulate extended operation
            start_time = time.perf_counter()
            
            for i in range(10):
                should_capture, _ = controller.wait_for_next_capture()
                controller.capture_completed()
            
            end_time = time.perf_counter()
            total_time = end_time - start_time
            
            # Check that total time is reasonable
            expected_time = 10 * 0.1  # 10 captures * 0.1s each
            self.assertGreater(total_time, expected_time * 0.8)  # Allow some overhead
            self.assertLess(total_time, expected_time * 1.2)  # Allow some overhead


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2) 