#!/bin/bash

# CinePi Timelapse System Installation Script
# This script automates the installation process for Raspberry Pi 5

set -e  # Exit on any error

echo "🎬 CinePi Timelapse System Installation"
echo "========================================"

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo; then
    echo "⚠️  Warning: This script is designed for Raspberry Pi systems"
    echo "   It may not work correctly on other platforms"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if running as root
if [[ $EUID -eq 0 ]]; then
    echo "❌ Please do not run this script as root"
    echo "   Run as a regular user with sudo privileges"
    exit 1
fi

# Update system
echo "📦 Updating system packages..."
sudo apt update
sudo apt upgrade -y

# Install system dependencies
echo "🔧 Installing system dependencies..."
sudo apt install -y python3-pip python3-venv git python3-picamera2 python3-libcamera

# Enable camera interface
echo "📷 Enabling camera interface..."
sudo raspi-config nonint do_camera 0

# Enable I2C (optional, for future sensor integration)
echo "🔌 Enabling I2C interface..."
sudo raspi-config nonint do_i2c 0

# Create virtual environment
echo "🐍 Creating Python virtual environment..."
python3 -m venv cinepi_env
source cinepi_env/bin/activate

# Install Python dependencies
echo "📚 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p output/images

# Create logs directory for application logging
# This ensures the logging structure is always present for metadata logging and system logs
echo "📝 Creating logs directory..."
mkdir -p logs
chmod 775 logs  # Set appropriate permissions for logging

# Copy configuration if it doesn't exist
if [ ! -f config.yaml ]; then
    echo "⚙️  Creating configuration file..."
    cp config.yaml.example config.yaml
    echo "   Edit config.yaml to customize settings"
fi

# Set proper permissions
echo "🔐 Setting permissions..."
chmod +x src/main.py
chmod +x test_error_handling.py

# Test installation
echo "🧪 Testing installation..."
python test_error_handling.py

echo ""
echo "✅ Installation completed successfully!"
echo ""
echo "🎯 Next steps:"
echo "   1. Edit config.yaml with your settings"
echo "   2. Connect your Raspberry Pi HQ Camera"
echo "   3. Run: python src/main.py --dry-run"
echo "   4. Start capturing: python src/main.py"
echo ""
echo "📖 For more information, see README.md"
echo "🆘 For troubleshooting, see the troubleshooting section in README.md"
echo ""
echo "🔄 Reboot recommended to ensure all changes take effect:"
echo "   sudo reboot"
