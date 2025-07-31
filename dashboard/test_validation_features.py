#!/usr/bin/env python3
"""
Test script for Enhanced Real-time YAML Validation Features

This script tests the advanced validation features including Monaco Editor markers,
detailed error reporting, and schema validation.
"""

import requests
import json
import yaml

# Configuration
BASE_URL = 'http://localhost:5000'
API_BASE = f'{BASE_URL}/api/editor'

def test_validation_features():
    """Test enhanced validation features"""
    print("Testing Enhanced Real-time YAML Validation Features...")
    print("=" * 60)
    
    # Test 1: Valid configuration with all required fields
    print("\n1. Testing valid configuration with all required fields")
    valid_config = """
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
    
    test_validation(valid_config, "valid", "Complete valid configuration")
    
    # Test 2: Missing required sections
    print("\n2. Testing missing required sections")
    missing_sections = """
camera:
  exposure: auto
  iso: 400
  resolution: 4056x3040
  gain: 2.0
# Missing capture and storage sections
"""
    
    test_validation(missing_sections, "invalid", "Missing required sections")
    
    # Test 3: Invalid camera settings
    print("\n3. Testing invalid camera settings")
    invalid_camera = """
camera:
  exposure: invalid_mode
  iso: 999
  resolution: invalid_resolution
  gain: 10.0
capture:
  interval: 30
storage:
  path: /opt/cinepi/captures
"""
    
    test_validation(invalid_camera, "invalid", "Invalid camera settings")
    
    # Test 4: Missing required camera fields
    print("\n4. Testing missing required camera fields")
    missing_camera_fields = """
camera:
  exposure: auto
  # Missing iso and resolution
capture:
  interval: 30
storage:
  path: /opt/cinepi/captures
"""
    
    test_validation(missing_camera_fields, "invalid", "Missing required camera fields")
    
    # Test 5: Invalid capture settings
    print("\n5. Testing invalid capture settings")
    invalid_capture = """
camera:
  exposure: auto
  iso: 400
  resolution: 4056x3040
capture:
  interval: -5
  format: invalid_format
  quality: 150
storage:
  path: /opt/cinepi/captures
"""
    
    test_validation(invalid_capture, "invalid", "Invalid capture settings")
    
    # Test 6: YAML syntax error
    print("\n6. Testing YAML syntax error")
    syntax_error = """
camera:
  exposure: auto
  iso: 400
  resolution: 4056x3040
capture:
  interval: 30
  settings: [unclosed bracket
storage:
  path: /opt/cinepi/captures
"""
    
    test_validation(syntax_error, "invalid", "YAML syntax error")
    
    # Test 7: Empty configuration
    print("\n7. Testing empty configuration")
    empty_config = ""
    
    test_validation(empty_config, "invalid", "Empty configuration")
    
    # Test 8: Partial configuration
    print("\n8. Testing partial configuration")
    partial_config = """
camera:
  exposure: auto
  iso: 400
  resolution: 4056x3040
  gain: 2.0
capture:
  interval: 30
  format: jpg
  quality: 95
# Missing storage section
"""
    
    test_validation(partial_config, "invalid", "Partial configuration")

def test_validation(content, expected_result, description):
    """Test validation with specific content"""
    try:
        response = requests.post(f'{API_BASE}/validate', 
                               json={'content': content})
        
        if response.status_code == 200:
            data = response.json()
            result = "valid" if data.get('valid') else "invalid"
            
            if result == expected_result:
                print(f"✓ {description}: {result}")
                
                if not data.get('valid'):
                    if data.get('errors'):
                        print(f"  Errors: {len(data['errors'])} validation errors")
                        for i, error in enumerate(data['errors'][:3]):  # Show first 3
                            print(f"    {i+1}. {error}")
                    elif data.get('error'):
                        print(f"  Error: {data['error']}")
            else:
                print(f"✗ {description}: Expected {expected_result}, got {result}")
        else:
            print(f"✗ {description}: HTTP Error {response.status_code}")
            
    except Exception as e:
        print(f"✗ {description}: Exception - {e}")

def test_monaco_editor_features():
    """Test Monaco Editor specific features"""
    print("\nTesting Monaco Editor Features...")
    print("=" * 40)
    
    try:
        response = requests.get(f'{BASE_URL}/editor')
        
        if response.status_code == 200:
            content = response.text
            
            # Check for Monaco Editor features
            features = [
                ('monaco.editor.create', 'Monaco Editor initialization'),
                ('setModelMarkers', 'Error markers support'),
                ('yamlDefaults.setDiagnosticsOptions', 'YAML validation schema'),
                ('MarkerSeverity.Error', 'Error severity markers'),
                ('validationTimer', 'Debounced validation'),
                ('clearValidationMarkers', 'Marker cleanup'),
                ('addValidationMarkers', 'Marker addition')
            ]
            
            for feature, description in features:
                if feature in content:
                    print(f"✓ {description}")
                else:
                    print(f"✗ {description} - Not found")
        else:
            print(f"✗ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Exception: {e}")

def test_error_detection():
    """Test specific error detection capabilities"""
    print("\nTesting Error Detection Capabilities...")
    print("=" * 45)
    
    # Test line number extraction
    print("\n1. Testing line number extraction from YAML errors")
    yaml_with_line_error = """
camera:
  exposure: auto
  iso: 400
  resolution: 4056x3040
capture:
  interval: 30
  settings: [unclosed bracket
storage:
  path: /opt/cinepi/captures
"""
    
    try:
        response = requests.post(f'{API_BASE}/validate', 
                               json={'content': yaml_with_line_error})
        
        if response.status_code == 200:
            data = response.json()
            if not data.get('valid') and data.get('error'):
                error = data['error']
                print(f"✓ YAML syntax error detected")
                print(f"  Error: {error}")
                
                # Check if line number is mentioned
                if 'line' in error.lower():
                    print(f"  ✓ Line number information included")
                else:
                    print(f"  ✗ Line number information missing")
        else:
            print(f"✗ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Exception: {e}")
    
    # Test multiple error detection
    print("\n2. Testing multiple error detection")
    multiple_errors = """
camera:
  exposure: invalid_mode
  # Missing iso and resolution
capture:
  # Missing interval
storage:
  # Missing path
"""
    
    try:
        response = requests.post(f'{API_BASE}/validate', 
                               json={'content': multiple_errors})
        
        if response.status_code == 200:
            data = response.json()
            if not data.get('valid'):
                error_count = len(data.get('errors', []))
                print(f"✓ Multiple errors detected: {error_count} errors")
                
                if error_count > 1:
                    print(f"  ✓ Multiple error reporting working")
                else:
                    print(f"  ✗ Expected multiple errors, got {error_count}")
        else:
            print(f"✗ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"✗ Exception: {e}")

def main():
    """Main test function"""
    print("Enhanced Real-time YAML Validation Test Suite")
    print("=" * 60)
    
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
    test_validation_features()
    test_monaco_editor_features()
    test_error_detection()
    
    print("\n" + "=" * 60)
    print("Enhanced validation test suite completed!")

if __name__ == '__main__':
    main() 
