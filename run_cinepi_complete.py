#!/usr/bin/env python3
"""
CinePi Complete Launcher Script

This script launches both the CinePi dashboard and the main timelapse system together.
You can run either just the dashboard, just the timelapse, or both simultaneously.
"""

import os
import sys
import time
import signal
import threading
import subprocess
from pathlib import Path
from typing import Optional

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print("\n🛑 Shutdown signal received. Stopping all CinePi processes...")
    sys.exit(0)

def setup_signal_handlers():
    """Set up signal handlers for graceful shutdown"""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

def run_dashboard():
    """Run the CinePi dashboard in a separate thread"""
    try:
        print("🌐 Starting CinePi Dashboard...")
        from dashboard.app import create_app, create_socketio_app
        
        # Set up environment
        os.environ.setdefault('FLASK_ENV', 'development')
        
        # Create application
        app = create_app('development')
        socketio = create_socketio_app(app)
        
        print("✅ Dashboard started successfully!")
        print("   📱 Dashboard URL: http://localhost:5000")
        print("   🔌 SocketIO URL: http://localhost:5000")
        print("   ❤️  Health Check: http://localhost:5000/health")
        
        # Run with SocketIO
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=False,  # Set to False when running with timelapse
            use_reloader=False  # Set to False when running with timelapse
        )
        
    except Exception as e:
        print(f"❌ Error starting dashboard: {e}")

def run_timelapse():
    """Run the CinePi timelapse system in a separate thread"""
    try:
        print("📸 Starting CinePi Timelapse System...")
        
        # Add the src directory to Python path
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        
        from main import main
        
        print("✅ Timelapse system started successfully!")
        main()
        
    except Exception as e:
        print(f"❌ Error starting timelapse system: {e}")

def run_dashboard_only():
    """Run only the dashboard"""
    print("🎯 Running Dashboard Only Mode")
    print("=" * 50)
    run_dashboard()

def run_timelapse_only():
    """Run only the timelapse system"""
    print("🎯 Running Timelapse Only Mode")
    print("=" * 50)
    run_timelapse()

def run_both():
    """Run both dashboard and timelapse system"""
    print("🎯 Running Complete CinePi System (Dashboard + Timelapse)")
    print("=" * 60)
    
    # Start dashboard in a separate thread
    dashboard_thread = threading.Thread(target=run_dashboard, daemon=True)
    dashboard_thread.start()
    
    # Give dashboard time to start
    print("⏳ Waiting for dashboard to initialize...")
    time.sleep(3)
    
    # Start timelapse system in main thread
    print("📸 Starting timelapse system...")
    run_timelapse()

def show_menu():
    """Show the main menu"""
    print("\n🎬 CinePi Complete Launcher")
    print("=" * 40)
    print("Choose what to run:")
    print("1. 🎯 Dashboard Only (Web Interface)")
    print("2. 📸 Timelapse Only (Camera System)")
    print("3. 🚀 Complete System (Dashboard + Timelapse)")
    print("4. ❌ Exit")
    print("=" * 40)

def main():
    """Main entry point"""
    setup_signal_handlers()
    
    # Check if command line arguments are provided
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode in ['dashboard', 'd', '1']:
            run_dashboard_only()
        elif mode in ['timelapse', 't', '2']:
            run_timelapse_only()
        elif mode in ['both', 'complete', 'c', '3']:
            run_both()
        elif mode in ['help', 'h', '?']:
            print("Usage: python run_cinepi_complete.py [mode]")
            print("Modes: dashboard|d|1, timelapse|t|2, both|complete|c|3, help|h|?")
        else:
            print(f"❌ Unknown mode: {mode}")
            print("Use 'help' for usage information")
    else:
        # Interactive mode
        while True:
            show_menu()
            try:
                choice = input("Enter your choice (1-4): ").strip()
                
                if choice == '1':
                    run_dashboard_only()
                    break
                elif choice == '2':
                    run_timelapse_only()
                    break
                elif choice == '3':
                    run_both()
                    break
                elif choice == '4':
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break

if __name__ == '__main__':
    main() 