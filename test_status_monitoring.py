#!/usr/bin/env python3
"""
Test script for Task 10: Console Status Monitoring
Tests the StatusMonitor class and enhanced console output functionality.
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from config_manager import ConfigManager


def test_status_monitor_initialization():
    """Test StatusMonitor initialization."""
    print("Testing StatusMonitor initialization...")
    
    config = ConfigManager()
    config.set('timelapse.interval_seconds', 30)
    config.set('timelapse.duration_hours', 2)
    config.set('timelapse.output_dir', 'test_output')
    
    from main import StatusMonitor
    
    monitor = StatusMonitor(config, verbose=True)
    
    # Test basic properties
    assert monitor.interval_seconds == 30
    assert monitor.duration_hours == 2
    assert monitor.output_dir == 'test_output'
    assert monitor.verbose == True
    assert monitor.capture_count == 0
    assert monitor.end_time is not None
    
    print("✓ StatusMonitor initialization successful")
    return True


def test_status_monitor_time_calculations():
    """Test time calculation methods."""
    print("Testing time calculations...")
    
    config = ConfigManager()
    config.set('timelapse.interval_seconds', 60)
    config.set('timelapse.duration_hours', 1)
    
    from main import StatusMonitor
    
    monitor = StatusMonitor(config)
    
    # Test elapsed time
    elapsed = monitor.get_elapsed_time()
    assert elapsed >= 0
    assert elapsed < 1  # Should be very small initially
    
    # Test remaining time
    remaining = monitor.get_remaining_time()
    assert remaining is not None
    assert remaining > 0
    assert remaining <= 1
    
    # Test next capture time
    next_time = monitor.get_next_capture_time()
    assert next_time > datetime.now()
    
    # Test time until next
    time_until = monitor.get_time_until_next()
    assert time_until >= 0
    assert time_until <= 60
    
    print("✓ Time calculations working correctly")
    return True


def test_status_monitor_quality_statistics():
    """Test quality statistics calculation."""
    print("Testing quality statistics...")
    
    config = ConfigManager()
    from main import StatusMonitor
    
    monitor = StatusMonitor(config)
    
    # Test empty statistics
    stats = monitor.get_quality_statistics()
    assert stats == {}
    
    # Add some test quality metrics
    test_metrics = [
        {'sharpness_score': 10.0, 'brightness_value': 50.0},
        {'sharpness_score': 15.0, 'brightness_value': 60.0},
        {'sharpness_score': 12.0, 'brightness_value': 55.0},
    ]
    
    for i, metrics in enumerate(test_metrics):
        monitor.update_capture(i + 1, metrics)
    
    # Test statistics calculation
    stats = monitor.get_quality_statistics()
    assert 'avg_sharpness' in stats
    assert 'min_sharpness' in stats
    assert 'max_sharpness' in stats
    assert 'avg_brightness' in stats
    assert 'min_brightness' in stats
    assert 'max_brightness' in stats
    
    # Verify calculations
    assert abs(stats['avg_sharpness'] - 12.33) < 0.1
    assert stats['min_sharpness'] == 10.0
    assert stats['max_sharpness'] == 15.0
    assert abs(stats['avg_brightness'] - 55.0) < 0.1
    assert stats['min_brightness'] == 50.0
    assert stats['max_brightness'] == 60.0
    
    print("✓ Quality statistics calculation working correctly")
    return True


def test_status_monitor_display_methods():
    """Test display methods (without actual output)."""
    print("Testing display methods...")
    
    config = ConfigManager()
    config.set('timelapse.interval_seconds', 30)
    config.set('timelapse.duration_hours', 1)
    
    from main import StatusMonitor
    
    monitor = StatusMonitor(config, verbose=True)
    
    # Test status line display
    current_time = datetime.now()
    monitor.display_status_line(current_time)
    
    # Test with quality metrics
    monitor.update_capture(1, {'sharpness_score': 12.5, 'brightness_value': 55.0})
    monitor.display_status_line(current_time, True, "")
    
    # Test with error
    monitor.display_status_line(current_time, False, "Test error")
    
    # Test periodic summary
    monitor.display_periodic_summary(current_time)
    
    # Test final summary
    monitor.display_final_summary(Path("test_output"))
    
    print("✓ Display methods working correctly")
    return True


def test_status_monitor_dry_run():
    """Test dry run mode."""
    print("Testing dry run mode...")
    
    config = ConfigManager()
    from main import StatusMonitor
    
    monitor = StatusMonitor(config)
    monitor.set_dry_run(True)
    
    # Verify dry run is set
    assert hasattr(monitor, 'dry_run')
    assert monitor.dry_run == True
    
    # Test status line with dry run
    current_time = datetime.now()
    monitor.display_status_line(current_time)
    
    print("✓ Dry run mode working correctly")
    return True


def test_status_monitor_capture_updates():
    """Test capture update functionality."""
    print("Testing capture updates...")
    
    config = ConfigManager()
    from main import StatusMonitor
    
    monitor = StatusMonitor(config)
    
    # Test initial state
    assert monitor.capture_count == 0
    assert monitor.last_quality_metrics is None
    
    # Test update without quality metrics
    monitor.update_capture(1)
    assert monitor.capture_count == 1
    assert monitor.last_quality_metrics is None
    
    # Test update with quality metrics
    quality_metrics = {'sharpness_score': 15.0, 'brightness_value': 60.0}
    monitor.update_capture(2, quality_metrics)
    assert monitor.capture_count == 2
    assert monitor.last_quality_metrics == quality_metrics
    
    # Test quality history
    assert len(monitor.quality_history) == 1
    assert monitor.quality_history[0] == quality_metrics
    
    print("✓ Capture updates working correctly")
    return True


def test_status_monitor_verbose_mode():
    """Test verbose mode functionality."""
    print("Testing verbose mode...")
    
    config = ConfigManager()
    config.set('timelapse.interval_seconds', 30)
    config.set('timelapse.duration_hours', 2)
    config.set('timelapse.output_dir', 'test_output')
    
    from main import StatusMonitor
    
    # Test non-verbose mode
    monitor_normal = StatusMonitor(config, verbose=False)
    assert monitor_normal.verbose == False
    
    # Test verbose mode
    monitor_verbose = StatusMonitor(config, verbose=True)
    assert monitor_verbose.verbose == True
    
    # Test periodic summary in verbose mode
    current_time = datetime.now()
    monitor_verbose.update_capture(10, {'sharpness_score': 12.0, 'brightness_value': 55.0})
    monitor_verbose.display_periodic_summary(current_time)
    
    print("✓ Verbose mode working correctly")
    return True


def test_status_monitor_integration():
    """Test integration with main system."""
    print("Testing integration with main system...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        # Create a temporary config file
        config_content = f"""timelapse:
  interval_seconds: 30
  duration_hours: 1
  output_dir: {temp_path / 'output'}
  
