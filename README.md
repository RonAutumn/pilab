# CinePi Timelapse System

A professional-grade timelapse photography system for Raspberry Pi 5 with HQ Camera, featuring comprehensive error handling, quality metrics, and graceful shutdown capabilities.

## 🎯 Features

- **High-Quality Timelapse Capture**: Optimized for Raspberry Pi 5 with HQ Camera
- **Comprehensive Error Handling**: Graceful shutdown, disk space monitoring, and permission validation
- **Image Quality Analysis**: Real-time sharpness and brightness metrics
- **Flexible Configuration**: YAML-based configuration with command-line overrides
- **Robust Logging**: CSV metadata logging with data integrity protection
- **Signal Handling**: Clean shutdown on Ctrl-C and system signals
- **Resource Management**: Automatic cleanup and resource monitoring

## 📋 System Requirements

### Operating System
- **Raspberry Pi OS Bullseye** (2021-11-02) or later
- **Supported**: Both 32-bit and 64-bit versions
- **Not Supported**: Raspberry Pi OS Buster or legacy images
- **Alternative**: Ubuntu Server 20.04+ (with manual camera setup)

### Hardware Requirements

#### Required Components
- **Raspberry Pi 5** (4GB or 8GB RAM recommended)
- **Raspberry Pi HQ Camera** (12MP Sony IMX477 sensor)
- **16mm C-mount lens** (or compatible C-mount lens)
- **MicroSD card** (64GB+ Class 10, UHS-I recommended)
- **Power supply** (5V/3A minimum, 5V/4A recommended)
- **Camera cable** (included with HQ Camera)

#### Optional Components
- **Tripod or mounting system** for stable positioning
- **External storage** (USB SSD for extended captures)
- **Cooling solution** (active cooling recommended for long captures)
- **Network connection** (WiFi or Ethernet for remote monitoring)

### Camera Limitations

**Important**: This system is designed for **single-camera operation only**. 

- **Single Camera Support**: Only one camera can be reliably used at a time
- **Resource Contention**: Multiple cameras may cause dropped frames or resource conflicts
- **High Resolution**: Full 12MP capture requires dedicated camera resources
- **Frame Rate**: Higher frame rates increase resource requirements
- **Memory Usage**: Each camera instance consumes significant system memory

**Note**: If you need multi-camera support, consider running separate instances on different Raspberry Pi devices or implementing a camera switching mechanism.

## 🚀 Installation

### 1. System Preparation

```bash
# Update Raspberry Pi OS
sudo apt update && sudo apt upgrade -y

# Enable camera interface
sudo raspi-config nonint do_camera 0

# Enable I2C (optional, for future sensor integration)
sudo raspi-config nonint do_i2c 0

# Reboot to apply changes
sudo reboot
```

### 2. Install Dependencies

#### Method A: Virtual Environment (Recommended)

```bash
# Install system dependencies
sudo apt install -y python3-pip python3-venv git

# Install camera libraries (RECOMMENDED: Use apt for picamera2)
sudo apt install -y python3-picamera2 python3-libcamera

# Create virtual environment
python3 -m venv cinepi_env
source cinepi_env/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

#### Method B: System-Wide Installation

```bash
# Install system dependencies
sudo apt install -y python3-pip git

# Install camera libraries
sudo apt install -y python3-picamera2 python3-libcamera

# Install Python dependencies system-wide
sudo pip3 install -r requirements.txt
```

#### Virtual Environment vs System-Wide Installation

| Aspect | Virtual Environment | System-Wide |
|--------|-------------------|-------------|
| **Isolation** | ✅ Isolated dependencies | ❌ Affects system Python |
| **Permissions** | ✅ No sudo required for pip | ❌ Requires sudo for pip |
| **Updates** | ✅ Easy to update/rollback | ❌ May affect other applications |
| **Disk Space** | ⚠️ Uses more disk space | ✅ More efficient |
| **Complexity** | ⚠️ Requires activation | ✅ No activation needed |
| **Development** | ✅ Recommended for development | ❌ Not recommended |

**Important Notes about picamera2 Installation:**

- **Recommended**: Install picamera2 via `apt` (as shown above) for best compatibility with Raspberry Pi OS
- **Alternative**: If apt installation is not available, pip installation is supported via requirements.txt
- **Avoid mixing**: Do not install picamera2 via both apt and pip to prevent version conflicts
- **Version pinning**: The requirements.txt pins picamera2 to version 0.3.12 for consistency
- **System Libraries**: picamera2 requires system-level camera libraries that are installed via apt

### 3. Clone and Setup

```bash
# Clone the repository
git clone <repository-url>
cd cinepi

