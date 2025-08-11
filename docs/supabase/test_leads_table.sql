-- Test queries to verify the leads table setup
-- Run these after executing leads_table_setup.sql

-- 1. Verify table structure
SELECT 
    column_name,
    data_type,
    column_default,
    is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = 'leads'
ORDER BY ordinal_position;

-- 2. Verify RLS is enabled
SELECT 
    schemaname, 
    tablename, 
    rowsecurity,
    rowsecurity
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename = 'leads';

-- 3. Verify policies exist
SELECT 
    policyname,
    roles,
    cmd,
    permissive,
    qual,
    with_check
FROM pg_policies 
WHERE schemaname = 'public' 
  AND tablename = 'leads';

-- 4. Verify seed data exists
SELECT 
    id,
    created_at,
    name,
    email,
    phone,
    source,
    status,
    metadata
FROM public.leads 
WHERE name = 'Smoke Test';

-- 5. Test insert (simulating anonymous role)
-- Note: This would need to be run with appropriate role permissions
-- INSERT INTO public.leads (name, email, source) 
-- VALUES ('Test Lead', 'test@example.com', 'web');

-- 6. Verify pgcrypto extension is installed
SELECT 
    extname,
    extversion
FROM pg_extension 
WHERE extname = 'pgcrypto';