#!/usr/bin/env python3
"""
Test script for libcamera installation and camera functionality
This script verifies that libcamera and Picamera2 are properly installed and working.
"""

import sys
import subprocess
import platform

def test_imports():
    """Test if libcamera and Picamera2 can be imported."""
    print("🔍 Testing Python imports...")
    
    try:
        import libcamera
        print("✅ libcamera imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import libcamera: {e}")
        return False
    
    try:
        from picamera2 import Picamera2
        print("✅ Picamera2 imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import Picamera2: {e}")
        return False
    
    return True

def test_camera_initialization():
    """Test if camera can be initialized."""
    print("\n🔍 Testing camera initialization...")
    
    try:
        from picamera2 import Picamera2
        picam2 = Picamera2()
        print("✅ Picamera2 object created successfully")
        
        # Try to get camera info
        camera_info = picam2.camera_properties
        print(f"✅ Camera properties: {camera_info}")
        
        return True
    except Exception as e:
        print(f"❌ Camera initialization failed: {e}")
        return False

def test_camera_start_stop():
    """Test if camera can be started and stopped."""
    print("\n🔍 Testing camera start/stop...")
    
    try:
        from picamera2 import Picamera2
        picam2 = Picamera2()
        
        # Create configuration
        config = picam2.create_still_configuration()
        picam2.configure(config)
        print("✅ Camera configured successfully")
        
        # Start camera
        picam2.start()
        print("✅ Camera started successfully")
        
        # Stop camera
        picam2.stop()
        print("✅ Camera stopped successfully")
        
        return True
    except Exception as e:
        print(f"❌ Camera start/stop test failed: {e}")
        return False

def test_command_line_tools():
    """Test if command line tools are available."""
    print("\n🔍 Testing command line tools...")
    
    tools = ['libcamera-hello', 'libcamera-still']
    available_tools = []
    
    for tool in tools:
        try:
            result = subprocess.run([tool, '--help'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"✅ {tool} is available")
                available_tools.append(tool)
            else:
                print(f"❌ {tool} returned error code {result.returncode}")
        except FileNotFoundError:
            print(f"❌ {tool} not found")
        except subprocess.TimeoutExpired:
            print(f"⚠️  {tool} timed out (this might be normal)")
            available_tools.append(tool)
        except Exception as e:
            print(f"❌ Error testing {tool}: {e}")
    
    return len(available_tools) > 0

def check_system_info():
    """Check system information."""
    print("🔍 System Information:")
    print(f"   Platform: {platform.platform()}")
    print(f"   Python version: {sys.version}")
    print(f"   Architecture: {platform.machine()}")
    
    # Check if running on Raspberry Pi
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
            if 'Raspberry Pi' in cpuinfo:
                print("   ✅ Running on Raspberry Pi")
                return True
            else:
                print("   ⚠️  Not running on Raspberry Pi")
                return False
    except FileNotFoundError:
        print("   ⚠️  Cannot determine if running on Raspberry Pi")
        return False

def main():
    """Main test function."""
    print("🔧 CinePi Dashboard - Libcamera Installation Test")
    print("=" * 50)
    
    # Check system info
    is_raspberry_pi = check_system_info()
    
    # Test imports
    imports_ok = test_imports()
    
    # Test command line tools
    tools_ok = test_command_line_tools()
    
    # Test camera functionality (only if imports work)
    camera_ok = False
    if imports_ok:
        camera_ok = test_camera_initialization()
        if camera_ok:
            camera_ok = test_camera_start_stop()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    print(f"   System: {'Raspberry Pi' if is_raspberry_pi else 'Other'}")
    print(f"   Python imports: {'✅ PASS' if imports_ok else '❌ FAIL'}")
    print(f"   Command line tools: {'✅ PASS' if tools_ok else '❌ FAIL'}")
    print(f"   Camera functionality: {'✅ PASS' if camera_ok else '❌ FAIL'}")
    
    if imports_ok and tools_ok and camera_ok:
        print("\n🎉 All tests passed! Libcamera installation is working correctly.")
        print("   You can now run the CinePi dashboard.")
        return True
    else:
        print("\n❌ Some tests failed. Please check the installation:")
        if not imports_ok:
            print("   - Run: sudo apt install -y python3-libcamera python3-picamera2")
        if not tools_ok:
            print("   - Run: sudo apt install -y libcamera-tools")
        if not camera_ok:
            print("   - Check camera hardware connection")
            print("   - Enable camera interface: sudo raspi-config")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 