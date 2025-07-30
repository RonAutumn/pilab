#!/bin/bash
#
# CinePi Background Launch Wrapper
# Ensures correct working directory for nohup background execution
#
# This script fixes the common issue where nohup fails with "python3: can't open file"
# when executed from the wrong directory. It automatically sets the working directory
# to the script's location before launching the application.
#
# Usage: ./run_all.sh [options]
# Options: Same as main.py (--interval, --duration, --output-dir, etc.)

set -e  # Exit on any error

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="timelapse.log"
PID_FILE="timelapse.pid"

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

# Function to display usage
show_usage() {
    cat << EOF
CinePi Background Launch Wrapper

Usage: $0 [options]

This script ensures the correct working directory for background execution,
preventing "python3: can't open file" errors when using nohup.

Options (same as main.py):
  --interval SECONDS     Capture interval in seconds (default: 30)
  --duration HOURS       Total duration in hours (0 = indefinite)
  --output-dir PATH      Output directory for images
  --config FILE          Configuration file path
  --verbose              Enable verbose logging
  --dry-run              Test configuration without capturing
  --help                 Show this help message
  --stop                 Stop running background process
  --status               Check status of background process

Examples:
  $0 --interval 60 --duration 2
  $0 --output-dir /mnt/external/timelapse --interval 30
  $0 --config my_config.yaml --verbose
  $0 --stop
  $0 --status

Log Files:
  - Application output: $LOG_FILE
  - Process ID: $PID_FILE
  - Application logs: logs/cinepi.log
  - Metadata: logs/timelapse_metadata.csv

Working Directory: $SCRIPT_DIR
EOF
}

# Function to check if process is running
is_process_running() {
    if [[ -f "$PID_FILE" ]]; then
        local pid=$(cat "$PID_FILE" 2>/dev/null || echo "")
        if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
            return 0  # Process is running
        fi
    fi
    return 1  # Process is not running
}

# Function to get process status
get_process_status() {
    if is_process_running; then
        local pid=$(cat "$PID_FILE")
        local uptime=$(ps -o etime= -p "$pid" 2>/dev/null || echo "unknown")
        print_status "$GREEN" "Process is running (PID: $pid, Uptime: $uptime)"
        
        # Show recent log entries
        if [[ -f "$LOG_FILE" ]]; then
            print_status "$BLUE" "Recent log entries:"
            tail -5 "$LOG_FILE" 2>/dev/null || echo "No log entries found"
        fi
    else
        print_status "$YELLOW" "No background process is running"
        # Clean up stale PID file
        if [[ -f "$PID_FILE" ]]; then
            rm -f "$PID_FILE"
            print_status "$BLUE" "Removed stale PID file"
        fi
    fi
}

# Function to stop background process
stop_process() {
    if is_process_running; then
        local pid=$(cat "$PID_FILE")
        print_status "$YELLOW" "Stopping background process (PID: $pid)..."
        
        # Send SIGTERM first
        kill "$pid" 2>/dev/null || true
        
        # Wait for graceful shutdown
        local count=0
        while [[ $count -lt 10 ]] && is_process_running; do
            sleep 1
            ((count++))
        done
        
        # Force kill if still running
        if is_process_running; then
            print_status "$YELLOW" "Process not responding, forcing shutdown..."
            kill -9 "$pid" 2>/dev/null || true
        fi
        
        # Clean up PID file
        rm -f "$PID_FILE"
        print_status "$GREEN" "Background process stopped"
    else
        print_status "$YELLOW" "No background process is running"
        rm -f "$PID_FILE"  # Clean up stale PID file
    fi
}

# Function to check dependencies
check_dependencies() {
    if [[ ! -f "$SCRIPT_DIR/run.py" ]]; then
        print_status "$RED" "Error: run.py not found in $SCRIPT_DIR"
        exit 1
    fi
    
    if ! command -v python3 &> /dev/null; then
        print_status "$RED" "Error: python3 not found in PATH"
        exit 1
    fi
}

# Function to launch background process
launch_background() {
    # Check if process is already running
    if is_process_running; then
        local pid=$(cat "$PID_FILE")
        print_status "$RED" "Background process is already running (PID: $pid)"
        print_status "$YELLOW" "Use '$0 --stop' to stop it first"
        exit 1
    fi
    
    # Change to script directory
    cd "$SCRIPT_DIR"
    print_status "$BLUE" "Working directory set to: $(pwd)"
    
    # Launch background process
    print_status "$GREEN" "Starting background timelapse capture..."
    print_status "$BLUE" "Arguments: $*"
    print_status "$BLUE" "Log file: $LOG_FILE"
    
    # Start process with nohup
    nohup python3 run.py "$@" > "$LOG_FILE" 2>&1 &
    local pid=$!
    
    # Save PID
    echo "$pid" > "$PID_FILE"
    
    print_status "$GREEN" "Background process started (PID: $pid)"
    print_status "$BLUE" "Monitor progress with: tail -f $LOG_FILE"
    print_status "$BLUE" "Check status with: $0 --status"
    print_status "$BLUE" "Stop process with: $0 --stop"
}

# Main execution
main() {
    # Parse special arguments
    case "${1:-}" in
        --help|-h)
            show_usage
            exit 0
            ;;
        --stop)
            stop_process
            exit 0
            ;;
        --status)
            get_process_status
            exit 0
            ;;
    esac
    
    print_status "$BLUE" "CinePi Background Launch Wrapper"
    print_status "$BLUE" "Script directory: $SCRIPT_DIR"
    print_status "$BLUE" "Working directory will be set to: $SCRIPT_DIR"
    
    # Check dependencies
    check_dependencies
    
    # Launch background process
    launch_background "$@"
}

# Run main function with all arguments
main "$@" 