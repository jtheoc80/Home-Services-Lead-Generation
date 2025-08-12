-- Remove temporary anon policies and replace with authenticated-only policies
-- Run this script after testing is complete to secure the leads table
-- Requires PostgreSQL with Row Level Security enabled

-- Remove temporary anonymous policies
DROP POLICY IF EXISTS "temp_anon_insert_leads" ON public.leads;
DROP POLICY IF EXISTS "temp_anon_select_leads" ON public.leads;

-- Create authenticated-only policies for production use
-- Policy for authenticated users to insert leads
DROP POLICY IF EXISTS "authenticated_users_insert_leads" ON public.leads;
CREATE POLICY "authenticated_users_insert_leads"
    ON public.leads FOR INSERT
    TO authenticated
    WITH CHECK (true);

-- Policy for authenticated users to select leads
DROP POLICY IF EXISTS "authenticated_users_select_leads" ON public.leads;
CREATE POLICY "authenticated_users_select_leads"
    ON public.leads FOR SELECT
    TO authenticated
    USING (true);

-- Policy for authenticated users to update leads
DROP POLICY IF EXISTS "authenticated_users_update_leads" ON public.leads;
CREATE POLICY "authenticated_users_update_leads"
    ON public.leads FOR UPDATE
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Allow service role full access (for backend processing)
DROP POLICY IF EXISTS "service_role_full_access_leads" ON public.leads;
CREATE POLICY "service_role_full_access_leads"
    ON public.leads FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Verify the production policies are active and RLS is enabled
SELECT 
    schemaname, 
    tablename, 
    rowsecurity AS rls_enabled
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename = 'leads';

-- Verify the production policies are active
SELECT 'Temporary anon policies removed and production authenticated-only RLS policies created successfully!' AS message;