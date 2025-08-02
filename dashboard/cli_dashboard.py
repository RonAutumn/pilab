#!/usr/bin/env python3
"""
PiLab CLI Dashboard

A command-line dashboard for monitoring PiLab storage, captures, and metrics
with real-time updates, interactive features, and comprehensive error handling.
"""

import os
import sys
import time
import json
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))

from supabase_client import PiLabSupabaseClient, create_pilab_client
from logging_utils import get_logger, log_with_context, generate_correlation_id
from retry import retry_on_supabase_error, RetryError


class CLIDashboard:
    """Command-line dashboard for PiLab monitoring."""
    
    def __init__(self):
        """Initialize the CLI dashboard."""
        self.client: Optional[PiLabSupabaseClient] = None
        self.running = False
        self.update_interval = 30  # seconds
        self.logger = get_logger('pilab.cli_dashboard')
        self.correlation_id = generate_correlation_id()
        
    @retry_on_supabase_error(max_attempts=3)
    def initialize_client(self) -> bool:
        """Initialize the Supabase client with retry logic."""
        try:
            self.client = create_pilab_client()
            if self.client.test_connection():
                log_with_context(self.logger, 'INFO', "Successfully connected to PiLab Supabase", 
                               correlation_id=self.correlation_id)
                print("✅ Connected to PiLab Supabase")
                return True
            else:
                log_with_context(self.logger, 'ERROR', "Failed to connect to Supabase", 
                               correlation_id=self.correlation_id)
                print("❌ Failed to connect to Supabase")
                return False
        except RetryError as e:
            log_with_context(self.logger, 'ERROR', f"Failed to initialize client after retries: {e}", 
                           correlation_id=self.correlation_id, attempts=e.attempts)
            print(f"❌ Failed to connect after {e.attempts} attempts: {e}")
            return False
        except Exception as e:
            log_with_context(self.logger, 'ERROR', f"Unexpected error initializing client: {e}", 
                           correlation_id=self.correlation_id, error=str(e))
            print(f"❌ Error initializing client: {e}")
            return False
    
    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def print_header(self):
        """Print the dashboard header."""
        print("=" * 80)
        print("🔬 PiLab CLI Dashboard")
        print("=" * 80)
        print(f"Last Update: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("-" * 80)
    
    def print_storage_usage(self):
        """Display storage usage information."""
        try:
            usage = self.client.get_storage_usage('pilab-dev')
            if 'error' in usage:
                print("❌ Storage Usage: Error retrieving data")
                return
            
            print("💾 STORAGE USAGE")
            print("-" * 40)
            print(f"Total Files:     {usage.get('total_files', 0):>10}")
            print(f"Total Size:      {usage.get('total_size_mb', 0):>8.2f} MB")
            print(f"Oldest File:     {usage.get('oldest_file', 'N/A'):>10}")
            print(f"Newest File:     {usage.get('newest_file', 'N/A'):>10}")
            print()
            
        except Exception as e:
            print(f"❌ Storage Usage: {e}")
    
    def print_upload_metrics(self):
        """Display upload metrics."""
        try:
            # Query upload metrics
            query = """
                SELECT 
                    COUNT(*) as total_uploads,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_uploads,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_uploads,
                    AVG(CASE WHEN status = 'success' THEN file_size END) as avg_file_size,
                    MAX(created_at) as last_upload
                FROM upload_logs
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """
            
            result = self.client.client.rpc('exec_sql', {
                'query': query, 
                'params': []
            }).execute()
            
            if result.data:
                data = result.data[0]
                success_rate = (data['successful_uploads'] / data['total_uploads'] * 100) if data['total_uploads'] > 0 else 0
                
                print("📤 UPLOAD METRICS (24h)")
                print("-" * 40)
                print(f"Total Uploads:   {data['total_uploads']:>10}")
                print(f"Successful:      {data['successful_uploads']:>10}")
                print(f"Failed:          {data['failed_uploads']:>10}")
                print(f"Success Rate:    {success_rate:>8.1f}%")
                print(f"Avg File Size:   {data['avg_file_size'] / (1024 * 1024) if data['avg_file_size'] else 0:>8.2f} MB")
                print(f"Last Upload:     {data['last_upload'] or 'N/A':>10}")
                print()
            else:
                print("📤 UPLOAD METRICS (24h)")
                print("-" * 40)
                print("No upload data available")
                print()
                
        except Exception as e:
            print(f"❌ Upload Metrics: {e}")
    
    def print_recent_captures(self, limit: int = 5):
        """Display recent captures."""
        try:
            query = """
                SELECT 
                    c.id,
                    c.filename,
                    c.created_at,
                    c.file_size,
                    COALESCE(c.metadata->>'exposure_time', 'N/A') as exposure_time,
                    COALESCE(c.metadata->>'iso', 'N/A') as iso,
                    COALESCE(c.metadata->>'aperture', 'N/A') as aperture
                FROM captures c
                WHERE c.deleted_at IS NULL
                ORDER BY c.created_at DESC
                LIMIT %s
            """
            
            result = self.client.client.rpc('exec_sql', {
                'query': query, 
                'params': [limit]
            }).execute()
            
            print(f"📸 RECENT CAPTURES (Last {limit})")
            print("-" * 40)
            
            if result.data:
                for i, capture in enumerate(result.data, 1):
                    file_size_mb = capture['file_size'] / (1024 * 1024) if capture['file_size'] else 0
                    created_at = datetime.fromisoformat(capture['created_at'].replace('Z', '+00:00'))
                    
                    print(f"{i}. {capture['filename']}")
                    print(f"   Size: {file_size_mb:.2f} MB | {capture['exposure_time']} | ISO {capture['iso']} | f/{capture['aperture']}")
                    print(f"   Created: {created_at.strftime('%Y-%m-%d %H:%M:%S')}")
                    print()
            else:
                print("No captures found")
                print()
                
        except Exception as e:
            print(f"❌ Recent Captures: {e}")
    
    def print_alerts(self):
        """Display system alerts."""
        try:
            alerts = []
            
            # Check storage usage
            usage = self.client.get_storage_usage('pilab-dev')
            if 'error' not in usage:
                total_size_gb = usage.get('total_size_mb', 0) / 1024
                if total_size_gb > 10:  # Alert if over 10GB
                    alerts.append({
                        'type': 'WARNING',
                        'message': f'Storage usage is high: {total_size_gb:.2f} GB'
                    })
            
            # Check recent upload failures
            query = """
                SELECT 
                    COUNT(*) as total_uploads,
                    COUNT(CASE WHEN status = 'success' THEN 1 END) as successful_uploads
                FROM upload_logs
                WHERE created_at >= NOW() - INTERVAL '24 hours'
            """
            
            result = self.client.client.rpc('exec_sql', {
                'query': query, 
                'params': []
            }).execute()
            
            if result.data and result.data[0]['total_uploads'] > 0:
                data = result.data[0]
                success_rate = (data['successful_uploads'] / data['total_uploads'] * 100)
                if success_rate < 90:  # Alert if success rate below 90%
                    alerts.append({
                        'type': 'ERROR',
                        'message': f'Upload success rate is low: {success_rate:.1f}%'
                    })
            
            print("⚠️  SYSTEM ALERTS")
            print("-" * 40)
            
            if alerts:
                for alert in alerts:
                    print(f"[{alert['type']}] {alert['message']}")
            else:
                print("✅ No alerts")
            print()
            
        except Exception as e:
            print(f"❌ Alerts: {e}")
    
    def print_audit_logs(self, limit: int = 5):
        """Display recent audit logs."""
        try:
            logs = self.client.get_audit_logs(limit=limit)
            
            print(f"📋 RECENT AUDIT LOGS (Last {limit})")
            print("-" * 40)
            
            if logs:
                for log in logs:
                    timestamp = datetime.fromisoformat(log['timestamp'].replace('Z', '+00:00'))
                    print(f"{timestamp.strftime('%H:%M:%S')} | {log['action']} | {log['bucket_id']}")
            else:
                print("No audit logs found")
            print()
            
        except Exception as e:
            print(f"❌ Audit Logs: {e}")
    
    def print_health_status(self):
        """Display system health status."""
        try:
            is_connected = self.client.test_connection()
            
            print("🏥 SYSTEM HEALTH")
            print("-" * 40)
            print(f"Status:          {'✅ Healthy' if is_connected else '❌ Unhealthy'}")
            print(f"Supabase:        {'✅ Connected' if is_connected else '❌ Disconnected'}")
            print(f"Last Check:      {datetime.now().strftime('%H:%M:%S')}")
            print()
            
        except Exception as e:
            print(f"❌ Health Status: {e}")
    
    def run_dashboard(self, interval: int = 30):
        """Run the interactive dashboard."""
        if not self.initialize_client():
            return False
        
        self.running = True
        self.update_interval = interval
        
        print("🚀 Starting PiLab CLI Dashboard...")
        print("Press Ctrl+C to exit")
        print()
        
        try:
            while self.running:
                self.clear_screen()
                self.print_header()
                
                # Display all sections
                self.print_health_status()
                self.print_storage_usage()
                self.print_upload_metrics()
                self.print_recent_captures()
                self.print_alerts()
                self.print_audit_logs()
                
                # Wait for next update
                time.sleep(self.update_interval)
                
        except KeyboardInterrupt:
            print("\n👋 Dashboard stopped by user")
            return True
        except Exception as e:
            print(f"\n❌ Dashboard error: {e}")
            return False
    
    def run_single_update(self):
        """Run a single dashboard update."""
        if not self.initialize_client():
            return False
        
        self.print_header()
        self.print_health_status()
        self.print_storage_usage()
        self.print_upload_metrics()
        self.print_recent_captures()
        self.print_alerts()
        self.print_audit_logs()
        
        return True


def main():
    """Main entry point for the CLI dashboard."""
    parser = argparse.ArgumentParser(description='PiLab CLI Dashboard')
    parser.add_argument('--interval', '-i', type=int, default=30,
                       help='Update interval in seconds (default: 30)')
    parser.add_argument('--once', '-o', action='store_true',
                       help='Run once and exit (no continuous updates)')
    parser.add_argument('--captures', '-c', type=int, default=5,
                       help='Number of recent captures to show (default: 5)')
    parser.add_argument('--logs', '-l', type=int, default=5,
                       help='Number of audit logs to show (default: 5)')
    
    args = parser.parse_args()
    
    dashboard = CLIDashboard()
    
    if args.once:
        success = dashboard.run_single_update()
        sys.exit(0 if success else 1)
    else:
        success = dashboard.run_dashboard(args.interval)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main() 