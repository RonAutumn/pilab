#!/usr/bin/env python3
"""
Test runner script for CinePi Dashboard

This script provides an easy way to run the test suite with different options.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print('='*60)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with exit code {e.returncode}")
        return False


def main():
    parser = argparse.ArgumentParser(description='CinePi Dashboard Test Runner')
    parser.add_argument('--unit', action='store_true', 
                       help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', 
                       help='Run integration tests only')
    parser.add_argument('--coverage', action='store_true', 
                       help='Run tests with coverage report')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Verbose output')
    parser.add_argument('--fast', action='store_true', 
                       help='Skip slow tests')
    parser.add_argument('--install-deps', action='store_true', 
                       help='Install test dependencies')
    parser.add_argument('--clean', action='store_true', 
                       help='Clean up test artifacts')
    
    args = parser.parse_args()
    
    # Check if we're in the right directory
    if not Path('dashboard').exists():
        print("❌ Error: 'dashboard' directory not found. Please run from project root.")
        sys.exit(1)
    
    # Install dependencies if requested
    if args.install_deps:
        print("Installing test dependencies...")
        if not run_command([sys.executable, '-m', 'pip', 'install', '-r', 'requirements-test.txt'], 
                          "Installing test dependencies"):
            sys.exit(1)
    
    # Clean up if requested
    if args.clean:
        print("Cleaning up test artifacts...")
        artifacts = ['htmlcov', 'coverage.xml', '.coverage', '.pytest_cache', '__pycache__']
        for artifact in artifacts:
            if Path(artifact).exists():
                if Path(artifact).is_file():
                    Path(artifact).unlink()
                else:
                    import shutil
                    shutil.rmtree(Path(artifact))
        print("✅ Cleanup completed")
    
    # Build pytest command
    cmd = [sys.executable, '-m', 'pytest']
    
    if args.verbose:
        cmd.append('-v')
    
    if args.unit:
        cmd.extend(['-m', 'unit'])
    elif args.integration:
        cmd.extend(['-m', 'integration'])
    
    if args.fast:
        cmd.extend(['-m', 'not slow'])
    
    if args.coverage:
        cmd.extend([
            '--cov=dashboard',
            '--cov-report=term-missing',
            '--cov-report=html:htmlcov',
            '--cov-report=xml:coverage.xml',
            '--cov-fail-under=90'
        ])
    
    # Run tests
    success = run_command(cmd, "Running test suite")
    
    if success:
        print("\n🎉 All tests passed!")
        if args.coverage:
            print("\n📊 Coverage reports generated:")
            print("   - HTML: htmlcov/index.html")
            print("   - XML: coverage.xml")
    else:
        print("\n💥 Some tests failed!")
        sys.exit(1)


if __name__ == '__main__':
    main() 