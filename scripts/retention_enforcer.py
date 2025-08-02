#!/usr/bin/env python3
"""
PiLab Retention Policy Enforcer

This script enforces retention policies on PiLab storage buckets.
It can be run as a scheduled task (cron job) to automatically clean up old files.

Usage:
    python scripts/retention_enforcer.py [--bucket BUCKET_NAME] [--retention-days DAYS] [--dry-run]
    
Example cron job (daily at 2 AM):
    0 2 * * * cd /path/to/pilab && python scripts/retention_enforcer.py --bucket pilab-dev --retention-days 30
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

from supabase_client import PiLabSupabaseClient, AuditLogEntry, create_pilab_client

# Configure logging for scheduled execution
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('retention_enforcer.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class RetentionEnforcer:
    """
    Dedicated retention policy enforcer for PiLab storage.
    """
    
    def __init__(self, client: PiLabSupabaseClient):
        self.client = client
        self.stats = {
            'enforcement_run': datetime.utcnow().isoformat(),
            'buckets_processed': 0,
            'files_checked': 0,
            'files_soft_deleted': 0,
            'total_size_freed': 0,
            'errors': []
        }
    
    def enforce_retention_for_bucket(self, bucket_name: str, retention_days: int, 
                                   dry_run: bool = False) -> Dict[str, Any]:
        """
        Enforce retention policy for a specific bucket.
        
        Args:
            bucket_name: Name of the bucket to process
            retention_days: Number of days to retain files
            dry_run: If True, don't actually delete files
            
        Returns:
            Dictionary with enforcement results
        """
        logger.info(f"Enforcing retention policy for bucket: {bucket_name}")
        logger.info(f"Retention period: {retention_days} days")
        logger.info(f"Dry run mode: {dry_run}")
        
        try:
            # Get files that exceed retention period
            files_to_delete = self.client.get_files_for_retention_check(
                bucket_name, retention_days
            )
            
            if not files_to_delete:
                logger.info(f"No files exceed retention period in bucket {bucket_name}")
                self.stats['buckets_processed'] += 1
                return {
                    'bucket_name': bucket_name,
                    'files_checked': 0,
                    'files_soft_deleted': 0,
                    'total_size_freed': 0,
                    'total_size_freed_mb': 0,
                    'dry_run': dry_run,
                    'status': 'no_files_to_delete'
                }
            
            logger.info(f"Found {len(files_to_delete)} files exceeding retention period")
            
            deleted_count = 0
            total_size_freed = 0
            errors = []
            
            # Process files in batches to avoid overwhelming the system
            batch_size = 50
            for i in range(0, len(files_to_delete), batch_size):
                batch = files_to_delete[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(files_to_delete) + batch_size - 1)//batch_size}")
                
                for file_obj in batch:
                    try:
                        if not dry_run:
                            # Soft delete the file
                            success = self.client.soft_delete_file(
                                file_obj.id, 
                                reason=f"retention_policy_{retention_days}_days"
                            )
                            
                            if success:
                                deleted_count += 1
                                total_size_freed += file_obj.size
                                
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
                                        'enforcement_run': self.stats['enforcement_run']
                                    }
                                )
                                self.client.log_audit_event(audit_entry)
                                
                                logger.debug(f"Soft deleted file: {file_obj.name} ({file_obj.size} bytes)")
                            else:
                                logger.warning(f"Failed to soft delete file: {file_obj.name}")
                                errors.append(f"Failed to delete {file_obj.name}")
                        else:
                            # Dry run - just count what would be deleted
                            deleted_count += 1
                            total_size_freed += file_obj.size
                            logger.debug(f"[DRY RUN] Would delete: {file_obj.name} ({file_obj.size} bytes)")
                        
                        self.stats['files_checked'] += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing file {file_obj.name}: {e}"
                        logger.error(error_msg)
                        errors.append(error_msg)
                        self.stats['errors'].append({
                            'file': file_obj.name,
                            'error': str(e),
                            'timestamp': datetime.utcnow().isoformat()
                        })
                
                # Small delay between batches to be nice to the system
                if not dry_run and i + batch_size < len(files_to_delete):
                    import time
                    time.sleep(0.1)
            
            # Log overall enforcement event
            audit_entry = AuditLogEntry(
                action='retention_check',
                object_id='enforcement-run',
                bucket_id=bucket_name,
                user_id=None,
                details={
                    'retention_days': retention_days,
                    'files_checked': len(files_to_delete),
                    'files_deleted': deleted_count,
                    'total_size_freed': total_size_freed,
                    'dry_run': dry_run,
                    'errors': errors
                }
            )
            self.client.log_audit_event(audit_entry)
            
            if not dry_run:
                self.stats['files_soft_deleted'] += deleted_count
                self.stats['total_size_freed'] += total_size_freed
            
            self.stats['buckets_processed'] += 1
            
            result = {
                'bucket_name': bucket_name,
                'files_checked': len(files_to_delete),
                'files_soft_deleted': deleted_count,
                'total_size_freed': total_size_freed,
                'total_size_freed_mb': round(total_size_freed / (1024 * 1024), 2),
                'dry_run': dry_run,
                'status': 'completed',
                'errors': errors
            }
            
            logger.info(f"Retention enforcement completed for {bucket_name}: "
                       f"{deleted_count}/{len(files_to_delete)} files processed, "
                       f"{result['total_size_freed_mb']} MB freed")
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to enforce retention policy for bucket {bucket_name}: {e}"
            logger.error(error_msg)
            self.stats['errors'].append({
                'bucket': bucket_name,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            })
            return {
                'bucket_name': bucket_name,
                'error': str(e),
                'status': 'failed'
            }
    
    def generate_enforcement_report(self) -> Dict[str, Any]:
        """
        Generate a retention enforcement report.
        
        Returns:
            Dictionary with enforcement report
        """
        report = {
            'enforcement_run': self.stats['enforcement_run'],
            'summary': {
                'buckets_processed': self.stats['buckets_processed'],
                'files_checked': self.stats['files_checked'],
                'files_soft_deleted': self.stats['files_soft_deleted'],
                'total_size_freed_mb': round(self.stats['total_size_freed'] / (1024 * 1024), 2),
                'errors_count': len(self.stats['errors'])
            },
            'errors': self.stats['errors']
        }
        
        return report


def main():
    """Main function for the retention enforcer script."""
    parser = argparse.ArgumentParser(
        description='Enforce PiLab storage retention policies'
    )
    parser.add_argument(
        '--bucket', 
        default='pilab-dev',
        help='Bucket name to process (default: pilab-dev)'
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
        '--quiet', 
        action='store_true',
        help='Suppress console output (useful for cron jobs)'
    )
    
    args = parser.parse_args()
    
    # Configure logging based on quiet mode
    if args.quiet:
        # Remove console handler for quiet mode
        for handler in logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler) and not isinstance(handler, logging.FileHandler):
                logger.removeHandler(handler)
    
    logger.info("Starting PiLab retention policy enforcement")
    logger.info(f"Configuration: bucket={args.bucket}, retention_days={args.retention_days}, "
               f"dry_run={args.dry_run}")
    
    try:
        # Initialize Supabase client
        client = create_pilab_client()
        
        # Test connection
        if not client.test_connection():
            logger.error("Failed to connect to Supabase")
            sys.exit(1)
        
        logger.info("✅ Connected to Supabase successfully")
        
        # Create retention enforcer
        enforcer = RetentionEnforcer(client)
        
        # Enforce retention policy
        results = enforcer.enforce_retention_for_bucket(
            args.bucket, args.retention_days, args.dry_run
        )
        
        if results.get('error'):
            logger.error(f"Retention enforcement failed: {results['error']}")
            sys.exit(1)
        
        # Print results (unless quiet mode)
        if not args.quiet:
            print(f"\n🗑️  Retention Policy Enforcement Results:")
            print(f"   Bucket: {results['bucket_name']}")
            print(f"   Files checked: {results['files_checked']}")
            print(f"   Files {'would be ' if args.dry_run else ''}deleted: {results['files_soft_deleted']}")
            print(f"   Size {'would be ' if args.dry_run else ''}freed: {results['total_size_freed_mb']} MB")
            print(f"   Status: {results['status']}")
            
            if results.get('errors'):
                print(f"   ⚠️  {len(results['errors'])} errors occurred")
        
        # Generate and save report
        report = enforcer.generate_enforcement_report()
        
        # Save report to file
        report_filename = f"retention_enforcement_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Enforcement report saved to: {report_filename}")
        
        # Print summary (unless quiet mode)
        if not args.quiet:
            print(f"\n✅ Retention enforcement completed successfully")
            print(f"   Report saved to: {report_filename}")
            if report['summary']['errors_count'] > 0:
                print(f"   ⚠️  {report['summary']['errors_count']} errors occurred (see log for details)")
        
        # Exit with error code if there were errors (useful for monitoring)
        if report['summary']['errors_count'] > 0:
            sys.exit(1)
        
    except Exception as e:
        logger.error(f"Retention enforcement failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 