# Copy configuration template
cp config.yaml.example config.yaml

# Edit configuration
nano config.yaml
```

## ⚙️ Configuration

### Configuration File Structure

The system uses `config.yaml` for all settings. Here's a complete example:

```yaml
# Camera settings
camera:
  resolution: [4056, 3040]  # Full resolution
  quality: 95               # JPEG quality (1-100)
  iso: 100                  # ISO sensitivity
  shutter_speed: 0          # Auto exposure (0) or microseconds
  exposure_mode: "auto"     # auto, night, backlight, spotlight, sports, snow, beach, verylong, fixedfps, antishake, fireworks
  awb_mode: "auto"          # auto, sunlight, cloudy, shade, tungsten, fluorescent, incandescent, flash, horizon

# Timelapse settings
timelapse:
  interval_seconds: 30      # Capture interval
  duration_hours: 24        # Total duration (0 = indefinite)
  output_dir: "output/images"
  filename_prefix: "timelapse"
  image_format: "jpg"       # jpg, png, bmp
  add_timestamp: true
  create_daily_dirs: true

# Logging settings
logging:
  log_level: "INFO"         # DEBUG, INFO, WARNING, ERROR
  log_dir: "logs"
  csv_filename: "timelapse_metadata.csv"
```

### Command-Line Options

```bash
# Basic usage with default config
python src/main.py

# Custom interval and duration
python src/main.py --interval 60 --duration 2

# Custom output directory
python src/main.py --output-dir /mnt/external/timelapse

# Verbose logging
python src/main.py --verbose

# Test configuration without capturing
python src/main.py --dry-run

# Suppress drift warnings
python src/main.py --suppress-drift

# Use custom config file
python src/main.py --config my_config.yaml
```

## 📸 Usage Examples

### Quick Start (First-Time Users)

**Before your first capture:**
```bash
# 1. Activate virtual environment (if using one)
source cinepi_env/bin/activate

# 2. Test configuration without capturing
python src/main.py --dry-run --verbose

# 3. Run a short test capture (1 minute)
python src/main.py --interval 10 --duration 0.1

# 4. Start your first timelapse
python src/main.py --interval 30 --duration 2
```

### Basic Usage
```bash
# Start a 24-hour timelapse with 30-second intervals
python src/main.py

# Start a 2-hour timelapse with 60-second intervals
python src/main.py --interval 60 --duration 2

# Test configuration without capturing images
python src/main.py --dry-run --verbose

# Use custom configuration file
python src/main.py --config my_config.yaml
```

### Advanced Usage
```bash
# High-frequency capture (5-second intervals for 1 hour)
python src/main.py --interval 5 --duration 1

# Long-term capture (indefinite duration)
python src/main.py --interval 300 --duration 0

# Custom output location
python src/main.py --output-dir /mnt/ssd/timelapse --interval 60

# Suppress drift warnings for systems with frequent NTP
python src/main.py --suppress-drift --interval 60

# High-quality capture with custom settings
python src/main.py --interval 30 --duration 4 --verbose
```

### Production Usage (Recommended)

For long-term or production use, use the launch scripts:

```bash
# Start timelapse capture with mutual exclusion
./run_capture.sh --interval 60 --duration 8

# Start with custom output directory
./run_capture.sh --output-dir /mnt/external/timelapse --interval 30

# Start live preview (for monitoring)
./run_preview.sh --port 8080 --resolution 1280 720

# Check status of running processes
./run_capture.sh --status
./run_preview.sh --status
```

### Background Operation (Recommended)

The project includes a background launch wrapper that fixes common nohup directory issues:

```bash
# Start background timelapse capture (automatically sets correct working directory)
./run_all.sh --interval 60 --duration 8

# Check status of background process
./run_all.sh --status

# Stop background process gracefully
./run_all.sh --stop

