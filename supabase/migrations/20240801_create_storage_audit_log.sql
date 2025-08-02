-- Migration: Create storage_audit_log table for PiLab storage operations
-- Date: 2024-08-01
-- Description: Creates audit logging table for tracking all storage operations

-- Create the storage_audit_log table
CREATE TABLE IF NOT EXISTS storage_audit_log (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp timestamptz NOT NULL DEFAULT now(),
    action text NOT NULL CHECK (action IN (
        'upload', 'download', 'delete', 'soft_delete', 'restore', 
        'retention_check', 'cleanup', 'access', 'modify'
    )),
    object_id uuid NOT NULL,
    bucket_id text NOT NULL,
    user_id uuid,
    details jsonb DEFAULT '{}',
    created_at timestamptz DEFAULT now()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_storage_audit_log_timestamp ON storage_audit_log(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_storage_audit_log_action ON storage_audit_log(action);
CREATE INDEX IF NOT EXISTS idx_storage_audit_log_bucket_id ON storage_audit_log(bucket_id);
CREATE INDEX IF NOT EXISTS idx_storage_audit_log_object_id ON storage_audit_log(object_id);
CREATE INDEX IF NOT EXISTS idx_storage_audit_log_user_id ON storage_audit_log(user_id);

-- Create a composite index for common query patterns
CREATE INDEX IF NOT EXISTS idx_storage_audit_log_bucket_action_time 
ON storage_audit_log(bucket_id, action, timestamp DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE storage_audit_log ENABLE ROW LEVEL SECURITY;

-- Create RLS policies

-- Policy: Service role can read all audit logs (for monitoring scripts)
CREATE POLICY "service_role_read_audit_logs" ON storage_audit_log
    FOR SELECT
    TO service_role
    USING (true);

-- Policy: Service role can insert audit logs (for logging operations)
CREATE POLICY "service_role_insert_audit_logs" ON storage_audit_log
    FOR INSERT
    TO service_role
    WITH CHECK (true);

-- Policy: Authenticated users can read audit logs for their own operations
CREATE POLICY "users_read_own_audit_logs" ON storage_audit_log
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

-- Policy: Authenticated users can insert audit logs for their own operations
CREATE POLICY "users_insert_own_audit_logs" ON storage_audit_log
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

-- Create a function to automatically log audit events
CREATE OR REPLACE FUNCTION log_storage_audit_event(
    p_action text,
    p_object_id uuid,
    p_bucket_id text,
    p_user_id uuid DEFAULT NULL,
    p_details jsonb DEFAULT '{}'
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_audit_id uuid;
BEGIN
    INSERT INTO storage_audit_log (
        action,
        object_id,
        bucket_id,
        user_id,
        details
    ) VALUES (
        p_action,
        p_object_id,
        p_bucket_id,
        COALESCE(p_user_id, auth.uid()),
        p_details
    ) RETURNING id INTO v_audit_id;
    
    RETURN v_audit_id;
END;
$$;

-- Grant execute permission on the function
GRANT EXECUTE ON FUNCTION log_storage_audit_event TO authenticated;
GRANT EXECUTE ON FUNCTION log_storage_audit_event TO service_role;

-- Create a view for easy querying of recent audit events
CREATE OR REPLACE VIEW recent_storage_audit_events AS
SELECT 
    id,
    timestamp,
    action,
    object_id,
    bucket_id,
    user_id,
    details,
    created_at
FROM storage_audit_log
ORDER BY timestamp DESC;

-- Grant select permission on the view
GRANT SELECT ON recent_storage_audit_events TO authenticated;
GRANT SELECT ON recent_storage_audit_events TO service_role;

-- Create a function to get audit summary statistics
CREATE OR REPLACE FUNCTION get_storage_audit_summary(
    p_bucket_id text DEFAULT NULL,
    p_since timestamptz DEFAULT NULL
)
RETURNS jsonb
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_summary jsonb;
BEGIN
    SELECT jsonb_build_object(
        'total_events', COUNT(*),
        'events_by_action', jsonb_object_agg(action, action_count),
        'events_by_bucket', jsonb_object_agg(bucket_id, bucket_count),
        'recent_activity', jsonb_build_object(
            'last_24h', last_24h_count,
            'last_7d', last_7d_count,
            'last_30d', last_30d_count
        )
    ) INTO v_summary
    FROM (
        SELECT 
            action,
            bucket_id,
            COUNT(*) as action_count,
            COUNT(*) FILTER (WHERE bucket_id = p_bucket_id OR p_bucket_id IS NULL) as bucket_count,
            COUNT(*) FILTER (WHERE timestamp >= now() - interval '24 hours') as last_24h_count,
            COUNT(*) FILTER (WHERE timestamp >= now() - interval '7 days') as last_7d_count,
            COUNT(*) FILTER (WHERE timestamp >= now() - interval '30 days') as last_30d_count
        FROM storage_audit_log
        WHERE (p_since IS NULL OR timestamp >= p_since)
        GROUP BY action, bucket_id
    ) stats;
    
    RETURN v_summary;
END;
$$;

-- Grant execute permission on the summary function
GRANT EXECUTE ON FUNCTION get_storage_audit_summary TO authenticated;
GRANT EXECUTE ON FUNCTION get_storage_audit_summary TO service_role;

-- Add comments for documentation
COMMENT ON TABLE storage_audit_log IS 'Audit log for all PiLab storage operations';
COMMENT ON COLUMN storage_audit_log.action IS 'Type of storage operation performed';
COMMENT ON COLUMN storage_audit_log.object_id IS 'ID of the storage object affected';
COMMENT ON COLUMN storage_audit_log.bucket_id IS 'ID of the storage bucket';
COMMENT ON COLUMN storage_audit_log.details IS 'Additional details about the operation in JSON format';
COMMENT ON FUNCTION log_storage_audit_event IS 'Convenience function to log storage audit events';
COMMENT ON VIEW recent_storage_audit_events IS 'View for querying recent storage audit events';
COMMENT ON FUNCTION get_storage_audit_summary IS 'Get summary statistics for storage audit events'; 