#!/usr/bin/env python3
"""
PiLab Audit Logger Utility

This script provides utilities for viewing and managing storage audit logs.
It can be used to analyze storage operations and troubleshoot issues.

Usage:
    python scripts/audit_logger.py [--action ACTION] [--bucket BUCKET] [--since DATE] [--limit N]
    python scripts/audit_logger.py --summary
    python scripts/audit_logger.py --export FILENAME
"""

import argparse
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import csv

# Add src directory to path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from supabase_client import PiLabSupabaseClient, create_pilab_client

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Utility for viewing and managing storage audit logs.
    """
    
    def __init__(self, client: PiLabSupabaseClient):
        self.client = client
    
    def get_audit_logs(self, bucket_id: str = None, action: str = None, 
                      since: datetime = None, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve audit logs with optional filtering.
        
        Args:
            bucket_id: Filter by bucket ID
            action: Filter by action type
            since: Filter by timestamp (get logs since this time)
            limit: Maximum number of logs to return
            
        Returns:
            List of audit log entries
        """
        return self.client.get_audit_logs(bucket_id, action, since, limit)
    
    def get_audit_summary(self, bucket_id: str = None, since: datetime = None) -> Dict[str, Any]:
        """
        Get summary statistics for audit logs.
        
        Args:
            bucket_id: Filter by bucket ID
            since: Filter by timestamp (get logs since this time)
            
        Returns:
            Dictionary with summary statistics
        """
        logs = self.get_audit_logs(bucket_id=bucket_id, since=since, limit=1000)
        
        if not logs:
            return {
                'total_events': 0,
                'events_by_action': {},
                'events_by_bucket': {},
                'recent_activity': {
                    'last_24h': 0,
                    'last_7d': 0,
                    'last_30d': 0
                }
            }
        
        # Count events by action
        events_by_action = {}
        events_by_bucket = {}
        last_24h = 0
        last_7d = 0
        last_30d = 0
        
        now = datetime.utcnow()
        
        for log in logs:
            # Count by action
            action = log.get('action', 'unknown')
            events_by_action[action] = events_by_action.get(action, 0) + 1
            
            # Count by bucket
            bucket = log.get('bucket_id', 'unknown')
            events_by_bucket[bucket] = events_by_bucket.get(bucket, 0) + 1
            
            # Count recent activity
            timestamp_str = log.get('timestamp')
            if timestamp_str:
                try:
                    timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                    if timestamp.tzinfo:
                        timestamp = timestamp.replace(tzinfo=None)
                    
                    if timestamp >= now - timedelta(days=1):
                        last_24h += 1
                    if timestamp >= now - timedelta(days=7):
                        last_7d += 1
                    if timestamp >= now - timedelta(days=30):
                        last_30d += 1
                except Exception as e:
                    logger.warning(f"Could not parse timestamp {timestamp_str}: {e}")
        
        return {
            'total_events': len(logs),
            'events_by_action': events_by_action,
            'events_by_bucket': events_by_bucket,
            'recent_activity': {
                'last_24h': last_24h,
                'last_7d': last_7d,
                'last_30d': last_30d
            }
        }
    
    def export_audit_logs(self, filename: str, bucket_id: str = None, 
                         action: str = None, since: datetime = None) -> bool:
        """
        Export audit logs to CSV file.
        
        Args:
            filename: Output CSV filename
            bucket_id: Filter by bucket ID
            action: Filter by action type
            since: Filter by timestamp
            
        Returns:
            True if successful, False otherwise
        """
        try:
            logs = self.get_audit_logs(bucket_id, action, since, limit=10000)
            
            if not logs:
                logger.warning("No audit logs found to export")
                return False
            
            # Write to CSV
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['id', 'timestamp', 'action', 'object_id', 'bucket_id', 
                             'user_id', 'details', 'created_at']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for log in logs:
                    # Flatten details JSON for CSV
                    row = {field: log.get(field, '') for field in fieldnames}
                    if row['details']:
                        try:
                            details = json.loads(row['details']) if isinstance(row['details'], str) else row['details']
                            row['details'] = json.dumps(details, separators=(',', ':'))
                        except:
                            row['details'] = str(row['details'])
                    writer.writerow(row)
            
            logger.info(f"Exported {len(logs)} audit log entries to {filename}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export audit logs: {e}")
            return False
    
    def print_audit_logs(self, logs: List[Dict[str, Any]], show_details: bool = False):
        """
        Print audit logs in a formatted way.
        
        Args:
            logs: List of audit log entries
            show_details: Whether to show detailed information
        """
        if not logs:
            print("No audit logs found.")
            return
        
        print(f"\n📋 Audit Logs ({len(logs)} entries):")
        print("-" * 80)
        
        for i, log in enumerate(logs, 1):
            timestamp = log.get('timestamp', 'Unknown')
            action = log.get('action', 'Unknown')
            object_id = log.get('object_id', 'Unknown')
            bucket_id = log.get('bucket_id', 'Unknown')
            
            print(f"{i:3d}. {timestamp} | {action:12s} | {object_id:36s} | {bucket_id}")
            
            if show_details:
                details = log.get('details', {})
                if details:
                    if isinstance(details, str):
                        try:
                            details = json.loads(details)
                        except:
                            pass
                    
                    if isinstance(details, dict):
                        for key, value in details.items():
                            print(f"     {key}: {value}")
                    else:
                        print(f"     Details: {details}")
                print()
    
    def print_summary(self, summary: Dict[str, Any]):
        """
        Print audit summary in a formatted way.
        
        Args:
            summary: Summary statistics dictionary
        """
        print(f"\n📊 Audit Log Summary:")
        print("-" * 40)
        print(f"Total Events: {summary['total_events']}")
        
        print(f"\nRecent Activity:")
        recent = summary['recent_activity']
        print(f"  Last 24 hours: {recent['last_24h']}")
        print(f"  Last 7 days:   {recent['last_7d']}")
        print(f"  Last 30 days:  {recent['last_30d']}")
        
        print(f"\nEvents by Action:")
        for action, count in summary['events_by_action'].items():
            print(f"  {action:15s}: {count}")
        
        print(f"\nEvents by Bucket:")
        for bucket, count in summary['events_by_bucket'].items():
            print(f"  {bucket:15s}: {count}")


