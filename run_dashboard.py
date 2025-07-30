#!/usr/bin/env python3
"""
CinePi Dashboard Launcher Script

This script launches the CinePi dashboard application.
"""

import os
import sys
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from dashboard.app import create_app, create_socketio_app


def main():
    """Main entry point for CinePi Dashboard"""
    
    # Set up environment
    os.environ.setdefault('FLASK_ENV', 'development')
    
    print("Starting CinePi Dashboard...")
    print("=" * 50)
    
    try:
        # Create application
        app = create_app('development')
        
        # Create SocketIO instance
        socketio = create_socketio_app(app)
        
        print(f"Dashboard URL: http://localhost:5000")
        print(f"SocketIO URL: http://localhost:5000")
        print(f"Health Check: http://localhost:5000/health")
        print("=" * 50)
        
        # Run with SocketIO
        socketio.run(
            app,
            host='0.0.0.0',
            port=5000,
            debug=True,
            use_reloader=True
        )
        
    except KeyboardInterrupt:
        print("\nShutting down CinePi Dashboard...")
    except Exception as e:
        print(f"Error starting dashboard: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main() 