#!/usr/bin/env python3
"""
Test script for YAML Configuration Editor

This script tests the YAML editor endpoints and functionality.
"""

import requests
import json
import yaml
import time

# Configuration
BASE_URL = 'http://localhost:5000'
API_BASE = f'{BASE_URL}/api/editor'

def test_editor_endpoints():
    """Test all YAML editor endpoints"""
    print("Testing YAML Editor Endpoints...")
    print("=" * 50)
    
    # Test 1: Get configuration for editor
    print("\n1. Testing GET /api/editor/config")
    try:
        response = requests.get(f'{API_BASE}/config')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✓ Configuration loaded successfully")
                print(f"Content length: {len(data.get('content', ''))} characters")
                print(f"Last modified: {data.get('last_modified')}")
            else:
                print(f"✗ Error: {data.get('error')}")
        else:
            print(f"✗ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"✗ Exception: {e}")
    
    # Test 2: Validate YAML content
    print("\n2. Testing POST /api/editor/validate")
    test_yaml = """
camera:
  exposure: auto
  iso: 400
  resolution: 4056x3040
  gain: 2.0
capture:
  interval: 30
  format: jpg
  quality: 95
storage:
  path: /opt/cinepi/captures
  max_files: 10000
"""
    
    try:
        response = requests.post(f'{API_BASE}/validate', 
                               json={'content': test_yaml})
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('valid'):
                print("✓ YAML validation successful")
            else:
                print(f"✗ Validation failed: {data.get('errors', data.get('error'))}")
        else:
            print(f"✗ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"✗ Exception: {e}")
    
    # Test 3: Validate invalid YAML
    print("\n3. Testing POST /api/editor/validate (invalid YAML)")
    invalid_yaml = """
camera:
  exposure: auto
  iso: 400
  resolution: 4056x3040
  gain: 2.0
capture:
  interval: 30
  format: jpg
  quality: 95
storage:
  path: /opt/cinepi/captures
  max_files: 10000
  invalid: [unclosed bracket
"""
    
    try:
        response = requests.post(f'{API_BASE}/validate', 
                               json={'content': invalid_yaml})
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if not data.get('valid'):
                print("✓ Invalid YAML correctly detected")
                print(f"Error: {data.get('error')}")
            else:
                print("✗ Invalid YAML was not detected")
        else:
            print(f"✗ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"✗ Exception: {e}")
    
    # Test 4: List backups
    print("\n4. Testing GET /api/editor/backups")
    try:
        response = requests.get(f'{API_BASE}/backups')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                backups = data.get('backups', [])
                print(f"✓ Found {len(backups)} backups")
                for backup in backups[:3]:  # Show first 3
                    print(f"  - {backup.get('name')} ({backup.get('date')})")
            else:
                print(f"✗ Error: {data.get('error')}")
        else:
            print(f"✗ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"✗ Exception: {e}")
    
    # Test 5: Create backup
    print("\n5. Testing POST /api/editor/backup")
    try:
        response = requests.post(f'{API_BASE}/backup')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✓ Backup created successfully")
                print(f"Backup file: {data.get('backup_file')}")
            else:
                print(f"✗ Error: {data.get('error')}")
        else:
            print(f"✗ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"✗ Exception: {e}")
    
    # Test 6: Save configuration (if validation passes)
    print("\n6. Testing POST /api/editor/config (save)")
    try:
        response = requests.post(f'{API_BASE}/config', 
                               json={'content': test_yaml})
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print("✓ Configuration saved successfully")
                if data.get('backup_file'):
                    print(f"Backup created: {data.get('backup_file')}")
            else:
                print(f"✗ Error: {data.get('error')}")
        else:
            print(f"✗ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"✗ Exception: {e}")

def test_editor_page():
    """Test the editor page loads correctly"""
    print("\nTesting Editor Page...")
    print("=" * 30)
    
    try:
        response = requests.get(f'{BASE_URL}/editor')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("✓ Editor page loads successfully")
            content = response.text
            if 'monaco-editor' in content:
                print("✓ Monaco Editor integration found")
            else:
                print("✗ Monaco Editor integration not found")
            
            if 'Configuration Editor' in content:
                print("✓ Editor title found")
            else:
                print("✗ Editor title not found")
        else:
            print(f"✗ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"✗ Exception: {e}")

def test_dashboard_integration():
    """Test dashboard integration"""
    print("\nTesting Dashboard Integration...")
    print("=" * 35)
    
    try:
        response = requests.get(f'{BASE_URL}/')
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            content = response.text
            if '/editor' in content:
                print("✓ Editor link found in dashboard")
            else:
                print("✗ Editor link not found in dashboard")
            
            if 'Configuration Management' in content:
                print("✓ Configuration Management section found")
            else:
                print("✗ Configuration Management section not found")
        else:
            print(f"✗ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"✗ Exception: {e}")

def main():
    """Main test function"""
    print("CinePi YAML Editor Test Suite")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get(f'{BASE_URL}/health', timeout=5)
        if response.status_code == 200:
            print("✓ Dashboard server is running")
        else:
            print("✗ Dashboard server is not responding correctly")
            return
    except Exception as e:
        print(f"✗ Cannot connect to dashboard server: {e}")
        print("Make sure the dashboard is running on http://localhost:5000")
        return
    
    # Run tests
    test_editor_endpoints()
    test_editor_page()
    test_dashboard_integration()
    
    print("\n" + "=" * 50)
    print("Test suite completed!")

if __name__ == '__main__':
    main() 