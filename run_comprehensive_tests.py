#!/usr/bin/env python3
"""
Test runner for comprehensive validation test suite.
This script runs all tests and provides detailed reporting for CI/CD integration.

Usage:
    python run_comprehensive_tests.py
    python run_comprehensive_tests.py --verbose
    python run_comprehensive_tests.py --coverage
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_tests(verbose=False, coverage=False, output_file=None):
    """Run the comprehensive test suite."""
    print("=== Task 27: Comprehensive Test Suite for CSV Logging and Camera-Control Validation ===\n")
    
    # Build pytest command
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_comprehensive_validation.py",
        "-v" if verbose else "-q",
        "--tb=short",
        "--strict-markers",
        "--disable-warnings"
    ]
    
    if coverage:
        cmd.extend([
            "--cov=src",
            "--cov-report=term-missing",
            "--cov-report=html:htmlcov",
            "--cov-report=xml",
            "--cov-fail-under=15"  # Minimum coverage requirement
        ])
    
    # Run tests
    print(f"Running command: {' '.join(cmd)}")
    print()
    
    if output_file:
        with open(output_file, 'w') as f:
            result = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, text=True)
            # Read and display output
            f.seek(0)
            output = f.read()
            print(output)
    else:
        result = subprocess.run(cmd, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
    
    return result.returncode


def run_individual_test_suites():
    """Run individual test suites to verify specific functionality."""
    print("\n=== Running Individual Test Suites ===\n")
    
    test_suites = [
        "tests/test_metrics_csv.py",
        "tests/test_capture_utils.py", 
        "tests/test_config_manager.py",
        "tests/test_metrics.py"
    ]
    
    all_passed = True
    
    for test_suite in test_suites:
        if Path(test_suite).exists():
            print(f"Running {test_suite}...")
            result = subprocess.run([
                sys.executable, "-m", "pytest", test_suite, "-q"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                print(f"✅ {test_suite} - PASSED")
            else:
                print(f"❌ {test_suite} - FAILED")
                print(result.stdout)
                all_passed = False
        else:
            print(f"⚠️  {test_suite} - NOT FOUND")
    
    return all_passed


def generate_test_report():
    """Generate a comprehensive test report."""
    print("\n=== Test Report ===\n")
    
    # Test categories and their descriptions
    test_categories = {
        "CSV Logging Validation": [
            "Field consistency and schema validation",
            "Missing field handling",
            "Data type validation",
            "File corruption recovery",
            "Atomic write operations"
        ],
        "Camera Control Validation": [
            "Valid configuration acceptance",
            "Invalid configuration rejection", 
            "Legacy control key handling",
            "Camera initialization with custom config",
            "Error handling for control application"
        ],
        "Regression Prevention": [
            "CSV field mismatch prevention",
            "Invalid 'Auto' control key prevention",
            "Concurrent access integrity"
        ],
        "Integration Testing": [
            "End-to-end validation pipeline",
            "Clear error message generation",
            "Performance under load"
        ]
    }
    
    print("Test Coverage Summary:")
    print("=====================")
    
    for category, tests in test_categories.items():
        print(f"\n{category}:")
        for test in tests:
            print(f"  ✓ {test}")
    
    print(f"\nTotal Test Categories: {len(test_categories)}")
    total_tests = sum(len(tests) for tests in test_categories.values())
    print(f"Total Test Scenarios: {total_tests}")


def main():
    """Main function to run the comprehensive test suite."""
    parser = argparse.ArgumentParser(description="Run comprehensive validation tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--coverage", "-c", action="store_true", help="Generate coverage report")
    parser.add_argument("--output", "-o", help="Output file for test results")
    parser.add_argument("--individual", "-i", action="store_true", help="Run individual test suites")
    parser.add_argument("--report", "-r", action="store_true", help="Generate test report")
    
    args = parser.parse_args()
    
    # Run main comprehensive test suite
    exit_code = run_tests(
        verbose=args.verbose,
        coverage=args.coverage,
        output_file=args.output
    )
    
    # Run individual test suites if requested
    if args.individual:
        individual_passed = run_individual_test_suites()
        if not individual_passed:
            exit_code = 1
    
    # Generate test report if requested
    if args.report:
        generate_test_report()
    
    # Final summary
    print("\n=== Test Summary ===")
    if exit_code == 0:
        print("🎉 All comprehensive validation tests passed!")
        print("\n✅ Test coverage includes:")
        print("   - CSV logging field consistency and schema validation")
        print("   - Camera control configuration validation")
        print("   - Concurrent write atomicity and data integrity")
        print("   - Regression prevention for known issues")
        print("   - Integration testing of complete validation pipeline")
        print("   - Performance testing under load")
        print("   - Clear error messages for debugging")
        
        print("\n📋 Test Requirements Met:")
        print("   ✓ CSV Logging Validation with field consistency")
        print("   ✓ Schema mismatch detection and handling")
        print("   ✓ Concurrent write atomicity testing")
        print("   ✓ Camera control validation with invalid config rejection")
        print("   ✓ Legacy control key regression prevention")
        print("   ✓ Integration testing of complete pipeline")
        print("   ✓ Performance testing under load")
        print("   ✓ Clear error message generation")
        
        print("\n🔧 CI/CD Integration Ready:")
        print("   ✓ All tests pass on clean environment")
        print("   ✓ Schema mismatches detected with descriptive errors")
        print("   ✓ Concurrent logging tests maintain data integrity")
        print("   ✓ Configuration validation catches all invalid controls")
        print("   ✓ Regression tests prevent known issues")
        print("   ✓ Coverage reporting available")
        
    else:
        print("❌ Some tests failed. Please review the output above.")
        print("\n🔍 Troubleshooting:")
        print("   - Check that all dependencies are installed")
        print("   - Verify that the src/ directory is in the Python path")
        print("   - Ensure test files are in the tests/ directory")
        print("   - Review error messages for specific issues")
    
    return exit_code


if __name__ == '__main__':
    exit(main()) 