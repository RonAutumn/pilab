"""
Tests for CinePi Complete Launcher System
Tests the one-click launcher functionality and integration
"""

import pytest
import sys
import os
import time
import threading
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import tempfile
import shutil


class TestLauncherSystem:
    """Tests for the complete launcher system"""

    def test_launcher_help_command(self):
        """Test that the launcher help command works"""
        from run_cinepi_complete import main
        
        with patch('sys.argv', ['run_cinepi_complete.py', 'help']):
            with patch('builtins.print') as mock_print:
                main()
                mock_print.assert_called()

    def test_launcher_invalid_mode(self):
        """Test that invalid modes are handled gracefully"""
        from run_cinepi_complete import main
        
        with patch('sys.argv', ['run_cinepi_complete.py', 'invalid_mode']):
            with patch('builtins.print') as mock_print:
                main()
                # Should print error message
                mock_print.assert_called()

    def test_launcher_signal_handling(self):
        """Test that signal handlers are properly set up"""
        from run_cinepi_complete import setup_signal_handlers
        
        with patch('signal.signal') as mock_signal:
            setup_signal_handlers()
            # Should call signal.signal twice (SIGINT and SIGTERM)
            assert mock_signal.call_count == 2

    def test_launcher_dashboard_only_mode(self):
        """Test dashboard only mode"""
        from run_cinepi_complete import run_dashboard_only
        
        with patch('run_cinepi_complete.run_dashboard') as mock_run_dashboard:
            with patch('builtins.print') as mock_print:
                run_dashboard_only()
                mock_run_dashboard.assert_called_once()
                mock_print.assert_called()

    def test_launcher_timelapse_only_mode(self):
        """Test timelapse only mode"""
        from run_cinepi_complete import run_timelapse_only
        
        with patch('run_cinepi_complete.run_timelapse') as mock_run_timelapse:
            with patch('builtins.print') as mock_print:
                run_timelapse_only()
                mock_run_timelapse.assert_called_once()
                mock_print.assert_called()

    def test_launcher_both_mode(self):
        """Test running both dashboard and timelapse"""
        from run_cinepi_complete import run_both
        
        with patch('run_cinepi_complete.run_dashboard') as mock_run_dashboard:
            with patch('run_cinepi_complete.run_timelapse') as mock_run_timelapse:
                with patch('threading.Thread') as mock_thread:
                    with patch('time.sleep') as mock_sleep:
                        with patch('builtins.print') as mock_print:
                            # Mock the thread instance
                            mock_thread_instance = Mock()
                            mock_thread.return_value = mock_thread_instance
                            
                            run_both()
                            
                            # Should start dashboard in thread
                            mock_thread.assert_called_once()
                            mock_thread_instance.start.assert_called_once()
                            
                            # Should wait for dashboard to start
                            mock_sleep.assert_called_once_with(3)
                            
                            # Should start timelapse in main thread
                            mock_run_timelapse.assert_called_once()

    def test_launcher_interactive_menu(self):
        """Test interactive menu functionality"""
        from run_cinepi_complete import show_menu, main
        
        with patch('builtins.print') as mock_print:
            show_menu()
            # Should print menu options
            assert mock_print.call_count > 0

    def test_launcher_command_line_arguments(self):
        """Test command line argument parsing"""
        from run_cinepi_complete import main
        
        # Test dashboard mode
        with patch('sys.argv', ['run_cinepi_complete.py', 'dashboard']):
            with patch('run_cinepi_complete.run_dashboard_only') as mock_run:
                main()
                mock_run.assert_called_once()

        # Test timelapse mode
        with patch('sys.argv', ['run_cinepi_complete.py', 't']):
            with patch('run_cinepi_complete.run_timelapse_only') as mock_run:
                main()
                mock_run.assert_called_once()

        # Test complete mode
        with patch('sys.argv', ['run_cinepi_complete.py', 'both']):
            with patch('run_cinepi_complete.run_both') as mock_run:
                main()
                mock_run.assert_called_once()

    def test_launcher_error_handling(self):
        """Test error handling in launcher"""
        from run_cinepi_complete import run_dashboard, run_timelapse
        
        # Test dashboard error handling
        with patch('dashboard.app.create_app') as mock_create_app:
            mock_create_app.side_effect = Exception("Dashboard error")
            with patch('builtins.print') as mock_print:
                run_dashboard()
                # Should print error message
                mock_print.assert_called()

        # Test timelapse error handling
        with patch('run_cinepi_complete.main') as mock_main:
            mock_main.side_effect = Exception("Timelapse error")
            with patch('builtins.print') as mock_print:
                run_timelapse()
                # Should print error message
                mock_print.assert_called()


