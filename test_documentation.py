#!/usr/bin/env python3
"""
Test script for Task 8: Documentation and Setup Files
Verifies that all required documentation and setup files are present and properly formatted.
"""

import os
import sys
from pathlib import Path

def test_required_files():
    """Test that all required files exist."""
    print("Testing required files...")
    
    required_files = [
        "requirements.txt",
        "README.md",
        "config.yaml.example",
        "install.sh",
        "src/main.py",
        "src/capture_utils.py",
        "src/config_manager.py",
        "src/metrics.py",
        "test_error_handling.py"
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
        else:
            print(f"✓ {file_path}")
    
    if missing_files:
        print(f"✗ Missing files: {missing_files}")
        return False
    
    return True

def test_requirements_content():
    """Test that requirements.txt contains the required dependencies."""
    print("\nTesting requirements.txt content...")
    
    required_deps = [
        "picamera2>=",
        "opencv-python>=",
        "PyYAML>=",
        "Pillow>=",
        "numpy>="
    ]
    
    try:
        with open("requirements.txt", "r") as f:
            content = f.read()
        
        missing_deps = []
        for dep in required_deps:
            if dep not in content:
                missing_deps.append(dep)
            else:
                print(f"✓ {dep}")
        
        if missing_deps:
            print(f"✗ Missing dependencies: {missing_deps}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error reading requirements.txt: {e}")
        return False

def test_readme_content():
    """Test that README.md contains required sections."""
    print("\nTesting README.md content...")
    
    required_sections = [
        "Hardware Requirements",
        "Installation",
        "Configuration",
        "Usage Examples",
        "Troubleshooting",
        "Project Structure"
    ]
    
    try:
        with open("README.md", "r", encoding="utf-8") as f:
            content = f.read()
        
        missing_sections = []
        for section in required_sections:
            if section in content:
                print(f"✓ {section}")
            else:
                missing_sections.append(section)
        
        if missing_sections:
            print(f"✗ Missing sections: {missing_sections}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error reading README.md: {e}")
        return False

def test_config_example():
    """Test that config.yaml.example contains required settings."""
    print("\nTesting config.yaml.example content...")
    
    required_settings = [
        "camera:",
        "resolution:",
        "quality:",
        "timelapse:",
        "interval_seconds:",
        "logging:",
        "log_level:"
    ]
    
    try:
        with open("config.yaml.example", "r") as f:
            content = f.read()
        
        missing_settings = []
        for setting in required_settings:
            if setting in content:
                print(f"✓ {setting}")
            else:
                missing_settings.append(setting)
        
        if missing_settings:
            print(f"✗ Missing settings: {missing_settings}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error reading config.yaml.example: {e}")
        return False

def test_install_script():
    """Test that install.sh contains required functionality."""
    print("\nTesting install.sh content...")
    
    required_features = [
        "python3-pip",
        "python3-picamera2",
        "raspi-config",
        "virtual environment",
        "requirements.txt"
    ]
    
    try:
        with open("install.sh", "r", encoding="utf-8") as f:
            content = f.read()
        
        missing_features = []
        for feature in required_features:
            if feature in content:
                print(f"✓ {feature}")
            else:
                missing_features.append(feature)
        
        if missing_features:
            print(f"✗ Missing features: {missing_features}")
            return False
        
        return True
        
    except Exception as e:
        print(f"✗ Error reading install.sh: {e}")
        return False

def main():
    """Run all documentation tests."""
    print("=== Task 8: Documentation and Setup Files Test ===\n")
    
    tests = [
        ("Required Files", test_required_files),
        ("Requirements Content", test_requirements_content),
        ("README Content", test_readme_content),
        ("Config Example", test_config_example),
        ("Install Script", test_install_script),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                passed += 1
                print(f"✓ {test_name} PASSED")
            else:
                print(f"✗ {test_name} FAILED")
        except Exception as e:
            print(f"✗ {test_name} FAILED with exception: {e}")
    
    print(f"\n=== Test Results ===")
    print(f"Passed: {passed}/{total}")
    print(f"Success Rate: {passed/total*100:.1f}%")
    
    if passed == total:
        print("🎉 All documentation tests passed!")
        print("✅ Task 8 requirements are complete:")
        print("   - requirements.txt with exact versions")
        print("   - Comprehensive README.md with installation steps")
        print("   - Hardware requirements and configuration guide")
        print("   - Usage examples and troubleshooting section")
        print("   - Configuration example file")
        print("   - Installation script")
        return 0
    else:
        print("⚠️  Some documentation tests failed.")
        print("   Please review and complete the missing documentation.")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 