logging:
  log_dir: {temp_path / 'logs'}
  log_level: INFO
  csv_filename: test_metadata.csv
"""
        
        config_file = temp_path / 'test_config.yaml'
        with open(config_file, 'w') as f:
            f.write(config_content)
        
        # Test config loading and StatusMonitor creation
        config = ConfigManager(config_path=str(config_file))
        from main import StatusMonitor
        
        monitor = StatusMonitor(config, verbose=True)
        
        # Verify config integration
        assert monitor.interval_seconds == 30
        assert monitor.duration_hours == 1
        assert str(monitor.output_dir) == str(temp_path / 'output')
        
        print("✓ Integration with main system working correctly")
        return True


def test_status_monitor_edge_cases():
    """Test edge cases and error handling."""
    print("Testing edge cases...")
    
    config = ConfigManager()
    from main import StatusMonitor
    
    monitor = StatusMonitor(config)
    
    # Test with zero duration (indefinite)
    config.set('timelapse.duration_hours', 0)
    monitor_indefinite = StatusMonitor(config)
    assert monitor_indefinite.end_time is None
    assert monitor_indefinite.get_remaining_time() is None
    
    # Test with very short interval
    config.set('timelapse.interval_seconds', 1)
    monitor_fast = StatusMonitor(config)
    assert monitor_fast.interval_seconds == 1
    
    # Test quality history limit
    for i in range(60):  # More than the 50 limit
        monitor.update_capture(i + 1, {'sharpness_score': i, 'brightness_value': i})
    
    # Should only keep last 50
    assert len(monitor.quality_history) == 50
    
    print("✓ Edge cases handled correctly")
    return True


def main():
    """Run all status monitoring tests."""
    print("=== Task 10: Console Status Monitoring Tests ===\n")
    
    tests = [
        ("StatusMonitor Initialization", test_status_monitor_initialization),
        ("Time Calculations", test_status_monitor_time_calculations),
        ("Quality Statistics", test_status_monitor_quality_statistics),
        ("Display Methods", test_status_monitor_display_methods),
        ("Dry Run Mode", test_status_monitor_dry_run),
        ("Capture Updates", test_status_monitor_capture_updates),
        ("Verbose Mode", test_status_monitor_verbose_mode),
        ("Integration", test_status_monitor_integration),
        ("Edge Cases", test_status_monitor_edge_cases),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            print(f"✗ {test_name} FAILED with exception: {e}")
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 All status monitoring tests passed!")
        print("✅ Task 10 requirements are complete:")
        print("   - StatusMonitor class implemented")
        print("   - Real-time console status updates")
        print("   - Quality metrics tracking and statistics")
        print("   - Periodic summary displays")
        print("   - Verbose mode support")
        print("   - Dry run mode support")
        print("   - Comprehensive time calculations")
        print("   - Integration with main capture loop")
        return 0
    else:
        print("⚠️  Some status monitoring tests failed.")
        print("   Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 