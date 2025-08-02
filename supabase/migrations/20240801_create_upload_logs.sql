-- Migration: Create upload_logs table for PiLab upload tracking
-- Date: 2024-08-01
-- Description: Creates table for tracking file upload operations and their status

-- Create the upload_logs table
CREATE TABLE IF NOT EXISTS upload_logs (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    filename text NOT NULL,
    file_path text NOT NULL,
    file_size bigint NOT NULL,
    status text NOT NULL CHECK (status IN ('pending', 'success', 'failed', 'cancelled')),
    bucket_id text NOT NULL,
    object_id uuid,
    user_id uuid,
    error_message text,
    upload_duration_ms integer,
    created_at timestamptz DEFAULT now(),
    updated_at timestamptz DEFAULT now()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_upload_logs_status ON upload_logs(status);
CREATE INDEX IF NOT EXISTS idx_upload_logs_created_at ON upload_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_upload_logs_bucket_id ON upload_logs(bucket_id);
CREATE INDEX IF NOT EXISTS idx_upload_logs_user_id ON upload_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_upload_logs_filename ON upload_logs(filename);

-- Create a composite index for common query patterns
CREATE INDEX IF NOT EXISTS idx_upload_logs_status_time 
ON upload_logs(status, created_at DESC);

-- Enable Row Level Security (RLS)
ALTER TABLE upload_logs ENABLE ROW LEVEL SECURITY;

-- Create RLS policies

-- Policy: Service role can read all upload logs (for monitoring scripts)
CREATE POLICY "service_role_read_upload_logs" ON upload_logs
    FOR SELECT
    TO service_role
    USING (true);

-- Policy: Service role can insert upload logs (for logging operations)
CREATE POLICY "service_role_insert_upload_logs" ON upload_logs
    FOR INSERT
    TO service_role
    WITH CHECK (true);

-- Policy: Service role can update upload logs (for status updates)
CREATE POLICY "service_role_update_upload_logs" ON upload_logs
    FOR UPDATE
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Policy: Authenticated users can read upload logs for their own uploads
CREATE POLICY "users_read_own_upload_logs" ON upload_logs
    FOR SELECT
    TO authenticated
    USING (user_id = auth.uid());

-- Policy: Authenticated users can insert upload logs for their own uploads
CREATE POLICY "users_insert_own_upload_logs" ON upload_logs
    FOR INSERT
    TO authenticated
    WITH CHECK (user_id = auth.uid());

-- Policy: Authenticated users can update their own upload logs
CREATE POLICY "users_update_own_upload_logs" ON upload_logs
    FOR UPDATE
    TO authenticated
    USING (user_id = auth.uid())
    WITH CHECK (user_id = auth.uid());

-- Create a function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_upload_logs_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update updated_at
CREATE TRIGGER trigger_update_upload_logs_updated_at
    BEFORE UPDATE ON upload_logs
    FOR EACH ROW
    EXECUTE FUNCTION update_upload_logs_updated_at();

-- Create a function to log upload events
CREATE OR REPLACE FUNCTION log_upload_event(
    p_filename text,
    p_file_path text,
    p_file_size bigint,
    p_status text,
    p_bucket_id text,
    p_object_id uuid DEFAULT NULL,
    p_user_id uuid DEFAULT NULL,
    p_error_message text DEFAULT NULL,
    p_upload_duration_ms integer DEFAULT NULL
)
RETURNS uuid
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    v_upload_id uuid;
BEGIN
    INSERT INTO upload_logs (
        filename,
        file_path,
        file_size,
        status,
        bucket_id,
        object_id,
        user_id,
        error_message,
        upload_duration_ms
    ) VALUES (
        p_filename,
        p_file_path,
        p_file_size,
        p_status,
        p_bucket_id,
        p_object_id,
        COALESCE(p_user_id, auth.uid()),
        p_error_message,
        p_upload_duration_ms
    ) RETURNING id INTO v_upload_id;
    
    RETURN v_upload_id;
END;
$$;

-- Grant execute permission on the function
GRANT EXECUTE ON FUNCTION log_upload_event TO authenticated;
GRANT EXECUTE ON FUNCTION log_upload_event TO service_role;

-- Create a view for easy querying of recent uploads
CREATE OR REPLACE VIEW recent_upload_logs AS
SELECT 
    id,
    filename,
    file_path,
    file_size,
    status,
    bucket_id,
    object_id,
    user_id,
    error_message,
    upload_duration_ms,
    created_at,
    updated_at
FROM upload_logs
ORDER BY created_at DESC;

-- Grant select permission on the view
GRANT SELECT ON recent_upload_logs TO authenticated;
GRANT SELECT ON recent_upload_logs TO service_role;

-- Create a function to get upload summary statistics
CREATE OR REPLACE FUNCTION get_upload_summary(
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
        'total_uploads', COUNT(*),
        'successful_uploads', COUNT(*) FILTER (WHERE status = 'success'),
        'failed_uploads', COUNT(*) FILTER (WHERE status = 'failed'),
        'pending_uploads', COUNT(*) FILTER (WHERE status = 'pending'),
        'total_size_bytes', COALESCE(SUM(file_size), 0),
        'avg_file_size_bytes', COALESCE(AVG(file_size), 0),
        'success_rate', CASE 
            WHEN COUNT(*) > 0 THEN 
                ROUND((COUNT(*) FILTER (WHERE status = 'success')::float / COUNT(*) * 100)::numeric, 2)
            ELSE 0 
        END,
        'recent_activity', jsonb_build_object(
            'last_24h', COUNT(*) FILTER (WHERE created_at >= now() - interval '24 hours'),
            'last_7d', COUNT(*) FILTER (WHERE created_at >= now() - interval '7 days'),
            'last_30d', COUNT(*) FILTER (WHERE created_at >= now() - interval '30 days')
        )
    ) INTO v_summary
    FROM upload_logs
    WHERE (p_bucket_id IS NULL OR bucket_id = p_bucket_id)
    AND (p_since IS NULL OR created_at >= p_since);
    
    RETURN v_summary;
END;
$$;

-- Grant execute permission on the summary function
GRANT EXECUTE ON FUNCTION get_upload_summary TO authenticated;
GRANT EXECUTE ON FUNCTION get_upload_summary TO service_role;

-- Add comments for documentation
COMMENT ON TABLE upload_logs IS 'Log of all file upload operations in PiLab';
COMMENT ON COLUMN upload_logs.status IS 'Status of the upload operation';
COMMENT ON COLUMN upload_logs.file_size IS 'Size of the uploaded file in bytes';
COMMENT ON COLUMN upload_logs.upload_duration_ms IS 'Duration of upload in milliseconds';
COMMENT ON FUNCTION log_upload_event IS 'Convenience function to log upload events';
COMMENT ON VIEW recent_upload_logs IS 'View for querying recent upload logs';
COMMENT ON FUNCTION get_upload_summary IS 'Get summary statistics for upload operations'; 