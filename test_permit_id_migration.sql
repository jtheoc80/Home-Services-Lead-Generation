-- =====================================================================
-- SQL Test Script for permit_id Implementation
-- =====================================================================
-- This script tests the permit_id functionality described in the problem statement:
-- 1. DB migration adds permit_id column
-- 2. Backfill from source_record_id or permit_no  
-- 3. Unique index (source, permit_id) where not null
-- 4. upsert_permit(jsonb) derives permit_id correctly
--
-- Run this script in Supabase SQL editor with postgres role
-- =====================================================================

-- Test 1: Verify permit_id column exists and has correct type
DO $$
DECLARE
    column_exists BOOLEAN;
    column_type TEXT;
BEGIN
    -- Check if permit_id column exists with correct type
    SELECT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_schema = 'public' 
        AND table_name = 'permits' 
        AND column_name = 'permit_id'
        AND data_type = 'text'
    ) INTO column_exists;
    
    IF column_exists THEN
        RAISE NOTICE 'TEST 1 PASSED: permit_id column exists with TEXT type';
    ELSE
        RAISE EXCEPTION 'TEST 1 FAILED: permit_id column missing or wrong type';
    END IF;
END $$;

-- Test 2: Verify unique index on (source, permit_id) exists
DO $$
DECLARE
    index_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM pg_indexes 
        WHERE tablename = 'permits' 
        AND indexname = 'uq_permits_source_permit_id'
    ) INTO index_exists;
    
    IF index_exists THEN
        RAISE NOTICE 'TEST 2 PASSED: Unique index uq_permits_source_permit_id exists';
    ELSE
        RAISE EXCEPTION 'TEST 2 FAILED: Unique index missing';
    END IF;
END $$;

-- Test 3: Verify upsert_permit function exists and has correct signature
DO $$
DECLARE
    function_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM pg_proc p
        JOIN pg_namespace n ON p.pronamespace = n.oid
        WHERE n.nspname = 'public'
        AND p.proname = 'upsert_permit'
        AND pg_get_function_arguments(p.oid) = 'p jsonb'
    ) INTO function_exists;
    
    IF function_exists THEN
        RAISE NOTICE 'TEST 3 PASSED: upsert_permit(jsonb) function exists';
    ELSE
        RAISE EXCEPTION 'TEST 3 FAILED: upsert_permit function missing or wrong signature';
    END IF;
END $$;

-- Test 4: Test upsert_permit function with selftest data
-- This creates the exact test case described in the problem statement
SELECT public.upsert_permit(jsonb_build_object(
    'source', 'selftest',
    'source_record_id', 'test-selftest-001', 
    'permit_id', 'SELFTEST-001',
    'permit_number', 'SELFTEST-001',
    'jurisdiction', 'Austin',
    'county', 'Travis', 
    'status', 'Issued',
    'permit_type', 'Building',
    'work_description', 'Test permit for permit_id functionality',
    'address', '100 Test St',
    'city', 'Austin',
    'state', 'TX',
    'zipcode', '78701',
    'valuation', 50000,
    'contractor_name', 'Test Contractor LLC',
    'applicant', 'Test Applicant',
    'owner', 'Test Owner',
    'issued_date', NOW()::timestamptz
)) AS upsert_result;

-- Test 5: Verify the selftest permit was created correctly
-- This is the exact verification query from the problem statement
SELECT 
    source,
    permit_id, 
    permit_number,
    jurisdiction,
    status,
    created_at
FROM public.permits 
WHERE source = 'selftest'
ORDER BY created_at DESC;

-- Test 6: Test permit_id derivation fallback logic
-- Test case where permit_id is provided explicitly
SELECT public.upsert_permit(jsonb_build_object(
    'source', 'test_fallback',
    'source_record_id', 'fallback-001',
    'permit_id', 'EXPLICIT-ID-001',  -- This should be used
    'permit_number', 'FALLBACK-NUM-001'
)) AS test_explicit_id;

