#!/bin/bash

echo ""
echo "========================================"
echo "    CinePi Complete System Launcher"
echo "========================================"
echo ""
echo "Starting CinePi Dashboard + Timelapse..."
echo ""
echo "Dashboard will be available at: http://localhost:5000"
echo ""
echo "Press Ctrl+C to stop all services"
echo ""

# Make sure the script is executable
chmod +x run_cinepi_complete.py

# Run the complete system
python3 run_cinepi_complete.py both 