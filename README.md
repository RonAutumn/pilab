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

## 📋 Hardware Requirements

### Required Components
- **Raspberry Pi 5** (4GB or 8GB RAM recommended)
- **Raspberry Pi HQ Camera** (12MP Sony IMX477 sensor)
- **16mm C-mount lens** (or compatible C-mount lens)
- **MicroSD card** (64GB+ Class 10, UHS-I recommended)
- **Power supply** (5V/3A minimum, 5V/4A recommended)
- **Camera cable** (included with HQ Camera)

### Optional Components
- **Tripod or mounting system** for stable positioning
- **External storage** (USB SSD for extended captures)
- **Cooling solution** (active cooling recommended for long captures)
- **Network connection** (WiFi or Ethernet for remote monitoring)

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

```bash
# Install system dependencies
sudo apt install -y python3-pip python3-venv git

# Install camera libraries
sudo apt install -y python3-picamera2 python3-libcamera

# Create virtual environment (recommended)
python3 -m venv cinepi_env
source cinepi_env/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

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

# Use custom config file
python src/main.py --config my_config.yaml
```

## 📸 Usage Examples

### Quick Start
```bash
# Start a 24-hour timelapse with 30-second intervals
python src/main.py

# Start a 2-hour timelapse with 60-second intervals
python src/main.py --interval 60 --duration 2

# Test configuration without capturing images
python src/main.py --dry-run --verbose
```

### Advanced Usage
```bash
# High-frequency capture (5-second intervals for 1 hour)
python src/main.py --interval 5 --duration 1

# Long-term capture (indefinite duration)
python src/main.py --interval 300 --duration 0

# Custom output location
python src/main.py --output-dir /mnt/ssd/timelapse --interval 60
```

### Background Operation
```bash
# Run in background with nohup
nohup python src/main.py --interval 60 --duration 8 > timelapse.log 2>&1 &

# Check status
tail -f timelapse.log

# Stop gracefully
pkill -f "python src/main.py"
```

## 📊 Output and Logging

### Image Files
- **Location**: `output/images/YYYY-MM-DD/` (daily directories)
- **Naming**: `timelapse_YYYYMMDD_HHMMSS_000001.jpg`
- **Format**: JPEG with configurable quality

### Log Files
- **Application Log**: `logs/cinepi.log`
- **Metadata CSV**: `logs/timelapse_metadata.csv`
- **Console Output**: Real-time progress and status

### CSV Metadata Structure
```csv
timestamp,filename,filepath,capture_number,interval_seconds,sharpness_score,brightness_value,file_size
2024-01-01T12:00:00,timelapse_20240101_120000_000001.jpg,output/images/2024-01-01/timelapse_20240101_120000_000001.jpg,1,30,125.5,128.3,2048576
```

## 🔧 Troubleshooting

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
```

## 📁 Project Structure

```
cinepi/
├── src/                    # Source code
│   ├── main.py            # Main entry point
│   ├── capture_utils.py   # Camera operations
│   ├── config_manager.py  # Configuration management
│   └── metrics.py         # Image quality and logging
├── config.yaml            # Configuration file
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── test_error_handling.py # Error handling tests
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