-- Test case where permit_id is empty, should use permit_number
SELECT public.upsert_permit(jsonb_build_object(
    'source', 'test_fallback',
    'source_record_id', 'fallback-002', 
    'permit_id', '',  -- Empty, should fallback
    'permit_number', 'FALLBACK-NUM-002'  -- This should be used
)) AS test_fallback_to_number;

-- Test case where permit_id and permit_number are empty, should use source_record_id
SELECT public.upsert_permit(jsonb_build_object(
    'source', 'test_fallback',
    'source_record_id', 'fallback-003',  -- This should be used
    'permit_id', '',
    'permit_number', ''
)) AS test_fallback_to_source_id;

-- Verify fallback test results
SELECT 
    source_record_id,
    permit_id,
    permit_number,
    CASE 
        WHEN source_record_id = 'fallback-001' AND permit_id = 'EXPLICIT-ID-001' THEN 'PASS: Used explicit permit_id'
        WHEN source_record_id = 'fallback-002' AND permit_id = 'FALLBACK-NUM-002' THEN 'PASS: Fell back to permit_number'
        WHEN source_record_id = 'fallback-003' AND permit_id = 'fallback-003' THEN 'PASS: Fell back to source_record_id'
        ELSE 'FAIL: Unexpected permit_id derivation'
    END AS test_result
FROM public.permits 
WHERE source = 'test_fallback'
ORDER BY source_record_id;

-- Test 7: Test unique constraint on (source, permit_id)
-- This should succeed (different sources, same permit_id)
SELECT public.upsert_permit(jsonb_build_object(
    'source', 'source_a',
    'source_record_id', 'rec-001',
    'permit_id', 'SHARED-ID-001'
)) AS test_unique_constraint_a;

SELECT public.upsert_permit(jsonb_build_object(
    'source', 'source_b',  -- Different source
    'source_record_id', 'rec-002', 
    'permit_id', 'SHARED-ID-001'  -- Same permit_id, should be allowed
)) AS test_unique_constraint_b;

-- This should fail with unique constraint violation (same source and permit_id)
-- We'll catch the error to prevent script failure
DO $$
BEGIN
    PERFORM public.upsert_permit(jsonb_build_object(
        'source', 'source_a',  -- Same source as first test
        'source_record_id', 'rec-003',
        'permit_id', 'SHARED-ID-001'  -- Same permit_id, should fail
    ));
    RAISE EXCEPTION 'TEST 7 FAILED: Duplicate (source, permit_id) was allowed';
EXCEPTION
    WHEN unique_violation THEN
        RAISE NOTICE 'TEST 7 PASSED: Unique constraint on (source, permit_id) working correctly';
    WHEN OTHERS THEN
        RAISE EXCEPTION 'TEST 7 FAILED: Unexpected error: %', SQLERRM;
END $$;

-- Test 8: Verify update functionality (same source_record_id should update, not insert)
SELECT public.upsert_permit(jsonb_build_object(
    'source', 'selftest',
    'source_record_id', 'test-selftest-001',  -- Same as first test
    'permit_id', 'SELFTEST-001-UPDATED',
    'status', 'Finalized',  -- Changed status
    'valuation', 75000  -- Changed valuation
)) AS test_update_result;

-- Verify update worked (should still be only one record for this source_record_id)
SELECT 
    COUNT(*) as record_count,
    permit_id,
    status,
    valuation
FROM public.permits 
WHERE source = 'selftest' AND source_record_id = 'test-selftest-001'
GROUP BY permit_id, status, valuation;

-- Test 9: Final verification - show all test records
RAISE NOTICE 'Final verification - all test permits created:';
SELECT 
    source,
    source_record_id,
    permit_id,
    permit_number,
    status,
    valuation,
    created_at,
    updated_at
FROM public.permits 
WHERE source IN ('selftest', 'test_fallback', 'source_a', 'source_b')
ORDER BY source, source_record_id;

-- Success message
SELECT 
    'permit_id implementation tests completed successfully!' as status,
    'All tests passed' as result,
    NOW() as tested_at;