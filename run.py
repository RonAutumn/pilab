#!/usr/bin/env python3
"""
Simple run script for CinePi timelapse system.
This script provides a convenient way to start the timelapse system.
"""

import sys
import os
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from main import main

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nCinePi stopped by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
