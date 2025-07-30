#!/usr/bin/env python3
"""
Test script for CinePi Dashboard Camera Settings

This script tests the camera settings functionality to ensure it works correctly.
"""

import requests
import json
import time
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5000"
API_BASE = f"{BASE_URL}/api"

def test_camera_settings():
    """Test camera settings functionality"""
    print("Testing CinePi Dashboard Camera Settings...")
    print("=" * 50)
    
    # Test 1: Get current settings
    print("\n1. Testing GET /api/camera/settings")
    try:
        response = requests.get(f"{API_BASE}/camera/settings")
        if response.status_code == 200:
            settings = response.json()
            print(f"✓ Current settings: {settings}")
        else:
            print(f"✗ Failed to get settings: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error getting settings: {e}")
        return False
    
    # Test 2: Get supported parameters
    print("\n2. Testing GET /api/camera/parameters")
    try:
        response = requests.get(f"{API_BASE}/camera/parameters")
        if response.status_code == 200:
            parameters = response.json()
            print(f"✓ Supported parameters: {parameters}")
        else:
            print(f"✗ Failed to get parameters: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error getting parameters: {e}")
        return False
    
    # Test 3: Update settings
    print("\n3. Testing PUT /api/camera/settings")
    test_settings = {
        "exposure_mode": "manual",
        "iso": 800,
        "gain": 4.0,
        "resolution": "4056x3040"
    }
    
    try:
        response = requests.put(
            f"{API_BASE}/camera/settings",
            json=test_settings,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✓ Settings updated successfully: {result}")
            else:
                print(f"✗ Settings update failed: {result.get('error')}")
                return False
        else:
            print(f"✗ Failed to update settings: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error updating settings: {e}")
        return False
    
    # Test 4: Verify settings were applied
    print("\n4. Verifying settings were applied")
    try:
        time.sleep(1)  # Give time for settings to apply
        response = requests.get(f"{API_BASE}/camera/settings")
        if response.status_code == 200:
            updated_settings = response.json()
            print(f"✓ Updated settings: {updated_settings}")
            
            # Check if settings match
            for key, value in test_settings.items():
                if updated_settings.get(key) != value:
                    print(f"✗ Setting {key} mismatch: expected {value}, got {updated_settings.get(key)}")
                    return False
            
            print("✓ All settings match expected values")
        else:
            print(f"✗ Failed to verify settings: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error verifying settings: {e}")
        return False
    
    # Test 5: Reset to auto exposure
    print("\n5. Testing reset to auto exposure")
    reset_settings = {
        "exposure_mode": "auto",
        "iso": 400,
        "gain": 2.0,
        "resolution": "4056x3040"
    }
    
    try:
        response = requests.put(
            f"{API_BASE}/camera/settings",
            json=reset_settings,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print(f"✓ Settings reset successfully: {result}")
            else:
                print(f"✗ Settings reset failed: {result.get('error')}")
                return False
        else:
            print(f"✗ Failed to reset settings: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error resetting settings: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✓ All camera settings tests passed!")
    return True

def test_dashboard_ui():
    """Test dashboard UI endpoints"""
    print("\nTesting Dashboard UI...")
    print("=" * 50)
    
    # Test main dashboard page
    print("\n1. Testing main dashboard page")
    try:
        response = requests.get(BASE_URL)
        if response.status_code == 200:
            print("✓ Dashboard page loads successfully")
        else:
            print(f"✗ Dashboard page failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error loading dashboard: {e}")
        return False
    
    # Test system status
    print("\n2. Testing system status")
    try:
        response = requests.get(f"{API_BASE}/status")
        if response.status_code == 200:
            status = response.json()
            print(f"✓ System status: {status}")
        else:
            print(f"✗ System status failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Error getting system status: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✓ All dashboard UI tests passed!")
    return True

def main():
    """Main test function"""
    print("CinePi Dashboard Camera Settings Test Suite")
    print("=" * 60)
    
    # Check if dashboard is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("✗ Dashboard is not running or not accessible")
            print("Please start the dashboard first:")
            print("  cd dashboard")
            print("  python app.py")
            return False
    except Exception as e:
        print("✗ Cannot connect to dashboard")
        print("Please start the dashboard first:")
        print("  cd dashboard")
        print("  python app.py")
        return False
    
    print("✓ Dashboard is running")
    
    # Run tests
    settings_success = test_camera_settings()
    ui_success = test_dashboard_ui()
    
    if settings_success and ui_success:
        print("\n🎉 All tests passed! Camera settings functionality is working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Please check the implementation.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1) 