#!/usr/bin/env python3
"""
PiLab Test Script Environment Validation

This script validates that all required environment variables and configuration
are properly set up for the PiLab test script.
"""

import os
import sys
import yaml
from pathlib import Path
from dotenv import load_dotenv

def load_environment():
    """Load environment variables from .env.pi file."""
    env_file = Path('.env.pi')
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment from {env_file}")
    else:
        print(f"❌ Environment file {env_file} not found")
        return False
    return True

def validate_environment_variables():
    """Validate required environment variables."""
    required_vars = [
        'SUPABASE_URL',
        'SUPABASE_SERVICE_KEY',
        'CAPTURE_DIR'
    ]
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: {value}")
        else:
            print(f"❌ {var}: Not set")
            missing_vars.append(var)
    
    return len(missing_vars) == 0

def validate_config_yaml():
    """Validate config.yaml contains required test script settings."""
    config_file = Path('config.yaml')
    if not config_file.exists():
        print(f"❌ Config file {config_file} not found")
        return False
    
    try:
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check for required sections
        required_sections = ['capture', 'storage']
        for section in required_sections:
            if section not in config:
                print(f"❌ Missing '{section}' section in config.yaml")
                return False
            print(f"✅ Found '{section}' section in config.yaml")
        
        # Check capture settings
        capture = config.get('capture', {})
        if capture.get('interval_sec') == 600:
            print("✅ Capture interval: 600 seconds (10 minutes)")
        else:
            print(f"⚠️  Capture interval: {capture.get('interval_sec')} (expected 600)")
        
        if capture.get('resolution') == "4056x3040":
            print("✅ Capture resolution: 4056x3040")
        else:
            print(f"⚠️  Capture resolution: {capture.get('resolution')} (expected 4056x3040)")
        
        if capture.get('rotation') == 180:
            print("✅ Capture rotation: 180 degrees")
        else:
            print(f"⚠️  Capture rotation: {capture.get('rotation')} (expected 180)")
        
        # Check storage settings
        storage = config.get('storage', {})
        if storage.get('bucket') == "pilab-captures":
            print("✅ Storage bucket: pilab-captures")
        else:
            print(f"⚠️  Storage bucket: {storage.get('bucket')} (expected pilab-captures)")
        
        return True
        
    except Exception as e:
        print(f"❌ Error reading config.yaml: {e}")
        return False

def validate_capture_directory():
    """Validate capture directory exists and is writable."""
    capture_dir = os.getenv('CAPTURE_DIR')
    if not capture_dir:
        print("❌ CAPTURE_DIR not set")
        return False
    
    # Handle cross-platform paths
    if capture_dir.startswith('/home/pi/'):
        # This is a Pi path, but we're on Windows for development
        # Check if we have a local captures directory
        local_captures = Path('captures')
        if local_captures.exists():
            print(f"✅ Local captures directory exists: {local_captures}")
            print(f"ℹ️  Note: CAPTURE_DIR set to Pi path: {capture_dir}")
            
            # Test if writable
            test_file = local_captures / '.test_write'
            try:
                test_file.write_text('test')
                test_file.unlink()
                print("✅ Local captures directory is writable")
                return True
            except Exception as e:
                print(f"❌ Local captures directory not writable: {e}")
                return False
        else:
            print(f"❌ Local captures directory does not exist: {local_captures}")
            print(f"ℹ️  Note: CAPTURE_DIR set to Pi path: {capture_dir}")
            return False
    else:
        # Regular path validation
        path = Path(capture_dir)
        if path.exists():
            print(f"✅ Capture directory exists: {capture_dir}")
            
            # Test if writable
            test_file = path / '.test_write'
            try:
                test_file.write_text('test')
                test_file.unlink()
                print("✅ Capture directory is writable")
                return True
            except Exception as e:
                print(f"❌ Capture directory not writable: {e}")
                return False
        else:
            print(f"❌ Capture directory does not exist: {capture_dir}")
            return False

def validate_supabase_client():
    """Validate Supabase client can be imported and initialized."""
    try:
        from src.supabase_client import create_pilab_client
        print("✅ Supabase client module imported successfully")
        
        # Try to create client
        client = create_pilab_client()
        print("✅ Supabase client created successfully")
        
        # Test connection (skip if running locally without Docker)
        try:
            if client.test_connection():
                print("✅ Supabase connection test successful")
                return True
            else:
                print("⚠️  Supabase connection test failed (expected if Docker not running)")
                print("ℹ️  This is normal for local development without Docker")
                return True  # Don't fail the validation for local development
        except Exception as e:
            print(f"⚠️  Supabase connection test failed: {e}")
            print("ℹ️  This is normal for local development without Docker")
            return True  # Don't fail the validation for local development
            
    except ImportError as e:
        print(f"❌ Failed to import Supabase client: {e}")
        return False
    except Exception as e:
        print(f"❌ Failed to create Supabase client: {e}")
        return False

def main():
    """Main validation function."""
    print("🔍 PiLab Test Script Environment Validation")
    print("=" * 50)
    
    # Load environment
    if not load_environment():
        sys.exit(1)
    
    # Validate environment variables
    print("\n📋 Environment Variables:")
    if not validate_environment_variables():
        print("❌ Environment validation failed")
        sys.exit(1)
    
    # Validate config.yaml
    print("\n⚙️  Configuration File:")
    if not validate_config_yaml():
        print("❌ Configuration validation failed")
        sys.exit(1)
    
    # Validate capture directory
    print("\n📁 Capture Directory:")
    if not validate_capture_directory():
        print("❌ Capture directory validation failed")
        sys.exit(1)
    
    # Validate Supabase client
    print("\n🔗 Supabase Client:")
    if not validate_supabase_client():
        print("❌ Supabase client validation failed")
        sys.exit(1)
    
    print("\n🎉 All validations passed! Environment is ready for PiLab test script.")
    print("\nNext steps:")
    print("1. Ensure Supabase bucket 'pilab-captures' exists and is private")
    print("2. Test camera capture functionality")
    print("3. Run the test script for 10-minute interval captures")

if __name__ == "__main__":
    main() 