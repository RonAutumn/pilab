#!/usr/bin/env python3
"""
Sample Data Import Script for PiLab Dashboard

This script imports sample capture data into the local database to populate
the dashboard with realistic data for testing and demonstration.
"""

import os
import sys
import csv
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add the dashboard directory to the path
sys.path.insert(0, os.path.dirname(__file__))

from local_db_client import LocalDBClient, create_local_client

def create_sample_captures() -> List[Dict[str, Any]]:
    """Create sample capture data based on the CSV structure we saw."""
    
    # Sample data based on the actual Pi captures
    sample_captures = [
        {
            'id': str(uuid.uuid4()),
            'file_path': 'output/images/2025-07-31/timelapse_20250731_002801_919_000001.jpg',
            'shot_type': 'lap',
            'brightness': 45.2,
            'sharpness': 78.5,
            'contrast': 65.3,
            'exposure': 0.033,
            'iso': 100,
            'temperature': 22.5,
            'focus_position': 0.5,
            'frame_hash': 'abc123def456',
            'metadata': json.dumps({
                'resolution': [4056, 3040],
                'quality': 95,
                'capture_duration': 0.5,
                'timing_interval': 30.0,
                'timing_drift': 0.205,
                'cpu_temp': 45.2,
                'memory_usage': 65.3
            }),
            'created_at': datetime(2025, 7, 31, 0, 28, 1)
        },
        {
            'id': str(uuid.uuid4()),
            'file_path': 'output/images/2025-07-31/timelapse_20250731_002831_919_000002.jpg',
            'shot_type': 'lap',
            'brightness': 47.8,
            'sharpness': 82.1,
            'contrast': 68.9,
            'exposure': 0.040,
            'iso': 100,
            'temperature': 22.7,
            'focus_position': 0.5,
            'frame_hash': 'def456ghi789',
            'metadata': json.dumps({
                'resolution': [4056, 3040],
                'quality': 95,
                'capture_duration': 0.6,
                'timing_interval': 30.0,
                'timing_drift': -0.023,
                'cpu_temp': 46.1,
                'memory_usage': 66.2
            }),
            'created_at': datetime(2025, 7, 31, 0, 28, 31)
        },
        {
            'id': str(uuid.uuid4()),
            'file_path': 'output/images/2025-07-31/timelapse_20250731_002901_919_000003.jpg',
            'shot_type': 'lap',
            'brightness': 44.5,
            'sharpness': 75.8,
            'contrast': 62.1,
            'exposure': 0.035,
            'iso': 100,
            'temperature': 22.3,
            'focus_position': 0.5,
            'frame_hash': 'ghi789jkl012',
            'metadata': json.dumps({
                'resolution': [4056, 3040],
                'quality': 95,
                'capture_duration': 0.4,
                'timing_interval': 30.0,
                'timing_drift': -0.007,
                'cpu_temp': 44.8,
                'memory_usage': 64.7
            }),
            'created_at': datetime(2025, 7, 31, 0, 29, 1)
        },
        {
            'id': str(uuid.uuid4()),
            'file_path': 'output/images/2025-07-31/timelapse_20250731_002931_919_000004.jpg',
            'shot_type': 'lap',
            'brightness': 49.2,
            'sharpness': 85.3,
            'contrast': 71.6,
            'exposure': 0.045,
            'iso': 100,
            'temperature': 23.1,
            'focus_position': 0.5,
            'frame_hash': 'jkl012mno345',
            'metadata': json.dumps({
                'resolution': [4056, 3040],
                'quality': 95,
                'capture_duration': 0.7,
                'timing_interval': 30.0,
                'timing_drift': 0.014,
                'cpu_temp': 47.3,
                'memory_usage': 67.8
            }),
            'created_at': datetime(2025, 7, 31, 0, 29, 31)
        },
        {
            'id': str(uuid.uuid4()),
            'file_path': 'output/images/2025-07-31/timelapse_20250731_003001_920_000005.jpg',
            'shot_type': 'lap',
            'brightness': 42.8,
            'sharpness': 72.4,
            'contrast': 59.8,
            'exposure': 0.030,
            'iso': 100,
            'temperature': 21.9,
            'focus_position': 0.5,
            'frame_hash': 'mno345pqr678',
            'metadata': json.dumps({
                'resolution': [4056, 3040],
                'quality': 95,
                'capture_duration': 0.3,
                'timing_interval': 30.0,
                'timing_drift': -0.012,
                'cpu_temp': 43.5,
                'memory_usage': 63.1
            }),
            'created_at': datetime(2025, 7, 31, 0, 30, 1)
        }
    ]
    
    return sample_captures

