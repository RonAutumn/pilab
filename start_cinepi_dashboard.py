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

# Add the current directory to Python path for dashboard imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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

def find_python_executable():
    """Find the appropriate Python executable"""
    # Check if we're in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return sys.executable
    
    # Check for common virtual environment locations
    venv_paths = ['.venv', 'venv', 'env']
    for venv_path in venv_paths:
        if os.path.exists(venv_path):
            python_path = os.path.join(venv_path, 'bin', 'python')
            if os.path.exists(python_path):
                return python_path
    
    # Fall back to system Python
    return 'python3'

def start_web_preview_server():
    """Start the web preview server"""
    print("🚀 Starting Web Preview Server...")
    
    python_exe = find_python_executable()
    cmd = [python_exe, 'web_preview.py']
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment to see if it starts successfully
        time.sleep(2)
        
        if process.poll() is None:
            print("✅ Web Preview Server started on port 8080")
            return process
        else:
            stdout, stderr = process.communicate()
            print("❌ Web Preview Server failed to start:")
            print(f"   STDOUT: {stdout}")
            print(f"   STDERR: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start Web Preview Server: {e}")
        return None

def start_dashboard():
    """Start the CinePi dashboard"""
    print("🚀 Starting CinePi Dashboard...")
    
    python_exe = find_python_executable()
    cmd = [python_exe, 'dashboard/app.py']
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Wait a moment to see if it starts successfully
        time.sleep(3)
        
        if process.poll() is None:
            print("✅ CinePi Dashboard started on port 5000")
            return process
        else:
            stdout, stderr = process.communicate()
            print("❌ Dashboard failed to start:")
            print(f"   STDOUT: {stdout}")
            print(f"   STDERR: {stderr}")
            return None
            
    except Exception as e:
        print(f"❌ Failed to start Dashboard: {e}")
        return None

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print("\n🛑 Shutting down CinePi services...")
    sys.exit(0)

def get_pi_ip_address():
    """Get the Pi's IP address"""
    try:
        import socket
        # Get the Pi's IP address
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip_address = s.getsockname()[0]
        s.close()
        return ip_address
    except:
        return "192.168.1.158"  # Fallback to known Pi IP

def main():
    """Main startup function"""
    print("🎬 CinePi Dashboard Startup")
    print("=" * 32)
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Check dependencies
    if not check_dependencies():
        sys.exit(1)
    
    # Check virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment found")
    else:
        print("⚠️  No virtual environment detected")
    
    # Start web preview server
    web_preview_process = start_web_preview_server()
    if not web_preview_process:
        print("❌ Failed to start Web Preview Server")
        sys.exit(1)
    
    # Wait a moment for web preview to fully start
    time.sleep(2)
    
    # Start dashboard
    dashboard_process = start_dashboard()
    if not dashboard_process:
        print("❌ Failed to start Dashboard")
        web_preview_process.terminate()
        sys.exit(1)
    
    # Get Pi IP address
    pi_ip = get_pi_ip_address()
    
    print("\n🎉 CinePi Dashboard is now running!")
    print("=" * 50)
    print(f"📱 Dashboard: http://{pi_ip}:5000")
    print(f"📷 Web Preview: http://{pi_ip}:8080")
    print(f"🔄 Live Preview: http://{pi_ip}:5000/stream")
    print("=" * 50)
    print("Press Ctrl+C to stop all services")
    
    try:
        # Keep the main process running
        while True:
            time.sleep(1)
            
            # Check if processes are still running
            if web_preview_process.poll() is not None:
                print("❌ Web Preview Server stopped unexpectedly")
                break
                
            if dashboard_process.poll() is not None:
                print("❌ Dashboard stopped unexpectedly")
                break
                
    except KeyboardInterrupt:
        print("\n🛑 Shutting down...")
    finally:
        # Clean up processes
        if web_preview_process:
            web_preview_process.terminate()
        if dashboard_process:
            dashboard_process.terminate()
        
        print("✅ All services stopped")

if __name__ == "__main__":
    main() 