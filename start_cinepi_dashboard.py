#!/usr/bin/env python3
"""
CinePi Dashboard Startup Script

This script starts both the main dashboard and web preview server together
for a complete CinePi experience.
"""

import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

def check_dependencies():
    """Check if required files exist"""
    required_files = [
        'dashboard/app.py',
        'web_preview.py'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ Missing required files:")
        for file_path in missing_files:
            print(f"   - {file_path}")
        return False
    
    return True

def start_web_preview_server():
    """Start the web preview server"""
    print("🚀 Starting Web Preview Server...")
    
    try:
        # Activate virtual environment if it exists
        venv_python = '.venv/bin/python' if os.path.exists('.venv/bin/python') else 'python'
        
        process = subprocess.Popen([
            venv_python, 'web_preview.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ Web Preview Server started on port 8080")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Web Preview Server failed to start:")
            print(f"   STDOUT: {stdout.decode()}")
            print(f"   STDERR: {stderr.decode()}")
            return None
    except Exception as e:
        print(f"❌ Error starting Web Preview Server: {e}")
        return None

def start_dashboard():
    """Start the main dashboard"""
    print("🚀 Starting CinePi Dashboard...")
    
    try:
        # Activate virtual environment if it exists
        venv_python = '.venv/bin/python' if os.path.exists('.venv/bin/python') else 'python'
        
        process = subprocess.Popen([
            venv_python, 'dashboard/app.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ CinePi Dashboard started on port 5000")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Dashboard failed to start:")
            print(f"   STDOUT: {stdout.decode()}")
            print(f"   STDERR: {stderr.decode()}")
            return None
    except Exception as e:
        print(f"❌ Error starting Dashboard: {e}")
        return None

def monitor_process(process, name):
    """Monitor a process and print its output"""
    while process.poll() is None:
        output = process.stdout.readline()
        if output:
            print(f"[{name}] {output.decode().strip()}")
        error = process.stderr.readline()
        if error:
            print(f"[{name} ERROR] {error.decode().strip()}")

def main():
    """Main startup function"""
    print("🎬 CinePi Dashboard Startup")
    print("=" * 40)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check if virtual environment exists
    if os.path.exists('.venv'):
        print("✅ Virtual environment found")
    else:
        print("⚠️  No virtual environment found, using system Python")
    
    # Start web preview server
    web_preview_process = start_web_preview_server()
    if not web_preview_process:
        print("❌ Failed to start Web Preview Server")
        sys.exit(1)
    
    # Start dashboard
    dashboard_process = start_dashboard()
    if not dashboard_process:
        print("❌ Failed to start Dashboard")
        web_preview_process.terminate()
        sys.exit(1)
    
    print("\n🎉 CinePi Dashboard is now running!")
    print("=" * 40)
    print("📊 Dashboard: http://192.168.1.158:5000")
    print("📹 Live Preview: http://192.168.1.158:8080")
    print("=" * 40)
    print("Press Ctrl+C to stop all services")
    
    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down CinePi Dashboard...")
        if web_preview_process:
            web_preview_process.terminate()
        if dashboard_process:
            dashboard_process.terminate()
        print("✅ Shutdown complete")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Monitor processes
    try:
        while True:
            if web_preview_process.poll() is not None:
                print("❌ Web Preview Server stopped unexpectedly")
                break
            if dashboard_process.poll() is not None:
                print("❌ Dashboard stopped unexpectedly")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(signal.SIGINT, None)

if __name__ == '__main__':
    main() 