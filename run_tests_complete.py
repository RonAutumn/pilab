#!/usr/bin/env python3
"""
CinePi Complete Test Runner

This script runs all tests for the CinePi system including:
- Dashboard integration tests
- Launcher system tests
- Core system tests
- Performance tests
- Security tests
"""

import os
import sys
import subprocess
import time
import argparse
from pathlib import Path
from typing import List, Dict, Any


class TestRunner:
    """Comprehensive test runner for CinePi system"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.test_results = {}
        self.start_time = time.time()
        
    def print_header(self, title: str):
        """Print a formatted header"""
        print("\n" + "=" * 60)
        print(f"🧪 {title}")
        print("=" * 60)
    
    def print_section(self, title: str):
        """Print a formatted section header"""
        print(f"\n📋 {title}")
        print("-" * 40)
    
    def run_pytest(self, test_path: str, test_name: str = None) -> Dict[str, Any]:
        """Run pytest on a specific test file or directory"""
        self.print_section(f"Running {test_name or test_path}")
        
        cmd = [
            sys.executable, "-m", "pytest",
            test_path,
            "-v",
            "--tb=short",
            "--color=yes"
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=300  # 5 minute timeout
            )
            
            success = result.returncode == 0
            output = result.stdout
            error = result.stderr
            
            print(f"✅ Test completed: {test_name or test_path}")
            if output:
                print(output)
            if error and not success:
                print(f"❌ Errors: {error}")
            
            return {
                'success': success,
                'output': output,
                'error': error,
                'return_code': result.returncode
            }
            
        except subprocess.TimeoutExpired:
            print(f"⏰ Test timed out: {test_name or test_path}")
            return {
                'success': False,
                'output': '',
                'error': 'Test timed out after 5 minutes',
                'return_code': -1
            }
        except Exception as e:
            print(f"❌ Test failed with exception: {e}")
            return {
                'success': False,
                'output': '',
                'error': str(e),
                'return_code': -1
            }
    
    def run_dashboard_tests(self) -> Dict[str, Any]:
        """Run dashboard integration tests"""
        self.print_header("Dashboard Integration Tests")
        
        # Test dashboard integration
        dashboard_test = self.run_pytest(
            "tests/test_dashboard_integration.py",
            "Dashboard Integration Tests"
        )
        
        # Test dashboard routes
        routes_test = self.run_pytest(
            "tests/test_routes.py",
            "Dashboard Routes Tests"
        )
        
        # Test dashboard services
        services_test = self.run_pytest(
            "tests/test_services.py",
            "Dashboard Services Tests"
        )
        
        return {
            'dashboard_integration': dashboard_test,
            'routes': routes_test,
            'services': services_test
        }
    
    def run_launcher_tests(self) -> Dict[str, Any]:
        """Run launcher system tests"""
        self.print_header("Launcher System Tests")
        
        launcher_test = self.run_pytest(
            "tests/test_launcher_system.py",
            "Launcher System Tests"
        )
        
        return {'launcher': launcher_test}
    
    def run_core_tests(self) -> Dict[str, Any]:
        """Run core system tests"""
        self.print_header("Core System Tests")
        
        tests = {}
        
        # Core system tests
        core_test_files = [
            ("tests/test_config_manager.py", "Configuration Manager"),
            ("tests/test_capture_utils.py", "Capture Utilities"),
            ("tests/test_timing_controller.py", "Timing Controller"),
            ("tests/test_metrics.py", "Metrics System"),
            ("tests/test_utils.py", "Utility Functions")
        ]
        
        for test_file, test_name in core_test_files:
            if Path(test_file).exists():
                tests[test_name.lower().replace(' ', '_')] = self.run_pytest(test_file, test_name)
            else:
                print(f"⚠️  Test file not found: {test_file}")
        
        return tests
    
    def run_performance_tests(self) -> Dict[str, Any]:
        """Run performance tests"""
        self.print_header("Performance Tests")
        
        # Run performance tests from integration test file
        performance_test = self.run_pytest(
            "tests/test_dashboard_integration.py::TestDashboardPerformance",
            "Dashboard Performance Tests"
        )
        
        return {'performance': performance_test}
    
    def run_security_tests(self) -> Dict[str, Any]:
        """Run security tests"""
        self.print_header("Security Tests")
        
        # Run security tests from integration test file
        security_test = self.run_pytest(
            "tests/test_dashboard_integration.py::TestDashboardSecurity",
            "Dashboard Security Tests"
        )
        
        # Run launcher security tests
        launcher_security_test = self.run_pytest(
            "tests/test_launcher_system.py::TestLauncherSecurity",
            "Launcher Security Tests"
        )
        
        return {
            'dashboard_security': security_test,
            'launcher_security': launcher_security_test
        }
    
    def run_quick_tests(self) -> Dict[str, Any]:
        """Run a quick subset of tests"""
        self.print_header("Quick Test Suite")
        
        # Run only essential tests
        essential_tests = [
            ("tests/test_dashboard_integration.py::TestDashboardIntegration::test_dashboard_home_page", "Dashboard Home Page"),
            ("tests/test_launcher_system.py::TestLauncherSystem::test_launcher_help_command", "Launcher Help Command"),
            ("tests/test_routes.py", "Core Routes"),
        ]
        
        results = {}
        for test_path, test_name in essential_tests:
            results[test_name.lower().replace(' ', '_')] = self.run_pytest(test_path, test_name)
        
        return results
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all test suites"""
        self.print_header("CinePi Complete Test Suite")
        
        all_results = {}
        
        # Run all test categories
        all_results['dashboard'] = self.run_dashboard_tests()
        all_results['launcher'] = self.run_launcher_tests()
        all_results['core'] = self.run_core_tests()
        all_results['performance'] = self.run_performance_tests()
        all_results['security'] = self.run_security_tests()
        
        return all_results
    
    def generate_report(self, results: Dict[str, Any]) -> str:
        """Generate a comprehensive test report"""
        self.print_header("Test Results Summary")
        
        total_tests = 0
        passed_tests = 0
        failed_tests = 0
        
        report_lines = []
        
        for category, category_results in results.items():
            if isinstance(category_results, dict):
                report_lines.append(f"\n📊 {category.upper()} TESTS:")
                report_lines.append("-" * 40)
                
                for test_name, test_result in category_results.items():
                    if isinstance(test_result, dict) and 'success' in test_result:
                        total_tests += 1
                        if test_result['success']:
                            passed_tests += 1
                            status = "✅ PASS"
                        else:
                            failed_tests += 1
                            status = "❌ FAIL"
                        
                        report_lines.append(f"{status} {test_name}")
                        
                        if not test_result['success'] and test_result.get('error'):
                            report_lines.append(f"   Error: {test_result['error'][:100]}...")
        
        # Summary
        report_lines.append(f"\n📈 SUMMARY:")
        report_lines.append("-" * 40)
        report_lines.append(f"Total Tests: {total_tests}")
        report_lines.append(f"Passed: {passed_tests}")
        report_lines.append(f"Failed: {failed_tests}")
        
        if total_tests > 0:
            success_rate = (passed_tests / total_tests) * 100
            report_lines.append(f"Success Rate: {success_rate:.1f}%")
        
        # Timing
        elapsed_time = time.time() - self.start_time
        report_lines.append(f"Total Time: {elapsed_time:.2f} seconds")
        
        return "\n".join(report_lines)
    
    def check_dependencies(self) -> bool:
        """Check if all required dependencies are available"""
        self.print_header("Dependency Check")
        
        required_packages = [
            'pytest',
            'flask',
            'flask_socketio',
            'pathlib',
            'threading',
            'time',
            'signal'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
                print(f"✅ {package}")
            except ImportError:
                print(f"❌ {package} - MISSING")
                missing_packages.append(package)
        
        if missing_packages:
            print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
            print("Please install missing dependencies:")
            print("pip install -r requirements.txt")
            return False
        
        print("\n✅ All dependencies available!")
        return True
    
    def run(self, test_type: str = 'all'):
        """Main test runner"""
        print("🎬 CinePi Complete Test Runner")
        print("=" * 60)
        
        # Check dependencies first
        if not self.check_dependencies():
            print("❌ Dependency check failed. Please install missing packages.")
            return False
        
        # Run tests based on type
        if test_type == 'quick':
            results = self.run_quick_tests()
        elif test_type == 'dashboard':
            results = self.run_dashboard_tests()
        elif test_type == 'launcher':
            results = self.run_launcher_tests()
        elif test_type == 'core':
            results = self.run_core_tests()
        elif test_type == 'performance':
            results = self.run_performance_tests()
        elif test_type == 'security':
            results = self.run_security_tests()
        else:  # 'all'
            results = self.run_all_tests()
        
        # Generate and print report
        report = self.generate_report(results)
        print(report)
        
        # Save report to file
        report_file = self.project_root / "test_report.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Return overall success
        total_tests = 0
        passed_tests = 0
        
        for category_results in results.values():
            if isinstance(category_results, dict):
                for test_result in category_results.values():
                    if isinstance(test_result, dict) and 'success' in test_result:
                        total_tests += 1
                        if test_result['success']:
                            passed_tests += 1
        
        overall_success = total_tests > 0 and passed_tests == total_tests
        
        if overall_success:
            print("\n🎉 All tests passed!")
        else:
            print(f"\n⚠️  {total_tests - passed_tests} test(s) failed. Check the report for details.")
        
        return overall_success


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="CinePi Complete Test Runner")
    parser.add_argument(
        '--type', '-t',
        choices=['all', 'quick', 'dashboard', 'launcher', 'core', 'performance', 'security'],
        default='all',
        help='Type of tests to run (default: all)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    args = parser.parse_args()
    
    runner = TestRunner()
    success = runner.run(args.type)
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main() 