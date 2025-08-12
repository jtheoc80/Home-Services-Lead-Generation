-- Check if public.leads table exists and has the required schema
-- This script verifies the table structure and RLS configuration

-- 1. Check if table exists
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_name = 'leads'
        ) 
        THEN 'public.leads table EXISTS' 
        ELSE 'public.leads table DOES NOT EXIST'
    END AS table_status;

-- 2. Verify table structure (only if table exists)
SELECT 
    column_name,
    data_type,
    column_default,
    is_nullable
FROM information_schema.columns 
WHERE table_schema = 'public' 
  AND table_name = 'leads'
ORDER BY ordinal_position;

-- 3. Verify RLS is enabled
SELECT 
    schemaname, 
    tablename, 
    rowsecurity AS rls_enabled
FROM pg_tables 
WHERE schemaname = 'public' 
  AND tablename = 'leads';

-- 4. Check existing policies
SELECT 
    policyname,
    roles,
    cmd AS command,
    permissive,
    qual,
    with_check
FROM pg_policies 
WHERE schemaname = 'public' 
  AND tablename = 'leads'
ORDER BY policyname;

-- 5. Check if pgcrypto extension is installed
SELECT 
    extname,
    extversion
FROM pg_extension 
WHERE extname = 'pgcrypto';

-- 6. Verify required fields exist with correct types
SELECT 
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
              AND table_name = 'leads' 
              AND column_name = 'id' 
              AND data_type = 'uuid'
        ) THEN '✓ id UUID field exists'
        ELSE '✗ id UUID field missing'
    END AS id_check,
    
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
              AND table_name = 'leads' 
              AND column_name = 'created_at' 
              AND data_type = 'timestamp with time zone'
        ) THEN '✓ created_at TIMESTAMPTZ field exists'
        ELSE '✗ created_at TIMESTAMPTZ field missing'
    END AS created_at_check,
    
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
              AND table_name = 'leads' 
              AND column_name = 'phone' 
              AND data_type = 'text'
        ) THEN '✓ phone TEXT field exists'
        ELSE '✗ phone TEXT field missing'
    END AS phone_check,
    
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public' 
              AND table_name = 'leads' 
              AND column_name = 'metadata' 
              AND data_type = 'jsonb'
        ) THEN '✓ metadata JSONB field exists'
        ELSE '✗ metadata JSONB field missing'
    END AS metadata_check;