# Monitor progress in real-time
tail -f timelapse.log
```

#### Why Use run_all.sh?

The `run_all.sh` wrapper fixes the common "python3: can't open file" error that occurs when nohup is executed from the wrong directory. It automatically:

- **Sets Working Directory**: Changes to the script's location before launching
- **Manages Process**: Tracks PID and provides status/stop commands
- **Handles Logging**: Directs output to `timelapse.log`
- **Prevents Conflicts**: Ensures only one background process runs at a time

#### Alternative: Manual nohup (Not Recommended)

If you must use nohup directly, ensure you're in the correct directory:

```bash
# Change to project directory first
cd /path/to/cinepi

# Then run nohup
nohup python src/main.py --interval 60 --duration 8 > timelapse.log 2>&1 &

# Check status
tail -f timelapse.log

# Stop gracefully
pkill -f "python src/main.py"
```

**Warning**: Manual nohup may fail with "python3: can't open file" if executed from the wrong directory.

### Using Launch Scripts (Recommended)

The project includes two launch scripts that ensure mutual exclusion between capture and preview processes:

#### Timelapse Capture
```bash
# Start timelapse capture with mutual exclusion
./run_capture.sh --interval 60 --duration 2

# Custom output directory
./run_capture.sh --output-dir /mnt/external/timelapse --interval 30

# Test configuration
./run_capture.sh --dry-run --verbose
```

#### Live Preview
```bash
# Start live preview with mutual exclusion
./run_preview.sh --port 8080 --resolution 1280 720

# High-quality preview
./run_preview.sh --fps 30 --quality 90

# Custom configuration
./run_preview.sh --config my_config.yaml --verbose
```

#### Mutual Exclusion Benefits
- **Prevents Resource Contention**: Only one camera process can run at a time
- **Automatic Lock Management**: Lock files are created and cleaned up automatically
- **Stale Lock Detection**: Automatically detects and removes orphaned lock files
- **Graceful Shutdown**: Proper cleanup on Ctrl-C or system signals
- **Clear Error Messages**: Informative messages when camera is already in use

#### Lock File Management
- **Location**: `/tmp/cinepi_camera.lock`
- **Automatic Cleanup**: Removed when process exits normally
- **Manual Cleanup**: If needed, remove manually: `rm /tmp/cinepi_camera.lock`
- **Timeout**: 5-second wait for lock acquisition

## 📊 Output and Logging

### Image Files
- **Location**: `output/images/YYYY-MM-DD/` (daily directories)
- **Naming**: `timelapse_YYYYMMDD_HHMMSS_000001.jpg`
- **Format**: JPEG with configurable quality

### Log Files
- **Application Log**: `logs/cinepi.log`
- **Metadata CSV**: `logs/timelapse_metadata.csv`
- **Console Output**: Real-time progress and status

### Log Handling and Management

#### Log Directory Structure
The `logs/` directory is automatically created during installation and contains:

```
logs/
├── cinepi.log              # Main application log
├── timelapse_YYYYMMDD.csv  # Daily metadata logs
├── preview.log             # Live preview server log (if used)
└── error.log              # Error-specific log (if enabled)
```

#### Log File Purposes

**Application Log (`cinepi.log`)**
- **Content**: System startup, camera initialization, capture events, errors, warnings
- **Rotation**: Automatic rotation when file size exceeds 10MB
- **Retention**: Keeps last 5 log files (cinepi.log.1, cinepi.log.2, etc.)
- **Format**: Standard Python logging format with timestamps

**Metadata CSV (`timelapse_YYYYMMDD.csv`)**
- **Content**: Per-capture metadata including quality metrics
- **Structure**: CSV format with headers for easy analysis
- **Daily Files**: New file created each day for organization
- **Integrity**: Protected against corruption during writes

#### Log Permissions and Access

```bash
# Check log directory permissions
ls -la logs/

# Expected permissions: drwxrwxr-x (775)
# Owner: Your user
# Group: Your user group

# If permissions are incorrect, fix them:
chmod 775 logs/
chown $USER:$USER logs/
```

#### Log Monitoring and Analysis

```bash
# Monitor logs in real-time
tail -f logs/cinepi.log

# Search for errors
grep ERROR logs/cinepi.log

# Check recent captures
tail -20 logs/timelapse_$(date +%Y%m%d).csv