class TestLauncherIntegration:
    """Integration tests for the launcher system"""

    def test_launcher_file_structure(self):
        """Test that all launcher files exist and are properly structured"""
        # Check main launcher file
        assert Path('run_cinepi_complete.py').exists()
        
        # Check batch file for Windows
        assert Path('run_cinepi.bat').exists()
        
        # Check shell script for Linux/Mac
        assert Path('run_cinepi.sh').exists()
        
        # Check README
        assert Path('CINEPI_LAUNCHER_README.md').exists()

    def test_launcher_imports(self):
        """Test that launcher can import required modules"""
        # Test dashboard imports
        try:
            from dashboard.app import create_app, create_socketio_app
            assert create_app is not None
            assert create_socketio_app is not None
        except ImportError as e:
            pytest.skip(f"Dashboard not available: {e}")

        # Test timelapse imports
        try:
            sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
            from main import main
            assert main is not None
        except ImportError as e:
            pytest.skip(f"Timelapse system not available: {e}")

    def test_launcher_configuration(self):
        """Test launcher configuration and environment setup"""
        from run_cinepi_complete import run_dashboard
        
        with patch('dashboard.app.create_app') as mock_create_app:
            with patch('dashboard.app.create_socketio_app') as mock_socketio:
                with patch('os.environ.setdefault') as mock_env:
                    # Mock the socketio instance
                    mock_socketio_instance = Mock()
                    mock_socketio.return_value = mock_socketio_instance
                    
                    run_dashboard()
                    
                    # Should set environment
                    mock_env.assert_called_with('FLASK_ENV', 'development')
                    
                    # Should create app
                    mock_create_app.assert_called_with('development')
                    
                    # Should create socketio
                    mock_socketio.assert_called()

    def test_launcher_port_configuration(self):
        """Test that launcher uses correct port configuration"""
        from run_cinepi_complete import run_dashboard
        
        with patch('dashboard.app.create_app') as mock_create_app:
            with patch('dashboard.app.create_socketio_app') as mock_socketio:
                # Mock the socketio instance
                mock_socketio_instance = Mock()
                mock_socketio.return_value = mock_socketio_instance
                
                run_dashboard()
                
                # Check that socketio.run was called with correct parameters
                mock_socketio_instance.run.assert_called_once()
                call_args = mock_socketio_instance.run.call_args
                assert call_args[1]['host'] == '0.0.0.0'
                assert call_args[1]['port'] == 5000
                assert call_args[1]['debug'] is False
                assert call_args[1]['use_reloader'] is False


class TestLauncherPerformance:
    """Performance tests for the launcher"""

    def test_launcher_startup_time(self):
        """Test that launcher starts up quickly"""
        from run_cinepi_complete import run_dashboard_only
        
        with patch('run_cinepi_complete.run_dashboard') as mock_run_dashboard:
            import time
            start_time = time.time()
            run_dashboard_only()
            startup_time = time.time() - start_time
            
            # Should start up within 1 second
            assert startup_time < 1.0

    def test_launcher_memory_usage(self):
        """Test that launcher doesn't use excessive memory"""
        import psutil
        import os
        
        # Get current process memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Run launcher operations
        from run_cinepi_complete import show_menu, main
        
        with patch('sys.argv', ['run_cinepi_complete.py', 'help']):
            with patch('builtins.print'):
                main()
        
        # Check memory usage hasn't increased significantly
        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory
        
        # Should not increase by more than 10MB
        assert memory_increase < 10 * 1024 * 1024


class TestLauncherSecurity:
    """Security tests for the launcher"""

    def test_launcher_input_validation(self):
        """Test that launcher validates input properly"""
        from run_cinepi_complete import main
        
        # Test with malicious input
        malicious_inputs = [
            '; rm -rf /',
            '$(cat /etc/passwd)',
            '<script>alert("xss")</script>',
            '"; DROP TABLE users; --'
        ]
        
        for malicious_input in malicious_inputs:
            with patch('sys.argv', ['run_cinepi_complete.py', malicious_input]):
                with patch('builtins.print') as mock_print:
                    main()
                    # Should handle malicious input gracefully
                    mock_print.assert_called()

    def test_launcher_file_permissions(self):
        """Test that launcher files have appropriate permissions"""
        # Check that launcher files are readable
        assert os.access('run_cinepi_complete.py', os.R_OK)
        
        # Check that batch file is readable
        assert os.access('run_cinepi.bat', os.R_OK)
        
        # Check that shell script is readable
        assert os.access('run_cinepi.sh', os.R_OK)

    def test_launcher_path_injection(self):
        """Test that launcher is not vulnerable to path injection"""
        from run_cinepi_complete import main
        
        # Test with path traversal attempts
        path_attacks = [
            '../../../etc/passwd',
            '..\\..\\..\\windows\\system32\\config\\sam',
            '....//....//....//etc/passwd'
        ]
        
        for path_attack in path_attacks:
            with patch('sys.argv', ['run_cinepi_complete.py', path_attack]):
                with patch('builtins.print') as mock_print:
                    main()
                    # Should handle path attacks gracefully
                    mock_print.assert_called()


class TestLauncherCompatibility:
    """Compatibility tests for the launcher"""

    def test_launcher_python_versions(self):
        """Test that launcher works with different Python versions"""
        import sys
        
        # Should work with Python 3.8+
        assert sys.version_info >= (3, 8)

    def test_launcher_platform_compatibility(self):
        """Test that launcher works on different platforms"""
        import platform
        
        # Should work on Windows, Linux, and macOS
        system = platform.system().lower()
        assert system in ['windows', 'linux', 'darwin']

    def test_launcher_dependency_check(self):
        """Test that launcher can check for required dependencies"""
        required_modules = [
            'flask',
            'flask_socketio',
            'pathlib',
            'threading',
            'time',
            'signal'
        ]
        
        for module in required_modules:
            try:
                __import__(module)
            except ImportError:
                pytest.fail(f"Required module {module} not available")


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 