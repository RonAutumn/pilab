#!/usr/bin/env python3
"""
Test script for Enhanced Backup and Restore Features

This script tests the advanced backup features including comparison,
deletion, content retrieval, and backup management.
"""

import requests
import json
import yaml
import time

# Configuration
BASE_URL = 'http://localhost:5000'
API_BASE = f'{BASE_URL}/api/editor'

def test_backup_features():
    """Test enhanced backup features"""
    print("Testing Enhanced Backup and Restore Features...")
    print("=" * 60)
    
    # Test 1: Create multiple backups for comparison
    print("\n1. Creating multiple backups for testing")
    
    # Create first backup with original config
    print("   Creating backup 1...")
    response1 = requests.post(f'{API_BASE}/backup')
    if response1.status_code == 200:
        data1 = response1.json()
        if data1.get('success'):
            backup1 = data1.get('backup_file')
            print(f"   ✓ Created backup: {backup1}")
        else:
            print(f"   ✗ Failed to create backup: {data1.get('error')}")
            return
    else:
        print(f"   ✗ HTTP Error: {response1.status_code}")
        return
    
    # Wait a moment
    time.sleep(1)
    
    # Create second backup
    print("   Creating backup 2...")
    response2 = requests.post(f'{API_BASE}/backup')
    if response2.status_code == 200:
        data2 = response2.json()
        if data2.get('success'):
            backup2 = data2.get('backup_file')
            print(f"   ✓ Created backup: {backup2}")
        else:
            print(f"   ✗ Failed to create backup: {data2.get('error')}")
            return
    else:
        print(f"   ✗ HTTP Error: {response2.status_code}")
        return
    
    # Test 2: Get backup content
    print("\n2. Testing backup content retrieval")
    try:
        response = requests.get(f'{API_BASE}/backup/{backup1}')
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✓ Backup content retrieved successfully")
                print(f"   Content length: {len(data.get('content', ''))} characters")
                print(f"   Timestamp: {data.get('timestamp')}")
            else:
                print(f"   ✗ Error: {data.get('error')}")
        else:
            print(f"   ✗ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    
    # Test 3: Compare backups
    print("\n3. Testing backup comparison")
    try:
        response = requests.post(f'{API_BASE}/compare', 
                               json={'backup1': backup1, 'backup2': backup2})
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✓ Backup comparison successful")
                print(f"   Comparing: {data['backup1']['filename']} vs {data['backup2']['filename']}")
                print(f"   Differences found: {len(data.get('differences', []))}")
                
                # Show first few differences
                for i, diff in enumerate(data.get('differences', [])[:3]):
                    print(f"     {i+1}. {diff['type']}: {diff['path']}")
            else:
                print(f"   ✗ Error: {data.get('error')}")
        else:
            print(f"   ✗ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    
    # Test 4: List backups with enhanced metadata
    print("\n4. Testing enhanced backup listing")
    try:
        response = requests.get(f'{API_BASE}/backups')
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                backups = data.get('backups', [])
                print(f"   ✓ Found {len(backups)} backups")
                
                # Show backup details
                for i, backup in enumerate(backups[:3]):
                    print(f"     {i+1}. {backup['name']}")
                    print(f"        Date: {backup['date']}")
                    print(f"        Size: {backup['size']} bytes")
                    if 'preview' in backup:
                        preview = backup['preview']
                        if isinstance(preview, dict):
                            sections = list(preview.keys())
                            print(f"        Sections: {', '.join(sections)}")
            else:
                print(f"   ✗ Error: {data.get('error')}")
        else:
            print(f"   ✗ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    
    # Test 5: Delete backup
    print("\n5. Testing backup deletion")
    try:
        response = requests.delete(f'{API_BASE}/backup/{backup2}')
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✓ Backup deleted successfully: {backup2}")
            else:
                print(f"   ✗ Error: {data.get('error')}")
        else:
            print(f"   ✗ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    
    # Test 6: Verify deletion
    print("\n6. Verifying backup deletion")
    try:
        response = requests.get(f'{API_BASE}/backups')
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                backups = data.get('backups', [])
                backup_names = [b['name'] for b in backups]
                
                if backup2 not in backup_names:
                    print(f"   ✓ Backup {backup2} successfully deleted")
                else:
                    print(f"   ✗ Backup {backup2} still exists")
                
                if backup1 in backup_names:
                    print(f"   ✓ Backup {backup1} still exists")
                else:
                    print(f"   ✗ Backup {backup1} was unexpectedly deleted")
            else:
                print(f"   ✗ Error: {data.get('error')}")
        else:
            print(f"   ✗ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")

def test_backup_validation():
    """Test backup validation and error handling"""
    print("\nTesting Backup Validation and Error Handling...")
    print("=" * 55)
    
    # Test 1: Get non-existent backup
    print("\n1. Testing retrieval of non-existent backup")
    try:
        response = requests.get(f'{API_BASE}/backup/nonexistent_backup.yaml')
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if not data.get('success'):
                print(f"   ✓ Correctly handled non-existent backup")
            else:
                print(f"   ✗ Unexpectedly found non-existent backup")
        else:
            print(f"   ✓ HTTP {response.status_code} for non-existent backup")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    
    # Test 2: Delete non-existent backup
    print("\n2. Testing deletion of non-existent backup")
    try:
        response = requests.delete(f'{API_BASE}/backup/nonexistent_backup.yaml')
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 404:
            print(f"   ✓ Correctly returned 404 for non-existent backup")
        else:
            print(f"   ✗ Unexpected status {response.status_code}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    
    # Test 3: Compare with invalid backup names
    print("\n3. Testing comparison with invalid backup names")
    try:
        response = requests.post(f'{API_BASE}/compare', 
                               json={'backup1': 'invalid1.yaml', 'backup2': 'invalid2.yaml'})
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if not data.get('success'):
                print(f"   ✓ Correctly handled invalid backup names")
            else:
                print(f"   ✗ Unexpectedly compared invalid backups")
        else:
            print(f"   ✓ HTTP {response.status_code} for invalid backup names")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    
    # Test 4: Compare with missing parameters
    print("\n4. Testing comparison with missing parameters")
    try:
        response = requests.post(f'{API_BASE}/compare', 
                               json={'backup1': 'test.yaml'})
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 400:
            print(f"   ✓ Correctly returned 400 for missing parameters")
        else:
            print(f"   ✗ Unexpected status {response.status_code}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")

def test_backup_integration():
    """Test backup integration with configuration changes"""
    print("\nTesting Backup Integration with Configuration Changes...")
    print("=" * 60)
    
    # Test 1: Create backup before configuration change
    print("\n1. Creating backup before configuration change")
    try:
        response = requests.post(f'{API_BASE}/backup')
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                pre_change_backup = data.get('backup_file')
                print(f"   ✓ Created pre-change backup: {pre_change_backup}")
            else:
                print(f"   ✗ Failed to create backup: {data.get('error')}")
                return
        else:
            print(f"   ✗ HTTP Error: {response.status_code}")
            return
    except Exception as e:
        print(f"   ✗ Exception: {e}")
        return
    
    # Test 2: Make configuration change
    print("\n2. Making configuration change")
    modified_config = """
camera:
  exposure: manual
  iso: 800
  resolution: 2028x1520
  gain: 4.0
capture:
  interval: 60
  format: jpg
  quality: 90
storage:
  path: /opt/cinepi/captures
  max_files: 5000
"""
    
    try:
        response = requests.post(f'{API_BASE}/config', 
                               json={'content': modified_config})
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                print(f"   ✓ Configuration updated successfully")
                if data.get('backup_file'):
                    print(f"   Auto-backup created: {data.get('backup_file')}")
            else:
                print(f"   ✗ Error: {data.get('error')}")
        else:
            print(f"   ✗ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")
    
    # Test 3: Create backup after configuration change
    print("\n3. Creating backup after configuration change")
    try:
        response = requests.post(f'{API_BASE}/backup')
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                post_change_backup = data.get('backup_file')
                print(f"   ✓ Created post-change backup: {post_change_backup}")
            else:
                print(f"   ✗ Failed to create backup: {data.get('error')}")
                return
        else:
            print(f"   ✗ HTTP Error: {response.status_code}")
            return
    except Exception as e:
        print(f"   ✗ Exception: {e}")
        return
    
    # Test 4: Compare pre and post change backups
    print("\n4. Comparing pre and post change backups")
    try:
        response = requests.post(f'{API_BASE}/compare', 
                               json={'backup1': pre_change_backup, 'backup2': post_change_backup})
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                differences = data.get('differences', [])
                print(f"   ✓ Comparison successful")
                print(f"   Differences found: {len(differences)}")
                
                # Show the differences
                for diff in differences:
                    print(f"     - {diff['type']}: {diff['path']}")
                    if diff['type'] == 'changed':
                        print(f"       {diff['old_value']} → {diff['new_value']}")
            else:
                print(f"   ✗ Error: {data.get('error')}")
        else:
            print(f"   ✗ HTTP Error: {response.status_code}")
    except Exception as e:
        print(f"   ✗ Exception: {e}")

def main():
    """Main test function"""
    print("Enhanced Backup and Restore Test Suite")
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
    test_backup_features()
    test_backup_validation()
    test_backup_integration()
    
    print("\n" + "=" * 60)
    print("Enhanced backup test suite completed!")

if __name__ == '__main__':
    main() 