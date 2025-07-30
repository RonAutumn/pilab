#!/usr/bin/env python3
"""
Test runner for CinePi Live Preview functionality.

Provides an easy way to run preview tests with different options.
"""

import sys
import argparse
import subprocess
from pathlib import Path


def run_tests_with_coverage():
    """Run tests with coverage reporting."""
    try:
        # Check if coverage is available
        import coverage
        print("Running tests with coverage...")
        
        # Start coverage
        cov = coverage.Coverage()
        cov.start()
        
        # Run tests
        from test_preview import run_preview_tests
        success = run_preview_tests()
        
        # Stop coverage and generate report
        cov.stop()
        cov.save()
        
        print("\nCoverage Report:")
        cov.report()
        
        # Generate HTML report
        cov.html_report(directory='htmlcov')
        print(f"\nHTML coverage report generated in: htmlcov/")
        
        return success
        
    except ImportError:
        print("Coverage not available. Install with: pip install coverage")
        return run_basic_tests()


def run_basic_tests():
    """Run basic tests without coverage."""
    print("Running basic tests...")
    from test_preview import run_preview_tests
    return run_preview_tests()


def run_specific_test(test_name):
    """Run a specific test class or method."""
    print(f"Running specific test: {test_name}")
    
    # Import specific test classes
    from test_preview import (
        TestFrameDispatcher, TestPreviewConfiguration, TestFlaskRoutes,
        TestPreviewIntegration, TestPreviewErrorHandling, TestPreviewThreadSafety,
        TestPreviewSignalHandling
    )
    
    # Create test suite for specific test
    import unittest
    test_suite = unittest.TestSuite()
    
    # Map test names to classes
    test_classes = {
        'TestFrameDispatcher': TestFrameDispatcher,
        'TestPreviewConfiguration': TestPreviewConfiguration,
        'TestFlaskRoutes': TestFlaskRoutes,
        'TestPreviewIntegration': TestPreviewIntegration,
        'TestPreviewErrorHandling': TestPreviewErrorHandling,
        'TestPreviewThreadSafety': TestPreviewThreadSafety,
        'TestPreviewSignalHandling': TestPreviewSignalHandling
    }
    
    # Try to load the specific test
    try:
        if '.' in test_name:
            # Specific test method
            class_name, method_name = test_name.split('.')
            test_class = test_classes[class_name]
            test_suite.addTest(test_class(method_name))
        else:
            # Test class
            test_class = test_classes[test_name]
            tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
            test_suite.addTests(tests)
    except KeyError:
        print(f"Test '{test_name}' not found!")
        return False
    
    # Run the test
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    return result.wasSuccessful()


def list_available_tests():
    """List all available test classes and methods."""
    print("Available test classes:")
    print("-" * 30)
    
    # Import specific test classes
    from test_preview import (
        TestFrameDispatcher, TestPreviewConfiguration, TestFlaskRoutes,
        TestPreviewIntegration, TestPreviewErrorHandling, TestPreviewThreadSafety,
        TestPreviewSignalHandling
    )
    
    test_classes = [
        ('TestFrameDispatcher', TestFrameDispatcher),
        ('TestPreviewConfiguration', TestPreviewConfiguration), 
        ('TestFlaskRoutes', TestFlaskRoutes),
        ('TestPreviewIntegration', TestPreviewIntegration),
        ('TestPreviewErrorHandling', TestPreviewErrorHandling),
        ('TestPreviewThreadSafety', TestPreviewThreadSafety),
        ('TestPreviewSignalHandling', TestPreviewSignalHandling)
    ]
    
    for class_name, test_class in test_classes:
        print(f"\n{class_name}:")
        methods = [method for method in dir(test_class) if method.startswith('test_')]
        for method in methods:
            print(f"  - {class_name}.{method}")


def check_dependencies():
    """Check if all required dependencies are available."""
    print("Checking dependencies...")
    
    dependencies = {
        'unittest': 'Built-in',
        'tempfile': 'Built-in', 
        'shutil': 'Built-in',
        'os': 'Built-in',
        'sys': 'Built-in',
        'time': 'Built-in',
        'threading': 'Built-in',
        'json': 'Built-in',
        'yaml': 'PyYAML',
        'pathlib': 'Built-in',
        'unittest.mock': 'Built-in',
        'io': 'Built-in'
    }
    
    missing = []
    available = []
    
    for module, package in dependencies.items():
        try:
            __import__(module)
            available.append(f"✅ {module} ({package})")
        except ImportError:
            missing.append(f"❌ {module} ({package})")
    
    print("\nAvailable dependencies:")
    for dep in available:
        print(f"  {dep}")
    
    if missing:
        print("\nMissing dependencies:")
        for dep in missing:
            print(f"  {dep}")
        print("\nInstall missing dependencies with:")
        print("  pip install PyYAML")
        return False
    else:
        print("\n✅ All dependencies available!")
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test runner for CinePi Live Preview functionality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_preview_tests.py                    # Run all tests
  python run_preview_tests.py --coverage         # Run with coverage
  python run_preview_tests.py --test TestFrameDispatcher  # Run specific test class
  python run_preview_tests.py --test TestFrameDispatcher.test_frame_dispatcher_initialization  # Run specific test
  python run_preview_tests.py --list             # List all available tests
  python run_preview_tests.py --check-deps       # Check dependencies
        """
    )
    
    parser.add_argument(
        '--coverage', action='store_true',
        help='Run tests with coverage reporting'
    )
    
    parser.add_argument(
        '--test', type=str,
        help='Run a specific test class or method (e.g., TestFrameDispatcher or TestFrameDispatcher.test_method)'
    )
    
    parser.add_argument(
        '--list', action='store_true',
        help='List all available test classes and methods'
    )
    
    parser.add_argument(
        '--check-deps', action='store_true',
        help='Check if all required dependencies are available'
    )
    
    parser.add_argument(
        '--verbose', '-v', action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Check dependencies first
    if not check_dependencies():
        print("\nPlease install missing dependencies before running tests.")
        sys.exit(1)
    
    # Handle different options
    if args.list:
        list_available_tests()
        return
    
    if args.check_deps:
        return  # Already checked above
    
    if args.test:
        success = run_specific_test(args.test)
    elif args.coverage:
        success = run_tests_with_coverage()
    else:
        success = run_basic_tests()
    
    # Exit with appropriate code
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)


if __name__ == '__main__':
    main() 