def parse_datetime(date_str: str) -> datetime:
    """
    Parse datetime string in various formats.
    
    Args:
        date_str: Date string to parse
        
    Returns:
        Parsed datetime object
    """
    formats = [
        '%Y-%m-%d',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%dT%H:%M:%SZ'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Could not parse date string: {date_str}")


def main():
    """Main function for the audit logger utility."""
    parser = argparse.ArgumentParser(
        description='View and manage PiLab storage audit logs'
    )
    parser.add_argument(
        '--action', 
        help='Filter by action type (e.g., upload, delete, soft_delete)'
    )
    parser.add_argument(
        '--bucket', 
        help='Filter by bucket ID'
    )
    parser.add_argument(
        '--since', 
        help='Filter by date (YYYY-MM-DD or YYYY-MM-DD HH:MM:SS)'
    )
    parser.add_argument(
        '--limit', 
        type=int, 
        default=100,
        help='Maximum number of logs to return (default: 100)'
    )
    parser.add_argument(
        '--summary', 
        action='store_true',
        help='Show summary statistics instead of detailed logs'
    )
    parser.add_argument(
        '--export', 
        help='Export logs to CSV file'
    )
    parser.add_argument(
        '--details', 
        action='store_true',
        help='Show detailed information for each log entry'
    )
    
    args = parser.parse_args()
    
    try:
        # Initialize Supabase client
        client = create_pilab_client()
        
        # Test connection
        if not client.test_connection():
            logger.error("Failed to connect to Supabase")
            sys.exit(1)
        
        logger.info("✅ Connected to Supabase successfully")
        
        # Create audit logger
        audit_logger = AuditLogger(client)
        
        # Parse since date if provided
        since_date = None
        if args.since:
            try:
                since_date = parse_datetime(args.since)
            except ValueError as e:
                logger.error(f"Invalid date format: {e}")
                sys.exit(1)
        
        if args.summary:
            # Show summary
            summary = audit_logger.get_audit_summary(args.bucket, since_date)
            audit_logger.print_summary(summary)
            
        elif args.export:
            # Export to CSV
            success = audit_logger.export_audit_logs(
                args.export, args.bucket, args.action, since_date
            )
            if not success:
                sys.exit(1)
                
        else:
            # Show detailed logs
            logs = audit_logger.get_audit_logs(
                args.bucket, args.action, since_date, args.limit
            )
            audit_logger.print_audit_logs(logs, args.details)
        
    except Exception as e:
        logger.error(f"Audit logger failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 