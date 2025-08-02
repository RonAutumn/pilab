#!/usr/bin/env python3
"""
PiLab Storage Monitoring Script

This script monitors storage usage, enforces retention policies, and maintains audit logs.
It uses the existing PiLabSupabaseClient for all operations with comprehensive error handling,
retry logic, and structured logging.

Usage:
    python scripts/storage_monitor.py [--bucket BUCKET_NAME] [--retention-days DAYS] [--dry-run]
"""

import argparse
import logging
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json

# Add src directory to path to import our modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'dashboard', 'utils'))

from supabase_client import PiLabSupabaseClient, AuditLogEntry, create_pilab_client
from logging_utils import get_logger, log_with_context, generate_correlation_id
from retry import retry_on_supabase_error, RetryError, ValidationError, TransientError, PermanentError
from chunked_processing import process_bulk_data, DEFAULT_CHUNK_SIZE

# Configure structured logging
logger = get_logger('pilab.storage_monitor', log_file='storage_monitor.log')
correlation_id = generate_correlation_id()


class StorageMonitor:
    """
    Storage monitoring and retention policy enforcement.
    """
    
    def __init__(self, client: PiLabSupabaseClient):
        self.client = client
        self.stats = {
            'monitoring_run': datetime.utcnow().isoformat(),
            'buckets_checked': 0,
            'files_processed': 0,
            'files_soft_deleted': 0,
            'errors': []
        }
    
    @retry_on_supabase_error(max_attempts=3)
    def monitor_storage_usage(self, bucket_name: str) -> Dict[str, Any]:
        """
        Monitor storage usage for a specific bucket with retry logic.
        
        Args:
            bucket_name: Name of the bucket to monitor
            
        Returns:
            Dictionary with usage statistics
        """
        log_with_context(logger, 'INFO', f"Monitoring storage usage for bucket: {bucket_name}", 
                        correlation_id=correlation_id, bucket_name=bucket_name)
        
        try:
            usage = self.client.get_storage_usage(bucket_name)
            
            if usage.get('error'):
                log_with_context(logger, 'ERROR', f"Error monitoring bucket {bucket_name}: {usage['error']}", 
                               correlation_id=correlation_id, bucket_name=bucket_name, error=usage['error'])
                self.stats['errors'].append({
                    'bucket': bucket_name,
                    'error': usage['error'],
                    'timestamp': datetime.utcnow().isoformat(),
                    'correlation_id': correlation_id
                })
                return usage
            
            # Log audit event for monitoring
            audit_entry = AuditLogEntry(
                action='retention_check',
                object_id='monitoring-run',
                bucket_id=bucket_name,
                user_id=None,
                details={
                    'usage_stats': usage,
                    'monitoring_type': 'storage_usage',
                    'correlation_id': correlation_id
                }
            )
            self.client.log_audit_event(audit_entry)
            
            log_with_context(logger, 'INFO', f"Bucket {bucket_name}: {usage['total_files']} files, {usage['total_size_mb']} MB", 
                           correlation_id=correlation_id, bucket_name=bucket_name, 
                           total_files=usage['total_files'], total_size_mb=usage['total_size_mb'])
            
            self.stats['buckets_checked'] += 1
            
            return usage
            
        except RetryError as e:
            log_with_context(logger, 'ERROR', f"Failed to monitor bucket {bucket_name} after retries: {e}", 
                           correlation_id=correlation_id, bucket_name=bucket_name, attempts=e.attempts)
            self.stats['errors'].append({
                'bucket': bucket_name,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
            return {'error': str(e)}
    
    @retry_on_supabase_error(max_attempts=3)
    def enforce_retention_policy(self, bucket_name: str, retention_days: int, 
                               dry_run: bool = False) -> Dict[str, Any]:
        """
        Enforce retention policy for a bucket with chunked processing.
        
        Args:
            bucket_name: Name of the bucket to check
            retention_days: Number of days to retain files
            dry_run: If True, don't actually delete files
            
        Returns:
            Dictionary with retention enforcement results
        """
        log_with_context(logger, 'INFO', f"Enforcing retention policy for bucket {bucket_name} (retention: {retention_days} days, dry_run: {dry_run})", 
                        correlation_id=correlation_id, bucket_name=bucket_name, retention_days=retention_days, dry_run=dry_run)
        
        try:
            # Get files that exceed retention period
            files_to_delete = self.client.get_files_for_retention_check(
                bucket_name, retention_days
            )
            
            if not files_to_delete:
                log_with_context(logger, 'INFO', f"No files exceed retention period in bucket {bucket_name}", 
                               correlation_id=correlation_id, bucket_name=bucket_name)
                return {
                    'bucket_name': bucket_name,
                    'files_checked': 0,
                    'files_soft_deleted': 0,
                    'total_size_freed': 0,
                    'dry_run': dry_run,
                    'correlation_id': correlation_id
                }
            
            log_with_context(logger, 'INFO', f"Found {len(files_to_delete)} files exceeding retention period", 
                           correlation_id=correlation_id, bucket_name=bucket_name, files_count=len(files_to_delete))
            
            # Process files in chunks to avoid memory issues
            def process_file_chunk(file_chunk):
                """Process a chunk of files for deletion."""
                chunk_results = {
                    'deleted_count': 0,
                    'total_size_freed': 0,
                    'errors': []
                }
                
                for file_obj in file_chunk:
                    try:
                        if not dry_run:
                            # Soft delete the file
                            success = self.client.soft_delete_file(
                                file_obj.id, 
                                reason=f"retention_policy_{retention_days}_days"
                            )
                            
                            if success:
                                chunk_results['deleted_count'] += 1
                                chunk_results['total_size_freed'] += file_obj.size
                                
                                # Log audit event
                                audit_entry = AuditLogEntry(
                                    action='soft_delete',
                                    object_id=file_obj.id,
                                    bucket_id=bucket_name,
                                    user_id=None,
                                    details={
                                        'file_name': file_obj.name,
                                        'file_size': file_obj.size,
                                        'created_at': file_obj.created_at.isoformat(),
                                        'retention_days': retention_days,
                                        'reason': 'retention_policy',
                                        'correlation_id': correlation_id
                                    }
                                )
                                self.client.log_audit_event(audit_entry)
                                
                                log_with_context(logger, 'INFO', f"Soft deleted file: {file_obj.name} ({file_obj.size} bytes)", 
                                               correlation_id=correlation_id, file_name=file_obj.name, file_size=file_obj.size)
                            else:
                                log_with_context(logger, 'WARNING', f"Failed to soft delete file: {file_obj.name}", 
                                               correlation_id=correlation_id, file_name=file_obj.name)
                        else:
                            # Dry run - just log what would be deleted
                            chunk_results['deleted_count'] += 1
                            chunk_results['total_size_freed'] += file_obj.size
                            log_with_context(logger, 'INFO', f"[DRY RUN] Would delete: {file_obj.name} ({file_obj.size} bytes)", 
                                           correlation_id=correlation_id, file_name=file_obj.name, file_size=file_obj.size)
                        
                        self.stats['files_processed'] += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing file {file_obj.name}: {e}"
                        log_with_context(logger, 'ERROR', error_msg, 
                                       correlation_id=correlation_id, file_name=file_obj.name, error=str(e))
                        chunk_results['errors'].append({
                            'file': file_obj.name,
                            'error': str(e),
                            'timestamp': datetime.utcnow().isoformat(),
                            'correlation_id': correlation_id
                        })
                
                return chunk_results
            
            # Process files in chunks
            bulk_result = process_bulk_data(
                data=files_to_delete,
                processor=process_file_chunk,
                chunk_size=DEFAULT_CHUNK_SIZE,
                logger=logger
            )
            
            # Aggregate results
            total_deleted = sum(chunk['deleted_count'] for chunk in bulk_result.chunk_results)
            total_size_freed = sum(chunk['total_size_freed'] for chunk in bulk_result.chunk_results)
            all_errors = []
            for chunk in bulk_result.chunk_results:
                all_errors.extend(chunk['errors'])
            
            if not dry_run:
                self.stats['files_soft_deleted'] += total_deleted
            
            # Add errors to stats
            self.stats['errors'].extend(all_errors)
            
            log_with_context(logger, 'INFO', f"Retention policy enforcement completed: {total_deleted} files deleted, {total_size_freed} bytes freed", 
                           correlation_id=correlation_id, bucket_name=bucket_name, files_deleted=total_deleted, 
                           size_freed=total_size_freed, success_rate=bulk_result.success_rate)
            
            result = {
                'bucket_name': bucket_name,
                'files_checked': len(files_to_delete),
                'files_soft_deleted': total_deleted,
                'total_size_freed': total_size_freed,
                'total_size_freed_mb': round(total_size_freed / (1024 * 1024), 2),
                'dry_run': dry_run
            }
            
            logger.info(f"Retention enforcement complete for {bucket_name}: "
                       f"{deleted_count}/{len(files_to_delete)} files processed")
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to enforce retention policy for bucket {bucket_name}: {e}"
            logger.error(error_msg)
            self.stats['errors'].append({
                'bucket': bucket_name,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
            return {'error': str(e)}
    
    def generate_report(self) -> Dict[str, Any]:
        """
        Generate a monitoring report.
        
        Returns:
            Dictionary with monitoring report
        """
        report = {
            'monitoring_run': self.stats['monitoring_run'],
            'summary': {
                'buckets_checked': self.stats['buckets_checked'],
                'files_processed': self.stats['files_processed'],
                'files_soft_deleted': self.stats['files_soft_deleted'],
                'errors_count': len(self.stats['errors'])
            },
            'errors': self.stats['errors']
        }
        
        return report


def main():
    """Main function for the storage monitoring script."""
    parser = argparse.ArgumentParser(
        description='Monitor PiLab storage usage and enforce retention policies'
    )
    parser.add_argument(
        '--bucket', 
        default='pilab-dev',
        help='Bucket name to monitor (default: pilab-dev)'
    )
    parser.add_argument(
        '--retention-days', 
        type=int, 
        default=30,
        help='Number of days to retain files (default: 30)'
    )
    parser.add_argument(
        '--dry-run', 
        action='store_true',
        help='Perform a dry run without actually deleting files'
    )
    parser.add_argument(
        '--monitor-only', 
        action='store_true',
        help='Only monitor usage, do not enforce retention policies'
    )
    
    args = parser.parse_args()
    
    logger.info("Starting PiLab storage monitoring")
    logger.info(f"Configuration: bucket={args.bucket}, retention_days={args.retention_days}, "
               f"dry_run={args.dry_run}, monitor_only={args.monitor_only}")
    
    try:
        # Initialize Supabase client
        client = create_pilab_client()
        
        # Test connection
        if not client.test_connection():
            logger.error("Failed to connect to Supabase")
            sys.exit(1)
        
        logger.info("✅ Connected to Supabase successfully")
        
        # Create storage monitor
        monitor = StorageMonitor(client)
        
        # Monitor storage usage
        usage_stats = monitor.monitor_storage_usage(args.bucket)
        
        if usage_stats.get('error'):
            logger.error(f"Storage monitoring failed: {usage_stats['error']}")
            sys.exit(1)
        
        # Print usage statistics
        print(f"\n📊 Storage Usage Report for {args.bucket}:")
        print(f"   Total files: {usage_stats['total_files']}")
        print(f"   Total size: {usage_stats['total_size_mb']} MB")
        print(f"   Oldest file: {usage_stats['oldest_file']}")
        print(f"   Newest file: {usage_stats['newest_file']}")
        
        # Enforce retention policy (unless monitor-only)
        if not args.monitor_only:
            retention_results = monitor.enforce_retention_policy(
                args.bucket, args.retention_days, args.dry_run
            )
            
            if retention_results.get('error'):
                logger.error(f"Retention enforcement failed: {retention_results['error']}")
                sys.exit(1)
            
            # Print retention results
            print(f"\n🗑️  Retention Policy Enforcement:")
            print(f"   Files checked: {retention_results['files_checked']}")
            print(f"   Files {'would be ' if args.dry_run else ''}deleted: {retention_results['files_soft_deleted']}")
            print(f"   Size {'would be ' if args.dry_run else ''}freed: {retention_results['total_size_freed_mb']} MB")
        
        # Generate and save report
        report = monitor.generate_report()
        
        # Save report to file
        report_filename = f"storage_monitor_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Monitoring report saved to: {report_filename}")
        
        # Print summary
        print(f"\n✅ Storage monitoring completed successfully")
        print(f"   Report saved to: {report_filename}")
        if report['summary']['errors_count'] > 0:
            print(f"   ⚠️  {report['summary']['errors_count']} errors occurred (see log for details)")
        
    except Exception as e:
        logger.error(f"Storage monitoring failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 