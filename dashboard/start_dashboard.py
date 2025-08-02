#!/usr/bin/env python3
"""
PiLab Dashboard Startup Script

This script provides easy access to both web and CLI dashboard modes.
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed."""
    required_packages = ['flask', 'flask-socketio', 'supabase', 'python-dotenv']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print("❌ Missing required packages:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\nInstall with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def start_web_dashboard(host='0.0.0.0', port=5000, debug=False):
    """Start the web dashboard."""
    print(f"🚀 Starting PiLab Web Dashboard on {host}:{port}")
    print("📱 Open your browser to: http://localhost:5000")
    print("⏹️  Press Ctrl+C to stop")
    print()
    
    # Set environment variables
    env = os.environ.copy()
    env['DASHBOARD_HOST'] = host
    env['DASHBOARD_PORT'] = str(port)
    env['FLASK_DEBUG'] = str(debug).lower()
    
    # Run the web dashboard
    try:
        subprocess.run([
            sys.executable, 'dashboard/app.py'
        ], env=env, cwd=Path(__file__).parent.parent)
    except KeyboardInterrupt:
        print("\n👋 Web dashboard stopped")
    except Exception as e:
        print(f"❌ Error starting web dashboard: {e}")

def start_cli_dashboard(interval=30, once=False):
    """Start the CLI dashboard."""
    print("🚀 Starting PiLab CLI Dashboard")
    print("⏹️  Press Ctrl+C to stop")
    print()
    
    try:
        subprocess.run([
            sys.executable, 'dashboard/cli_dashboard.py',
            '--interval', str(interval)
        ] + (['--once'] if once else []), cwd=Path(__file__).parent.parent)
    except KeyboardInterrupt:
        print("\n👋 CLI dashboard stopped")
    except Exception as e:
        print(f"❌ Error starting CLI dashboard: {e}")

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='PiLab Dashboard Launcher',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python dashboard/start_dashboard.py web          # Start web dashboard
  python dashboard/start_dashboard.py web --port 8080  # Custom port
  python dashboard/start_dashboard.py cli          # Start CLI dashboard
  python dashboard/start_dashboard.py cli --once   # Single update
  python dashboard/start_dashboard.py cli --interval 60  # 60s updates
        """
    )
    
    subparsers = parser.add_subparsers(dest='mode', help='Dashboard mode')
    
    # Web dashboard parser
    web_parser = subparsers.add_parser('web', help='Start web dashboard')
    web_parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    web_parser.add_argument('--port', type=int, default=5000, help='Port to bind to (default: 5000)')
    web_parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    
    # CLI dashboard parser
    cli_parser = subparsers.add_parser('cli', help='Start CLI dashboard')
    cli_parser.add_argument('--interval', '-i', type=int, default=30, help='Update interval in seconds (default: 30)')
    cli_parser.add_argument('--once', '-o', action='store_true', help='Run once and exit')
    
    args = parser.parse_args()
    
    if not args.mode:
        parser.print_help()
        return
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Start appropriate dashboard
    if args.mode == 'web':
        start_web_dashboard(args.host, args.port, args.debug)
    elif args.mode == 'cli':
        start_cli_dashboard(args.interval, args.once)

if __name__ == '__main__':
    main() 