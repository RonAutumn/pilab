#!/bin/bash
#
# CinePi Live Preview Script
# Ensures mutual exclusion with capture process using lock file
#
# Usage: ./run_preview.sh [options]
# Options: Same as preview.py (--port, --resolution, --fps, etc.)

set -e  # Exit on any error

# Script configuration
LOCK_FILE="/tmp/cinepi_camera.lock"
LOCK_TIMEOUT=5  # Seconds to wait for lock
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_SCRIPT="$SCRIPT_DIR/preview.py"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local color=$1
    local message=$2
    echo -e "${color}[$(date '+%Y-%m-%d %H:%M:%S')] $message${NC}"
}

# Function to cleanup lock file
cleanup_lock() {
    if [[ -f "$LOCK_FILE" ]]; then
        local lock_pid=$(cat "$LOCK_FILE" 2>/dev/null || echo "")
        if [[ "$lock_pid" == "$$" ]]; then
            rm -f "$LOCK_FILE"
            print_status "$GREEN" "Lock file removed"
        fi
    fi
}

# Function to check if process is still running
is_process_running() {
    local pid=$1
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
        return 0  # Process is running
    else
        return 1  # Process is not running
    fi
}

# Function to handle stale lock
handle_stale_lock() {
    local lock_pid=$(cat "$LOCK_FILE" 2>/dev/null || echo "")
    
    if [[ -n "$lock_pid" ]]; then
        if is_process_running "$lock_pid"; then
            print_status "$RED" "Camera is already in use by process $lock_pid"
            print_status "$YELLOW" "If this is incorrect, manually remove: $LOCK_FILE"
            exit 1
        else
            print_status "$YELLOW" "Found stale lock file (process $lock_pid not running)"
            print_status "$BLUE" "Removing stale lock file..."
            rm -f "$LOCK_FILE"
        fi
    else
        print_status "$YELLOW" "Found empty or corrupted lock file"
        print_status "$BLUE" "Removing corrupted lock file..."
        rm -f "$LOCK_FILE"
    fi
}

# Function to acquire lock
acquire_lock() {
    local attempts=0
    local max_attempts=$((LOCK_TIMEOUT * 2))  # Check every 0.5 seconds
    
    while [[ $attempts -lt $max_attempts ]]; do
        if [[ ! -f "$LOCK_FILE" ]]; then
            # Try to create lock file atomically
            if (set -C; echo "$$" > "$LOCK_FILE") 2>/dev/null; then
                print_status "$GREEN" "Camera lock acquired (PID: $$)"
                return 0
            fi
        else
            handle_stale_lock
            continue
        fi
        
        print_status "$YELLOW" "Waiting for camera lock... (attempt $((attempts + 1))/$max_attempts)"
        sleep 0.5
        ((attempts++))
    done
    
    print_status "$RED" "Failed to acquire camera lock after $LOCK_TIMEOUT seconds"
    print_status "$YELLOW" "Another process may be using the camera"
    exit 1
}

# Function to setup signal handlers
setup_signals() {
    trap cleanup_lock EXIT
    trap 'print_status "$YELLOW" "Received SIGINT, shutting down..."; cleanup_lock; exit 0' INT
    trap 'print_status "$YELLOW" "Received SIGTERM, shutting down..."; cleanup_lock; exit 0' TERM
}

# Function to check dependencies
check_dependencies() {
    if [[ ! -f "$PYTHON_SCRIPT" ]]; then
        print_status "$RED" "Error: Python script not found: $PYTHON_SCRIPT"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        print_status "$RED" "Error: python3 not found in PATH"
        exit 1
    fi
}

# Function to display usage
show_usage() {
    cat << EOF
CinePi Live Preview Script

Usage: $0 [options]

This script ensures only one camera process (capture or preview) runs at a time
to prevent resource contention and "Device or resource busy" errors.

Options (same as preview.py):
  --port PORT             Server port (default: 5000)
  --host HOST             Server host binding (default: 0.0.0.0)
  --resolution WIDTH HEIGHT  Preview resolution (default: 640 480)
  --fps FPS               Target frame rate (default: 20)
  --quality QUALITY       JPEG quality 1-100 (default: 85)
  --config FILE           Configuration file path
  --verbose               Enable debug logging
  --help                  Show this help message

Examples:
  $0 --port 8080 --resolution 1280 720
  $0 --fps 30 --quality 90
  $0 --config my_config.yaml --verbose

Web Interface:
  Once started, open http://localhost:5000 in your browser
  (Replace localhost with your Pi's IP address for network access)

Lock File: $LOCK_FILE
EOF
}

# Function to get local IP address
get_local_ip() {
    local ip=$(hostname -I 2>/dev/null | awk '{print $1}' | head -1)
    if [[ -n "$ip" ]]; then
        echo "$ip"
    else
        echo "localhost"
    fi
}

# Main execution
main() {
    # Parse help argument
    if [[ "$1" == "--help" ]] || [[ "$1" == "-h" ]]; then
        show_usage
        exit 0
    fi
    
    print_status "$BLUE" "Starting CinePi Live Preview"
    print_status "$BLUE" "Script: $PYTHON_SCRIPT"
    print_status "$BLUE" "Lock file: $LOCK_FILE"
    
    # Check dependencies
    check_dependencies
    
    # Setup signal handlers
    setup_signals
    
    # Acquire lock
    acquire_lock
    
    # Launch Python script with all arguments
    print_status "$GREEN" "Launching live preview..."
    print_status "$BLUE" "Arguments: $*"
    
    # Get local IP for user information
    local ip=$(get_local_ip)
    print_status "$GREEN" "Preview will be available at: http://$ip:5000"
    
    if python3 "$PYTHON_SCRIPT" "$@"; then
        print_status "$GREEN" "Live preview completed successfully"
    else
        local exit_code=$?
        print_status "$RED" "Live preview failed with exit code $exit_code"
        exit $exit_code
    fi
}

# Run main function with all arguments
main "$@" 