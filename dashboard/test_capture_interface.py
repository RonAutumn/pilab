#!/usr/bin/env python3
"""
Test script for CinePi Dashboard Capture Control Interface

This script tests the enhanced capture control interface functionality
including the new status indicators, slider, and real-time updates.
"""

import requests
import json
import time
from datetime import datetime

# Dashboard base URL
BASE_URL = "http://localhost:5000"

def test_api_endpoints():
    """Test all capture control API endpoints"""
    print("Testing Capture Control API Endpoints...")
    
    # Test 1: Get system status
    print("\n1. Testing GET /api/status")
    try:
        response = requests.get(f"{BASE_URL}/api/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status endpoint working - Camera: {data.get('camera', {}).get('status', 'Unknown')}")
        else:
            print(f"❌ Status endpoint failed - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Status endpoint error: {e}")
    
    # Test 2: Get capture status
    print("\n2. Testing GET /api/capture/status")
    try:
        response = requests.get(f"{BASE_URL}/api/capture/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Capture status working - Status: {data.get('status', 'Unknown')}")
        else:
            print(f"❌ Capture status failed - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Capture status error: {e}")
    
    # Test 3: Get camera settings
    print("\n3. Testing GET /api/camera/settings")
    try:
        response = requests.get(f"{BASE_URL}/api/camera/settings")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Camera settings working - ISO: {data.get('iso', 'Unknown')}")
        else:
            print(f"❌ Camera settings failed - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Camera settings error: {e}")
    
    # Test 4: Get recent captures
    print("\n4. Testing GET /api/capture/list")
    try:
        response = requests.get(f"{BASE_URL}/api/capture/list?limit=5")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Capture list working - Count: {data.get('count', 0)}")
        else:
            print(f"❌ Capture list failed - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Capture list error: {e}")

def test_capture_controls():
    """Test capture control operations"""
    print("\nTesting Capture Control Operations...")
    
    # Test 1: Start capture
    print("\n1. Testing POST /api/capture/start")
    try:
        response = requests.post(
            f"{BASE_URL}/api/capture/start",
            json={"interval": 30},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Start capture working")
            else:
                print(f"❌ Start capture failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ Start capture failed - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Start capture error: {e}")
    
    # Wait a moment
    time.sleep(2)
    
    # Test 2: Get updated status
    print("\n2. Testing updated capture status")
    try:
        response = requests.get(f"{BASE_URL}/api/capture/status")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Updated status - Status: {data.get('status', 'Unknown')}, Captures: {data.get('captures', 0)}")
        else:
            print(f"❌ Updated status failed - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Updated status error: {e}")
    
    # Test 3: Update interval
    print("\n3. Testing PUT /api/capture/interval")
    try:
        response = requests.put(
            f"{BASE_URL}/api/capture/interval",
            json={"interval": 45},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Update interval working")
            else:
                print(f"❌ Update interval failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ Update interval failed - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Update interval error: {e}")
    
    # Test 4: Take manual snapshot
    print("\n4. Testing POST /api/capture/manual")
    try:
        response = requests.post(
            f"{BASE_URL}/api/capture/manual",
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Manual snapshot working")
            else:
                print(f"❌ Manual snapshot failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ Manual snapshot failed - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Manual snapshot error: {e}")
    
    # Test 5: Stop capture
    print("\n5. Testing POST /api/capture/stop")
    try:
        response = requests.post(
            f"{BASE_URL}/api/capture/stop",
            headers={"Content-Type": "application/json"}
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✅ Stop capture working")
            else:
                print(f"❌ Stop capture failed: {data.get('error', 'Unknown error')}")
        else:
            print(f"❌ Stop capture failed - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Stop capture error: {e}")

def test_ui_features():
    """Test UI-specific features"""
    print("\nTesting UI Features...")
    
    # Test 1: Check if dashboard loads
    print("\n1. Testing dashboard page load")
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code == 200:
            print("✅ Dashboard page loads successfully")
            # Check for new UI elements
            if "intervalSlider" in response.text:
                print("✅ Interval slider found in HTML")
            else:
                print("❌ Interval slider not found in HTML")
            
            if "status-indicators" in response.text:
                print("✅ Status indicators found in HTML")
            else:
                print("❌ Status indicators not found in HTML")
            
            if "progress-container" in response.text:
                print("✅ Progress bar found in HTML")
            else:
                print("❌ Progress bar not found in HTML")
        else:
            print(f"❌ Dashboard page failed - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Dashboard page error: {e}")
    
    # Test 2: Check static files
    print("\n2. Testing static files")
    try:
        response = requests.get(f"{BASE_URL}/static/js/dashboard.js")
        if response.status_code == 200:
            print("✅ Dashboard JavaScript loads")
        else:
            print(f"❌ Dashboard JavaScript failed - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Dashboard JavaScript error: {e}")
    
    try:
        response = requests.get(f"{BASE_URL}/static/css/main.css")
        if response.status_code == 200:
            print("✅ Dashboard CSS loads")
        else:
            print(f"❌ Dashboard CSS failed - Status: {response.status_code}")
    except Exception as e:
        print(f"❌ Dashboard CSS error: {e}")

def main():
    """Main test function"""
    print("=" * 60)
    print("CinePi Dashboard Capture Control Interface Test")
    print("=" * 60)
    print(f"Testing against: {BASE_URL}")
    print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    try:
        # Test API endpoints
        test_api_endpoints()
        
        # Test capture controls
        test_capture_controls()
        
        # Test UI features
        test_ui_features()
        
        print("\n" + "=" * 60)
        print("Test completed!")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n\nTest failed with error: {e}")

if __name__ == "__main__":
    main() 
