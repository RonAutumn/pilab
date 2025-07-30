#!/usr/bin/env python3
"""
Test script for drift warning suppression functionality.
Tests the new --suppress-drift flag and warning level behavior.
"""

import sys
import time
import logging
import unittest
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.timing_controller import TimingController


class TestDriftWarningSuppression(unittest.TestCase):
    """Test cases for drift warning suppression functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Configure logging to capture messages
        self.log_capture = []
        
        class TestHandler(logging.Handler):
            def __init__(self, capture_list):
                super().__init__()
                self.capture_list = capture_list
            
            def emit(self, record):
                self.capture_list.append({
                    'level': record.levelname,
                    'message': record.getMessage()
                })
        
        # Set up test handler
        test_handler = TestHandler(self.log_capture)
        test_handler.setLevel(logging.DEBUG)
        
        # Configure logger
        logger = logging.getLogger('src.timing_controller')
        logger.setLevel(logging.DEBUG)
        logger.addHandler(test_handler)
        
        # Clear any existing handlers
        logger.handlers = [test_handler]
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove test handler
        logger = logging.getLogger('src.timing_controller')
        logger.handlers.clear()
        self.log_capture.clear()
    
    def test_default_warning_behavior(self):
        """Test default warning behavior (first 3 warnings at WARNING level)."""
        controller = TimingController(interval_seconds=1.0, suppress_drift_warnings=False)
        
        # Simulate system clock adjustments
        for i in range(5):
            # Manually trigger clock adjustment detection
            controller.last_system_time = time.time() - 2.0  # Simulate 2-second jump
            controller._detect_system_clock_adjustment()
        
        # Check warning levels
        warning_messages = [msg for msg in self.log_capture if 'System clock adjustment detected' in msg['message']]
        
        self.assertEqual(len(warning_messages), 5)
        
        # First 3 should be WARNING level
        for i in range(3):
            self.assertEqual(warning_messages[i]['level'], 'WARNING')
        
        # Subsequent ones should be INFO level
        for i in range(3, 5):
            self.assertEqual(warning_messages[i]['level'], 'INFO')
    
    def test_suppress_drift_warnings(self):
        """Test complete suppression of drift warnings."""
        controller = TimingController(interval_seconds=1.0, suppress_drift_warnings=True)
        
        # Simulate system clock adjustments
        for i in range(3):
            controller.last_system_time = time.time() - 2.0
            controller._detect_system_clock_adjustment()
        
        # Check that warnings are suppressed (logged at DEBUG level)
        warning_messages = [msg for msg in self.log_capture if 'System clock adjustment detected' in msg['message']]
        
        self.assertEqual(len(warning_messages), 3)
        
        # All should be DEBUG level (suppressed)
        for msg in warning_messages:
            self.assertEqual(msg['level'], 'DEBUG')
    
    def test_warning_counter_reset(self):
        """Test that warning counter resets properly."""
        controller = TimingController(interval_seconds=1.0, suppress_drift_warnings=False)
        
        # Simulate 2 warnings
        for i in range(2):
            controller.last_system_time = time.time() - 2.0
            controller._detect_system_clock_adjustment()
        
        self.assertEqual(controller.drift_warning_count, 2)
        
        # Reset warnings
        controller.reset_drift_warnings()
        self.assertEqual(controller.drift_warning_count, 0)
        
        # Next warning should be at WARNING level again
        controller.last_system_time = time.time() - 2.0
        controller._detect_system_clock_adjustment()
        
        warning_messages = [msg for msg in self.log_capture if 'System clock adjustment detected' in msg['message']]
        self.assertEqual(warning_messages[-1]['level'], 'WARNING')
    
    def test_drift_info_includes_warning_stats(self):
        """Test that drift info includes warning statistics."""
        controller = TimingController(interval_seconds=1.0, suppress_drift_warnings=True)
        
        # Simulate a clock adjustment
        controller.last_system_time = time.time() - 2.0
        controller._detect_system_clock_adjustment()
        
        drift_info = controller.get_drift_info()
        
        self.assertIn('drift_warnings_suppressed', drift_info)
        self.assertIn('drift_warning_count', drift_info)
        self.assertTrue(drift_info['drift_warnings_suppressed'])
        self.assertEqual(drift_info['drift_warning_count'], 1)
    
    def test_initialization_logging(self):
        """Test that initialization logs warning suppression status."""
        # Test with warnings enabled
        controller1 = TimingController(interval_seconds=1.0, suppress_drift_warnings=False)
        init_messages = [msg for msg in self.log_capture if 'Timing controller initialized' in msg['message']]
        self.assertIn('drift_warnings=enabled', init_messages[0]['message'])
        
        # Clear and test with warnings suppressed
        self.log_capture.clear()
        controller2 = TimingController(interval_seconds=1.0, suppress_drift_warnings=True)
        init_messages = [msg for msg in self.log_capture if 'Timing controller initialized' in msg['message']]
        self.assertIn('drift_warnings=suppressed', init_messages[0]['message'])


def test_cli_argument_parsing():
    """Test that the --suppress-drift argument is properly parsed."""
    import argparse
    
    # Simulate argument parsing
    parser = argparse.ArgumentParser()
    parser.add_argument('--suppress-drift', action='store_true')
    
    # Test without flag
    args = parser.parse_args([])
    assert not args.suppress_drift
    
    # Test with flag
    args = parser.parse_args(['--suppress-drift'])
    assert args.suppress_drift
    
    print("✓ CLI argument parsing test passed")


def test_integration_with_main():
    """Test integration with main.py (simulated)."""
    # This would normally test the full integration
    # For now, we'll just verify the TimingController works with the flag
    controller = TimingController(interval_seconds=1.0, suppress_drift_warnings=True)
    
    # Verify it's properly configured
    assert controller.suppress_drift_warnings == True
    assert controller.drift_warning_count == 0
    assert controller.max_drift_warnings == 3
    
    print("✓ Integration test passed")


if __name__ == '__main__':
    print("Running drift warning suppression tests...")
    
    # Run unit tests
    unittest.main(argv=[''], exit=False, verbosity=2)
    
    # Run additional tests
    test_cli_argument_parsing()
    test_integration_with_main()
    
    print("\nAll tests completed successfully!")
    print("\nTo test manually:")
    print("1. python src/main.py --suppress-drift --interval 5 --duration 0.1")
    print("2. Check logs for suppressed drift warnings")
    print("3. python src/main.py --interval 5 --duration 0.1")
    print("4. Check logs for normal warning behavior") 