#!/usr/bin/env python3
"""
Test script for Task 12: Timestamped Filename Generation
Tests the enhanced filename generation with millisecond precision and uniqueness.
"""

import os
import sys
import tempfile
import time
from pathlib import Path
from datetime import datetime

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.config_manager import ConfigManager


def test_basic_filename_generation():
    """Test basic filename generation without uniqueness check."""
    print("Testing basic filename generation...")
    
    config = ConfigManager()
    config.set('timelapse.filename_prefix', 'test')
    config.set('timelapse.image_format', 'jpg')
    config.set('timelapse.add_timestamp', True)
    
    from main import generate_filename
    
    # Test filename generation
    filename = generate_filename(config, 1)
    
    # Verify format: test_YYYYMMDD_HHMMSS_mmm_000001.jpg
    assert filename.startswith('test_')
    assert filename.endswith('.jpg')
    assert '_000001.jpg' in filename
    
    # Verify timestamp format (YYYYMMDD_HHMMSS_mmm)
    parts = filename.split('_')
    assert len(parts) >= 4
    
    # Check date part (YYYYMMDD)
    date_part = parts[1]
    assert len(date_part) == 8
    assert date_part.isdigit()
    
    # Check time part (HHMMSS)
    time_part = parts[2]
    assert len(time_part) == 6
    assert time_part.isdigit()
    
    # Check millisecond part (mmm)
    ms_part = parts[3]
    assert len(ms_part) == 3
    assert ms_part.isdigit()
    
    print("✓ Basic filename generation working correctly")
    return True


def test_filename_without_timestamp():
    """Test filename generation without timestamp."""
    print("Testing filename generation without timestamp...")
    
    config = ConfigManager()
    config.set('timelapse.filename_prefix', 'test')
    config.set('timelapse.image_format', 'png')
    config.set('timelapse.add_timestamp', False)
    
    from main import generate_filename
    
    filename = generate_filename(config, 42)
    
    # Should be: test_000042.png
    assert filename == 'test_000042.png'
    
    print("✓ Filename generation without timestamp working correctly")
    return True


def test_different_image_formats():
    """Test filename generation with different image formats."""
    print("Testing different image formats...")
    
    config = ConfigManager()
    config.set('timelapse.filename_prefix', 'test')
    config.set('timelapse.add_timestamp', True)
    
    from main import generate_filename
    
    formats = ['jpg', 'jpeg', 'png', 'bmp', 'JPG', '.jpg', 'JPEG']
    expected_extensions = ['jpg', 'jpeg', 'png', 'bmp', 'jpg', 'jpg', 'jpeg']
    
    for i, (format_input, expected_ext) in enumerate(zip(formats, expected_extensions)):
        config.set('timelapse.image_format', format_input)
        filename = generate_filename(config, i + 1)
        
        assert filename.endswith(f'.{expected_ext}')
        print(f"  ✓ Format '{format_input}' -> '{expected_ext}'")
    
    print("✓ Different image formats handled correctly")
    return True