# Analyze log file sizes
du -h logs/*

# Check for log rotation
ls -la logs/cinepi.log*
```

#### Log Troubleshooting

**Common Log Issues:**

1. **Permission Denied**
   ```bash
   # Fix log directory permissions
   sudo chown $USER:$USER logs/
   chmod 775 logs/
   ```

2. **Disk Space Full**
   ```bash
   # Check available space
   df -h
   
   # Clean old log files
   find logs/ -name "*.log.*" -mtime +7 -delete
   ```

3. **Log File Corruption**
   ```bash
   # Backup and recreate log file
   mv logs/cinepi.log logs/cinepi.log.corrupted
   touch logs/cinepi.log
   chmod 664 logs/cinepi.log
   ```

4. **Missing Log Directory**
   ```bash
   # Recreate logs directory
   mkdir -p logs
   chmod 775 logs
   chown $USER:$USER logs
   ```

### CSV Metadata Structure
```csv
timestamp,filename,filepath,capture_number,interval_seconds,sharpness_score,brightness_value,file_size
2024-01-01T12:00:00,timelapse_20240101_120000_000001.jpg,output/images/2024-01-01/timelapse_20240101_120000_000001.jpg,1,30,125.5,128.3,2048576
```

## ⏱️ Timing Accuracy and System Clock Behavior

### Understanding NTP and Kernel Slewing

The CinePi system uses high-precision timing to maintain accurate capture intervals. However, system clock adjustments from NTP (Network Time Protocol) or kernel slewing can affect timing accuracy:

#### What Causes System Clock Adjustments?

1. **NTP Synchronization**: Network time servers periodically adjust the system clock to maintain accuracy
2. **Kernel Slewing**: The Linux kernel gradually adjusts the clock to correct drift without sudden jumps
3. **Manual Time Changes**: System administrators or other processes may modify the system time

#### How CinePi Handles Clock Adjustments

The timing controller automatically detects system clock adjustments and responds appropriately:

- **Detection**: Monitors for clock jumps greater than 1 second
- **Drift Reset**: Automatically resets accumulated drift when adjustments are detected
- **Warning System**: Logs clock adjustments with configurable verbosity
- **Timing Recovery**: Maintains accurate intervals despite system clock changes

#### Warning Suppression Options

For systems with frequent NTP adjustments, you can control warning verbosity:

```bash
# Default behavior: First 3 warnings at WARNING level, then INFO level
python src/main.py --interval 60

# Suppress all drift warnings (useful for systems with frequent NTP sync)
python src/main.py --suppress-drift --interval 60

# Verbose logging to see all timing details
python src/main.py --verbose --interval 60
```

#### Expected Behavior

- **Normal Operation**: Occasional clock adjustments are normal and expected
- **Warning Messages**: First few adjustments are logged as warnings, subsequent ones as info
- **Timing Accuracy**: The system maintains accurate intervals despite clock adjustments
- **No Data Loss**: Clock adjustments don't cause missed captures or timing errors

#### Best Practices

1. **For Stable Networks**: Use default warning behavior to monitor system health
2. **For Frequent NTP**: Use `--suppress-drift` to reduce log noise
3. **For Critical Timing**: Consider using a local NTP server with less frequent adjustments
4. **For Monitoring**: Check timing statistics in the final report for accuracy verification

## 🔧 Troubleshooting

### First-Launch Issues

#### System Preparation Checklist
Before running CinePi for the first time, ensure:

```bash
# 1. Check operating system version
cat /etc/os-release | grep VERSION

# 2. Verify camera hardware
vcgencmd get_camera

# 3. Check camera interface is enabled
sudo raspi-config nonint get_camera

# 4. Verify user permissions
groups $USER

# 5. Check available disk space
df -h

# 6. Verify Python environment
python3 --version
pip3 --version
```

#### Common First-Launch Problems

**1. "Camera not detected" or "No camera found"**
```bash
# Check hardware connection
vcgencmd get_camera
# Expected: supported=1 detected=1

# If detected=0, check:
# - Camera cable connection
# - Camera power (HQ Camera is self-powered)
# - Reboot after connecting camera

# Enable camera interface
sudo raspi-config nonint do_camera 0
sudo reboot
```

**2. "Permission denied" or "Access denied"**
```bash
# Add user to video group
sudo usermod -a -G video $USER

# Add user to gpio group (if needed)
sudo usermod -a -G gpio $USER

# Log out and back in, or reboot
sudo reboot

# Verify group membership
groups $USER
```

**3. "Module not found" or ImportError**
```bash
# Check if virtual environment is activated
echo $VIRTUAL_ENV

# If not activated:
source cinepi_env/bin/activate

# Verify picamera2 installation
python3 -c "import picamera2; print('picamera2 version:', picamera2.__version__)"

# If ImportError, reinstall:
sudo apt install python3-picamera2 python3-libcamera
```

**4. "Device or resource busy"**
```bash
# Check if another process is using the camera
ps aux | grep -E "(main.py|preview.py)"

# Kill any existing processes
pkill -f "python.*main.py"
pkill -f "python.*preview.py"

# Remove stale lock files
rm -f /tmp/cinepi_camera.lock
```

**5. "Insufficient disk space"**
```bash
# Check available space
df -h

# Clean up if needed
sudo apt autoremove
sudo apt autoclean

# Use external storage
python src/main.py --output-dir /mnt/external/timelapse
```

**6. "Configuration file not found"**
```bash
# Copy configuration template
cp config.yaml.example config.yaml

# Edit configuration
nano config.yaml

# Verify configuration
python src/main.py --dry-run
```

#### Environment-Specific Issues

**Virtual Environment Issues:**
```bash
# If virtual environment is corrupted
rm -rf cinepi_env
python3 -m venv cinepi_env
source cinepi_env/bin/activate
pip install -r requirements.txt
```

**System-Wide Installation Issues:**
```bash
# If system Python is affected
sudo pip3 uninstall picamera2
sudo apt install python3-picamera2 python3-libcamera
```

**Network/Remote Access Issues:**
```bash
# Check network connectivity
ping 8.8.8.8

# Check SSH access (if using remote)
ssh pi@raspberrypi.local

# Verify firewall settings
sudo ufw status
```

### Common Issues

#### Camera Not Detected
```bash
# Check camera connection
vcgencmd get_camera

# Expected output: supported=1 detected=1

# Check camera permissions
ls -la /dev/video*

# Enable camera interface
sudo raspi-config nonint do_camera 0
sudo reboot
```

#### Permission Errors
```bash
# Check user permissions
groups $USER

# Add user to video group
sudo usermod -a -G video $USER

# Log out and back in, or reboot
sudo reboot
```

#### Insufficient Disk Space
```bash
# Check available space
df -h

# Clean up old captures
rm -rf output/images/*

# Use external storage
python src/main.py --output-dir /mnt/external/timelapse
```

#### High CPU Usage
```bash
# Check system resources
htop

# Reduce image quality
# Edit config.yaml: camera.quality: 85

# Use lower resolution
# Edit config.yaml: camera.resolution: [2028, 1520]
```

#### Memory Issues
```bash
# Check memory usage
free -h

# Increase swap space
sudo dphys-swapfile swapoff
sudo nano /etc/dphys-swapfile
# Set CONF_SWAPSIZE=2048
sudo dphys-swapfile setup
sudo dphys-swapfile swapon
```

#### OpenCV Installation Issues
```bash
# Check if OpenCV is installed
python -c "import cv2; print('OpenCV version:', cv2.__version__)"

# If ImportError occurs, install OpenCV:

# Method 1: Install via pip (recommended)
pip install opencv-python>=4.8.0

# Method 2: System-level installation (Raspberry Pi/Linux)
sudo apt update
sudo apt install python3-opencv

# Method 3: If pip install fails, try system packages
sudo apt install python3-opencv python3-opencv-headless

# Verify installation
python -c "import cv2; print('OpenCV installed successfully')"
```

**Note**: If you see warnings like "OpenCV not available for sharpness calculation", the system will continue to function but image quality metrics (sharpness and brightness) will be disabled. This is a graceful fallback that prevents crashes when OpenCV is unavailable.

#### picamera2 Installation Issues
```bash
# Check if picamera2 is installed
python -c "import picamera2; print('picamera2 version:', picamera2.__version__)"

# If ImportError occurs, install picamera2:

# Method 1: Install via apt (RECOMMENDED for Raspberry Pi OS)
sudo apt update
sudo apt install python3-picamera2 python3-libcamera

# Method 2: Install via pip (for non-Raspberry Pi environments)
pip install picamera2==0.3.12

# Method 3: If you have version conflicts, clean up and reinstall
# Remove pip version if apt version is preferred
pip uninstall picamera2
sudo apt install python3-picamera2

# Method 4: If apt version conflicts with pip version
sudo apt remove python3-picamera2
pip install picamera2==0.3.12

# Verify installation
python -c "import picamera2; print('picamera2 installed successfully')"
```

**Important**: 
- **Avoid mixing apt and pip installations** of picamera2 to prevent version conflicts
- **Use apt installation** on Raspberry Pi OS for best compatibility
- **Use pip installation** only when apt is not available
- **Version 0.3.12** is pinned in requirements.txt for consistency

#### Launch Script Issues
```bash
# Check if scripts are executable
ls -la run_capture.sh run_preview.sh

# Make scripts executable if needed
chmod +x run_capture.sh run_preview.sh

# Check lock file status
ls -la /tmp/cinepi_camera.lock

# Remove stale lock file if needed
rm /tmp/cinepi_camera.lock

# Check if another process is using the camera
ps aux | grep -E "(main.py|preview.py)"

#### Background Process Issues
```bash
# Check if background process is running
./run_all.sh --status

# Stop background process if needed
./run_all.sh --stop

# Check background process logs
tail -f timelapse.log

# Remove stale PID file if needed
rm -f timelapse.pid

# Check if process is actually running
ps aux | grep run.py
```

**Common Issues:**
- **"Camera is already in use"**: Another process (capture or preview) is running
- **"Failed to acquire camera lock"**: Lock file exists but process is not running (stale lock)
- **"Permission denied"**: Scripts need to be made executable with `chmod +x`
- **"Device or resource busy"**: Use launch scripts to prevent this error
- **"python3: can't open file"**: Use `run_all.sh` instead of manual nohup to fix directory issues

### Performance Optimization

#### For Long Captures
```yaml
# Optimize for extended operation
camera:
  resolution: [2028, 1520]  # Lower resolution
  quality: 85               # Slightly lower quality
  exposure_mode: "auto"     # Auto exposure

timelapse:
  interval_seconds: 60      # Longer intervals
```

#### For High-Quality Captures
```yaml
# Optimize for quality
camera:
  resolution: [4056, 3040]  # Full resolution
  quality: 95               # High quality
  iso: 100                  # Low ISO for less noise
  exposure_mode: "auto"     # Auto exposure

timelapse:
  interval_seconds: 30      # Shorter intervals
```

### System Monitoring

#### Check System Health
```bash
# Monitor temperature
vcgencmd measure_temp

# Check CPU frequency
vcgencmd measure_clock arm

# Monitor disk usage
watch -n 5 df -h

# Check memory usage
watch -n 5 free -h
```

#### Log Analysis
```bash
# View recent logs
tail -f logs/cinepi.log

# Search for errors
grep ERROR logs/cinepi.log

# Check capture statistics
tail -20 logs/timelapse_metadata.csv
```

## 🧪 Testing

### Run Test Suite
```bash
# Test error handling
python test_error_handling.py

# Expected output: All tests passed
```

### Manual Testing
```bash
# Test configuration
python src/main.py --dry-run --verbose

# Test short capture
python src/main.py --interval 5 --duration 0.1

# Test signal handling (Ctrl-C)
python src/main.py --interval 10
# Press Ctrl-C to test graceful shutdown

# Suppress drift warnings (useful for systems with frequent NTP adjustments)
python src/main.py --suppress-drift --interval 60 --duration 2

## 📁 Project Structure

```
cinepi/
├── src/                    # Source code
│   ├── main.py            # Main entry point
│   ├── capture_utils.py   # Camera operations
│   ├── config_manager.py  # Configuration management
│   └── metrics.py         # Image quality and logging
├── run_all.sh             # Background launch wrapper (fixes nohup directory issues)
├── run_capture.sh         # Timelapse capture launcher (mutual exclusion)
├── run_preview.sh         # Live preview launcher (mutual exclusion)
├── run.py                 # Simple Python launcher
├── preview.py             # Live preview web server
├── config.yaml            # Configuration file
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── test_error_handling.py # Error handling tests
├── timelapse.log          # Background process output (created by run_all.sh)
├── timelapse.pid          # Background process PID (created by run_all.sh)
├── output/               # Captured images
│   └── images/
└── logs/                 # Log files
    ├── cinepi.log
    └── timelapse_metadata.csv
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section above
2. Review the logs in `logs/cinepi.log`
3. Run the test suite: `python test_error_handling.py`
4. Create an issue with detailed error information

## 🔄 Version History

- **v1.0.0**: Initial release with comprehensive error handling
- Features: Signal handling, disk space monitoring, CSV integrity protection
- Hardware: Raspberry Pi 5 + HQ Camera support
- Quality: Real-time image analysis and metadata logging