def create_sample_upload_logs() -> List[Dict[str, Any]]:
    """Create sample upload log data."""
    
    sample_uploads = [
        {
            'id': str(uuid.uuid4()),
            'filename': 'timelapse_20250731_002801_919_000001.jpg',
            'file_path': 'output/images/2025-07-31/timelapse_20250731_002801_919_000001.jpg',
            'file_size': 2191874,
            'status': 'success',
            'bucket_id': 'pilab-dev',
            'object_id': str(uuid.uuid4()),
            'user_id': None,
            'error_message': None,
            'upload_duration_ms': 1250,
            'created_at': datetime(2025, 7, 31, 0, 28, 5),
            'updated_at': datetime(2025, 7, 31, 0, 28, 6)
        },
        {
            'id': str(uuid.uuid4()),
            'filename': 'timelapse_20250731_002831_919_000002.jpg',
            'file_path': 'output/images/2025-07-31/timelapse_20250731_002831_919_000002.jpg',
            'file_size': 2173033,
            'status': 'success',
            'bucket_id': 'pilab-dev',
            'object_id': str(uuid.uuid4()),
            'user_id': None,
            'error_message': None,
            'upload_duration_ms': 1180,
            'created_at': datetime(2025, 7, 31, 0, 28, 35),
            'updated_at': datetime(2025, 7, 31, 0, 28, 36)
        },
        {
            'id': str(uuid.uuid4()),
            'filename': 'timelapse_20250731_002901_919_000003.jpg',
            'file_path': 'output/images/2025-07-31/timelapse_20250731_002901_919_000003.jpg',
            'file_size': 2104293,
            'status': 'success',
            'bucket_id': 'pilab-dev',
            'object_id': str(uuid.uuid4()),
            'user_id': None,
            'error_message': None,
            'upload_duration_ms': 1100,
            'created_at': datetime(2025, 7, 31, 0, 29, 5),
            'updated_at': datetime(2025, 7, 31, 0, 29, 6)
        },
        {
            'id': str(uuid.uuid4()),
            'filename': 'timelapse_20250731_002931_919_000004.jpg',
            'file_path': 'output/images/2025-07-31/timelapse_20250731_002931_919_000004.jpg',
            'file_size': 2088366,
            'status': 'success',
            'bucket_id': 'pilab-dev',
            'object_id': str(uuid.uuid4()),
            'user_id': None,
            'error_message': None,
            'upload_duration_ms': 1050,
            'created_at': datetime(2025, 7, 31, 0, 29, 35),
            'updated_at': datetime(2025, 7, 31, 0, 29, 36)
        },
        {
            'id': str(uuid.uuid4()),
            'filename': 'timelapse_20250731_003001_920_000005.jpg',
            'file_path': 'output/images/2025-07-31/timelapse_20250731_003001_920_000005.jpg',
            'file_size': 2066975,
            'status': 'failed',
            'bucket_id': 'pilab-dev',
            'object_id': None,
            'user_id': None,
            'error_message': 'Network timeout during upload',
            'upload_duration_ms': 5000,
            'created_at': datetime(2025, 7, 31, 0, 30, 5),
            'updated_at': datetime(2025, 7, 31, 0, 30, 10)
        }
    ]
    
    return sample_uploads

def create_sample_audit_logs() -> List[Dict[str, Any]]:
    """Create sample audit log data."""
    
    sample_audits = [
        {
            'id': str(uuid.uuid4()),
            'action': 'upload',
            'object_id': str(uuid.uuid4()),
            'bucket_id': 'pilab-dev',
            'user_id': None,
            'details': json.dumps({
                'filename': 'timelapse_20250731_002801_919_000001.jpg',
                'file_size': 2191874,
                'upload_duration_ms': 1250
            }),
            'created_at': datetime(2025, 7, 31, 0, 28, 6)
        },
        {
            'id': str(uuid.uuid4()),
            'action': 'upload',
            'object_id': str(uuid.uuid4()),
            'bucket_id': 'pilab-dev',
            'user_id': None,
            'details': json.dumps({
                'filename': 'timelapse_20250731_002831_919_000002.jpg',
                'file_size': 2173033,
                'upload_duration_ms': 1180
            }),
            'created_at': datetime(2025, 7, 31, 0, 28, 36)
        },
        {
            'id': str(uuid.uuid4()),
            'action': 'upload',
            'object_id': str(uuid.uuid4()),
            'bucket_id': 'pilab-dev',
            'user_id': None,
            'details': json.dumps({
                'filename': 'timelapse_20250731_003001_920_000005.jpg',
                'file_size': 2066975,
                'error': 'Network timeout during upload'
            }),
            'created_at': datetime(2025, 7, 31, 0, 30, 10)
        },
        {
            'id': str(uuid.uuid4()),
            'action': 'retention_check',
            'object_id': str(uuid.uuid4()),
            'bucket_id': 'pilab-dev',
            'user_id': None,
            'details': json.dumps({
                'files_checked': 45,
                'files_marked_for_deletion': 3,
                'total_size_freed_mb': 15.2
            }),
            'created_at': datetime(2025, 7, 31, 0, 25, 0)
        }
    ]
    
    return sample_audits

def import_sample_data():
    """Import all sample data into the database."""
    
    try:
        # Create database client
        client = create_local_client()
        
        print("✅ Connected to local database")
        
        # Import captures
        captures = create_sample_captures()
        print(f"📸 Importing {len(captures)} sample captures...")
        
        for capture in captures:
            client.insert_capture(capture)
        
        print("✅ Captures imported successfully")
        
        # Import upload logs
        uploads = create_sample_upload_logs()
        print(f"📤 Importing {len(uploads)} sample upload logs...")
        
        for upload in uploads:
            client.insert_upload_log(upload)
        
        print("✅ Upload logs imported successfully")
        
        # Import audit logs
        audits = create_sample_audit_logs()
        print(f"📋 Importing {len(audits)} sample audit logs...")
        
        for audit in audits:
            client.insert_audit_log(audit)
        
        print("✅ Audit logs imported successfully")
        
        print("\n🎉 Sample data import completed successfully!")
        print("The dashboard should now show realistic data.")
        
    except Exception as e:
        print(f"❌ Error importing sample data: {e}")
        return False
    
    return True

if __name__ == '__main__':
    print("🚀 Starting sample data import for PiLab Dashboard...")
    success = import_sample_data()
    
    if success:
        print("\n✅ Sample data import completed!")
        print("You can now start the dashboard to see the sample data.")
    else:
        print("\n❌ Sample data import failed!")
        sys.exit(1) 