def test_filename_uniqueness():
    """Test filename uniqueness by creating duplicate files."""
    print("Testing filename uniqueness...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        config = ConfigManager()
        config.set('timelapse.filename_prefix', 'test')
        config.set('timelapse.image_format', 'jpg')
        config.set('timelapse.add_timestamp', True)
        
        from main import generate_filename, ensure_filename_uniqueness
        
        # Create a base filename
        base_filename = 'test_20240101_120000_123_000001.jpg'
        
        # Create the first file
        first_file = temp_path / base_filename
        first_file.touch()
        
        # Test uniqueness function
        unique_filename = ensure_filename_uniqueness(base_filename, temp_path)
        
        # Should be different due to collision
        assert unique_filename != base_filename
        assert unique_filename == 'test_20240101_120000_123_000001_001.jpg'
        
        # Create the second file
        second_file = temp_path / unique_filename
        second_file.touch()
        
        # Test again - should get _002
        unique_filename2 = ensure_filename_uniqueness(base_filename, temp_path)
        assert unique_filename2 == 'test_20240101_120000_123_000001_002.jpg'
        
        print("✓ Filename uniqueness working correctly")
        return True


def test_filename_uniqueness_with_generate_filename():
    """Test filename uniqueness integrated with generate_filename."""
    print("Testing filename uniqueness with generate_filename...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        config = ConfigManager()
        config.set('timelapse.filename_prefix', 'test')
        config.set('timelapse.image_format', 'jpg')
        config.set('timelapse.add_timestamp', True)
        
        from main import generate_filename
        
        # Generate first filename
        filename1 = generate_filename(config, 1, temp_path)
        file1 = temp_path / filename1
        file1.touch()
        
        # Generate second filename with same parameters (should be unique)
        filename2 = generate_filename(config, 1, temp_path)
        file2 = temp_path / filename2
        file2.touch()
        
        # Filenames should be different
        assert filename1 != filename2
        
        # Verify both files exist
        assert file1.exists()
        assert file2.exists()
        
        print("✓ Filename uniqueness with generate_filename working correctly")
        return True


def test_millisecond_precision():
    """Test that millisecond precision is working correctly."""
    print("Testing millisecond precision...")
    
    config = ConfigManager()
    config.set('timelapse.filename_prefix', 'test')
    config.set('timelapse.image_format', 'jpg')
    config.set('timelapse.add_timestamp', True)
    
    from main import generate_filename
    
    # Generate multiple filenames quickly to test millisecond precision
    filenames = []
    for i in range(5):
        time.sleep(0.001)  # Small delay to ensure different milliseconds
        filename = generate_filename(config, i + 1)
        filenames.append(filename)
    
    # All filenames should be unique due to millisecond precision
    unique_filenames = set(filenames)
    assert len(unique_filenames) == len(filenames)
    
    # Verify millisecond format in each filename
    for filename in filenames:
        parts = filename.split('_')
        assert len(parts) >= 4
        
        # Check millisecond part (mmm)
        ms_part = parts[3]
        assert len(ms_part) == 3
        assert ms_part.isdigit()
        assert 0 <= int(ms_part) <= 999
    
    print("✓ Millisecond precision working correctly")
    return True


def test_filename_without_extension():
    """Test filename generation without file extension."""
    print("Testing filename without extension...")
    
    config = ConfigManager()
    config.set('timelapse.filename_prefix', 'test')
    config.set('timelapse.image_format', '')
    config.set('timelapse.add_timestamp', True)
    
    from main import generate_filename
    
    filename = generate_filename(config, 1)
    
    # Should not end with a dot
    assert not filename.endswith('.')
    assert '_000001' in filename
    
    print("✓ Filename without extension working correctly")
    return True


def test_error_handling():
    """Test error handling in filename generation."""
    print("Testing error handling...")
    
    config = ConfigManager()
    
    from main import generate_filename
    
    # Test with invalid config (should use fallback)
    try:
        filename = generate_filename(config, 1)
        # Should still generate a valid filename
        assert filename.startswith('timelapse_')
        assert filename.endswith('.jpg')
        assert '_000001.jpg' in filename
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False
    
    print("✓ Error handling working correctly")
    return True


def test_uniqueness_edge_cases():
    """Test edge cases in filename uniqueness."""
    print("Testing uniqueness edge cases...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        from main import ensure_filename_uniqueness
        
        # Test with filename without extension
        base_filename = 'test_file'
        unique_filename = ensure_filename_uniqueness(base_filename, temp_path)
        assert unique_filename == base_filename
        
        # Create the file
        file1 = temp_path / base_filename
        file1.touch()
        
        # Test again - should get _001
        unique_filename2 = ensure_filename_uniqueness(base_filename, temp_path)
        assert unique_filename2 == 'test_file_001'
        
        # Create files to test counter behavior
        for i in range(1, 5):  # Create files to test counter
            test_file = temp_path / f'test_file_{i:03d}'
            test_file.touch()
        
        # Test normal counter behavior - should get _005
        unique_filename3 = ensure_filename_uniqueness(base_filename, temp_path)
        assert unique_filename3 == 'test_file_005'
        
        # Create the _005 file to force next iteration
        overflow_file = temp_path / 'test_file_005'
        overflow_file.touch()
        
        # Test next counter - should get _006
        unique_filename4 = ensure_filename_uniqueness(base_filename, temp_path)
        assert unique_filename4 == 'test_file_006'
        
        # Create the _006 file too
        overflow_file2 = temp_path / 'test_file_006'
        overflow_file2.touch()
        
        # Test next counter - should get _007
        unique_filename5 = ensure_filename_uniqueness(base_filename, temp_path)
        assert unique_filename5 == 'test_file_007'
        
        print("✓ Uniqueness edge cases handled correctly")
        return True


def test_integration_with_config():
    """Test integration with configuration system."""
    print("Testing integration with configuration...")
    
    config = ConfigManager()
    
    # Test default values
    from main import generate_filename
    
    filename = generate_filename(config, 1)
    
    # Should use default prefix 'timelapse'
    assert filename.startswith('timelapse_')
    
    # Test custom configuration
    config.set('timelapse.filename_prefix', 'custom_prefix')
    config.set('timelapse.image_format', 'png')
    config.set('timelapse.add_timestamp', False)
    
    filename2 = generate_filename(config, 1)
    assert filename2 == 'custom_prefix_000001.png'
    
    print("✓ Integration with configuration working correctly")
    return True


def test_performance():
    """Test performance of filename generation."""
    print("Testing performance...")
    
    config = ConfigManager()
    config.set('timelapse.filename_prefix', 'perf_test')
    config.set('timelapse.image_format', 'jpg')
    config.set('timelapse.add_timestamp', True)
    
    from main import generate_filename
    
    import time
    
    # Test generation speed
    start_time = time.time()
    for i in range(100):
        filename = generate_filename(config, i + 1)
    end_time = time.time()
    
    generation_time = end_time - start_time
    print(f"  Generated 100 filenames in {generation_time:.3f} seconds")
    
    # Should be reasonably fast (less than 1 second for 100 filenames)
    assert generation_time < 1.0
    
    print("✓ Performance is acceptable")
    return True


def main():
    """Run all filename generation tests."""
    print("=== Task 12: Timestamped Filename Generation Tests ===\n")
    
    tests = [
        ("Basic Filename Generation", test_basic_filename_generation),
        ("Filename Without Timestamp", test_filename_without_timestamp),
        ("Different Image Formats", test_different_image_formats),
        ("Filename Uniqueness", test_filename_uniqueness),
        ("Filename Uniqueness with generate_filename", test_filename_uniqueness_with_generate_filename),
        ("Millisecond Precision", test_millisecond_precision),
        ("Filename Without Extension", test_filename_without_extension),
        ("Error Handling", test_error_handling),
        ("Uniqueness Edge Cases", test_uniqueness_edge_cases),
        ("Integration with Config", test_integration_with_config),
        ("Performance", test_performance),
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
        print("🎉 All filename generation tests passed!")
        print("✅ Task 12 requirements are complete:")
        print("   - Millisecond precision timestamp generation")
        print("   - Filename uniqueness with counter fallback")
        print("   - Support for different image formats")
        print("   - Integration with configuration system")
        print("   - Error handling and fallback mechanisms")
        print("   - Performance optimization")
        print("   - Edge case handling")
        return 0
    else:
        print("⚠️  Some filename generation tests failed.")
        print("   Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main()) 