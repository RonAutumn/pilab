#!/bin/bash

# CinePi Dashboard - Libcamera Installation Fix Script
# This script fixes the "No module named 'libcamera'" error on Raspberry Pi

set -e  # Exit on any error

echo "🔧 CinePi Dashboard - Libcamera Installation Fix"
echo "================================================"

# Check if running on Raspberry Pi
if ! grep -q "Raspberry Pi" /proc/cpuinfo 2>/dev/null; then
    echo "❌ This script should be run on a Raspberry Pi"
    exit 1
fi

echo "✅ Running on Raspberry Pi"

# Step 1: Update system packages
echo ""
echo "📦 Step 1: Updating system packages..."
sudo apt update && sudo apt upgrade -y
echo "✅ System packages updated"

# Step 2: Check camera interface status
echo ""
echo "📷 Step 2: Checking camera interface status..."
if ! grep -q "camera_auto_detect=1" /boot/firmware/config.txt 2>/dev/null; then
    echo "⚠️  Camera interface not enabled in config.txt"
    echo "   Please run: sudo raspi-config"
    echo "   Navigate to: Interface Options → Camera → Enable"
    echo "   Then reboot and run this script again"
    echo ""
    read -p "Press Enter to continue anyway, or Ctrl+C to exit..."
else
    echo "✅ Camera interface is enabled in config.txt"
fi

# Step 3: Install libcamera dependencies
echo ""
echo "📦 Step 3: Installing libcamera dependencies..."
sudo apt install -y python3-libcamera python3-kms++ python3-prctl libatlas-base-dev ffmpeg
echo "✅ Libcamera dependencies installed"

# Step 4: Install Picamera2
echo ""
echo "📦 Step 4: Installing Picamera2..."
sudo apt install -y python3-picamera2
echo "✅ Picamera2 installed"

# Step 5: Test Python imports
echo ""
echo "🐍 Step 5: Testing Python imports..."
if python3 -c "import libcamera; from picamera2 import Picamera2; print('✅ Libcamera and Picamera2 imports successful')" 2>/dev/null; then
    echo "✅ Python imports successful"
else
    echo "❌ Python imports failed"
    echo "   Trying alternative installation method..."
    pip3 install numpy --upgrade
    pip3 install picamera2
    echo "✅ Alternative installation completed"
fi

# Step 6: Test camera functionality
echo ""
echo "📷 Step 6: Testing camera functionality..."
echo "   Testing libcamera-hello..."
if command -v libcamera-hello >/dev/null 2>&1; then
    echo "   libcamera-hello is available"
    echo "   Run 'libcamera-hello' to test camera preview"
else
    echo "   libcamera-hello not found"
fi

echo "   Testing libcamera-still..."
if command -v libcamera-still >/dev/null 2>&1; then
    echo "   libcamera-still is available"
    echo "   Run 'libcamera-still -o test.jpg' to capture test image"
else
    echo "   libcamera-still not found"
fi

# Step 7: Test Python camera initialization
echo ""
echo "🐍 Step 7: Testing Python camera initialization..."
python3 -c "
try:
    from picamera2 import Picamera2
    picam2 = Picamera2()
    print('✅ Picamera2 initialization successful')
    
    # Try to start camera
    config = picam2.create_still_configuration()
    picam2.configure(config)
    picam2.start()
    print('✅ Camera started successfully')
    
    # Stop camera
    picam2.stop()
    print('✅ Camera stopped successfully')
    
except Exception as e:
    print(f'❌ Camera test failed: {e}')
    print('   This might be due to hardware issues or camera not connected')
"

echo ""
echo "🎉 Libcamera installation fix completed!"
echo ""
echo "Next steps:"
echo "1. If camera tests failed, check physical camera connection"
echo "2. Run the CinePi dashboard to test camera integration"
echo "3. Check dashboard logs for any remaining camera issues"
echo ""
echo "Useful commands:"
echo "- Test camera preview: libcamera-hello"
echo "- Capture test image: libcamera-still -o test.jpg"
echo "- Check camera devices: ls /dev/video*"
echo "- Check camera logs: dmesg | grep -i camera" 