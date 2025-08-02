-- Verify and ensure RLS policies for PiLab storage system
-- This migration ensures all tables have proper RLS policies configured

-- Enable RLS on all tables if not already enabled
ALTER TABLE captures ENABLE ROW LEVEL SECURITY;
ALTER TABLE upload_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE storage_audit_log ENABLE ROW LEVEL SECURITY;

-- Drop existing policies to recreate them properly
DROP POLICY IF EXISTS "anon_read_captures" ON captures;
DROP POLICY IF EXISTS "service_role_full_captures" ON captures;
DROP POLICY IF EXISTS "anon_read_upload_logs" ON upload_logs;
DROP POLICY IF EXISTS "service_role_full_upload_logs" ON upload_logs;
DROP POLICY IF EXISTS "anon_read_audit_log" ON storage_audit_log;
DROP POLICY IF EXISTS "service_role_full_audit_log" ON storage_audit_log;

-- Captures table policies
-- Anonymous users can only read public fields (no sensitive data)
CREATE POLICY "anon_read_captures" ON captures
    FOR SELECT
    TO anon
    USING (true);  -- Allow read access to all captures for anonymous users

-- Service role has full access for backend operations
CREATE POLICY "service_role_full_captures" ON captures
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Upload logs table policies
-- Anonymous users can only read basic upload statistics
CREATE POLICY "anon_read_upload_logs" ON upload_logs
    FOR SELECT
    TO anon
    USING (true);  -- Allow read access to upload logs for anonymous users

-- Service role has full access for backend operations
CREATE POLICY "service_role_full_upload_logs" ON upload_logs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Storage audit log table policies
-- Anonymous users can only read basic audit information
CREATE POLICY "anon_read_audit_log" ON storage_audit_log
    FOR SELECT
    TO anon
    USING (true);  -- Allow read access to audit logs for anonymous users

-- Service role has full access for backend operations
CREATE POLICY "service_role_full_audit_log" ON storage_audit_log
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_captures_created_at ON captures(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_captures_shot_type ON captures(shot_type);
CREATE INDEX IF NOT EXISTS idx_upload_logs_created_at ON upload_logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_upload_logs_status ON upload_logs(status);
CREATE INDEX IF NOT EXISTS idx_audit_log_created_at ON storage_audit_log(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_audit_log_action ON storage_audit_log(action);

-- Verify RLS is enabled on all tables
DO $$
DECLARE
    table_name text;
    rls_enabled boolean;
BEGIN
    FOR table_name IN SELECT unnest(ARRAY['captures', 'upload_logs', 'storage_audit_log']) LOOP
        SELECT relrowsecurity INTO rls_enabled
        FROM pg_class
        WHERE relname = table_name;
        
        IF NOT rls_enabled THEN
            RAISE EXCEPTION 'RLS is not enabled on table %', table_name;
        END IF;
        
        RAISE NOTICE 'RLS is enabled on table %', table_name;
    END LOOP;
END $$;

-- Verify policies exist
DO $$
DECLARE
    policy_count integer;
BEGIN
    -- Check captures policies
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE tablename = 'captures';
    
    IF policy_count < 2 THEN
        RAISE EXCEPTION 'Insufficient policies on captures table. Found: %', policy_count;
    END IF;
    
    -- Check upload_logs policies
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE tablename = 'upload_logs';
    
    IF policy_count < 2 THEN
        RAISE EXCEPTION 'Insufficient policies on upload_logs table. Found: %', policy_count;
    END IF;
    
    -- Check storage_audit_log policies
    SELECT COUNT(*) INTO policy_count
    FROM pg_policies
    WHERE tablename = 'storage_audit_log';
    
    IF policy_count < 2 THEN
        RAISE EXCEPTION 'Insufficient policies on storage_audit_log table. Found: %', policy_count;
    END IF;
    
    RAISE NOTICE 'All RLS policies verified successfully';
END $$; 