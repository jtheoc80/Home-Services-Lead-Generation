-- =====================================================================
-- Test Script for upsert_leads_from_permits_limit() RPC Function
-- =====================================================================
-- This script tests the upsert_leads_from_permits_limit() function to ensure:
-- 1. Function exists and can be called
-- 2. Uses correct issued_date column (not issue_date)
-- 3. Properly respects limit parameter
-- 4. Properly respects days parameter  
-- 5. Returns correct counts
-- 6. Works with parameters from problem statement: p_limit=50, p_days=365
-- =====================================================================

-- Test 1: Verify function exists
DO $$
DECLARE
    function_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.routines 
        WHERE routine_schema = 'public' 
        AND routine_name = 'upsert_leads_from_permits_limit'
        AND routine_type = 'FUNCTION'
    ) INTO function_exists;
    
    IF function_exists THEN
        RAISE NOTICE 'TEST 1 PASSED: upsert_leads_from_permits_limit() function exists';
    ELSE
        RAISE EXCEPTION 'TEST 1 FAILED: upsert_leads_from_permits_limit() function does not exist';
    END IF;
END;
$$;

-- Test 2: Cleanup and insert sample permit data for testing
DELETE FROM public.leads WHERE source = 'test_limit_function';
DELETE FROM public.permits WHERE source = 'test_limit_function';

-- Insert test permits with various dates
INSERT INTO public.permits (
    id,
    source, 
    source_record_id, 
    permit_id, 
    permit_number, 
    issued_date,
    application_date,
    permit_type, 
    permit_class, 
    work_description, 
    address, 
    city, 
    county, 
    zipcode, 
    latitude, 
    longitude, 
    valuation, 
    applicant_name, 
    contractor_name, 
    status,
    created_at,
    updated_at
) VALUES 
-- Recent permits (within 365 days)
(gen_random_uuid(), 'test_limit_function', 'TEST-LIMIT-1', 'TEST-LIMIT-1', 'TEST-LIMIT-1', 
 NOW() - INTERVAL '10 days', NOW() - INTERVAL '15 days', 'Residential', 'Building', 
 'Kitchen Remodel', '123 Test St', 'Houston', 'Harris', '77001', 29.7604, -95.3698, 
 75000, 'John Doe', 'ABC Construction', 'Issued', NOW(), NOW()),

(gen_random_uuid(), 'test_limit_function', 'TEST-LIMIT-2', 'TEST-LIMIT-2', 'TEST-LIMIT-2', 
 NOW() - INTERVAL '20 days', NOW() - INTERVAL '25 days', 'Residential', 'Electrical', 
 'Panel Upgrade', '456 Test Ave', 'Austin', 'Travis', '78701', 30.2672, -97.7431, 
 12000, 'Jane Smith', 'XYZ Electric', 'Issued', NOW(), NOW()),

(gen_random_uuid(), 'test_limit_function', 'TEST-LIMIT-3', 'TEST-LIMIT-3', 'TEST-LIMIT-3', 
 NOW() - INTERVAL '30 days', NOW() - INTERVAL '35 days', 'Residential', 'Plumbing', 
 'Bathroom Remodel', '789 Test Blvd', 'Dallas', 'Dallas', '75201', 32.7767, -96.7970, 
 45000, 'Bob Johnson', 'Best Plumbing', 'Issued', NOW(), NOW()),

-- More permits to test limit functionality
(gen_random_uuid(), 'test_limit_function', 'TEST-LIMIT-4', 'TEST-LIMIT-4', 'TEST-LIMIT-4', 
 NOW() - INTERVAL '5 days', NOW() - INTERVAL '10 days', 'Commercial', 'HVAC', 
 'AC Installation', '321 Business Dr', 'San Antonio', 'Bexar', '78201', 29.4241, -98.4936, 
 25000, 'Sarah Wilson', 'Cool Air Co', 'Issued', NOW(), NOW()),

(gen_random_uuid(), 'test_limit_function', 'TEST-LIMIT-5', 'TEST-LIMIT-5', 'TEST-LIMIT-5', 
 NOW() - INTERVAL '7 days', NOW() - INTERVAL '12 days', 'Residential', 'Roofing', 
 'Roof Replacement', '654 Maple St', 'Fort Worth', 'Tarrant', '76101', 32.7555, -97.3308, 
 35000, 'Mike Davis', 'Top Roofing', 'Issued', NOW(), NOW()),

-- Old permit (beyond 365 days) - should be excluded when p_days=365
(gen_random_uuid(), 'test_limit_function', 'TEST-LIMIT-OLD', 'TEST-LIMIT-OLD', 'TEST-LIMIT-OLD', 
 NOW() - INTERVAL '400 days', NOW() - INTERVAL '405 days', 'Residential', 'Building', 
 'Old Permit', '999 Old St', 'Houston', 'Harris', '77002', 29.7604, -95.3698, 
 50000, 'Old Owner', 'Old Contractor', 'Issued', NOW(), NOW());

-- Test 3: Test function without parameters (should process all test permits)
DO $$
DECLARE
    result RECORD;
BEGIN
    RAISE NOTICE 'TEST 3: Testing function without parameters';
    SELECT * FROM public.upsert_leads_from_permits_limit() INTO result;
    
    RAISE NOTICE 'Result: inserted=%, updated=%, total=%', 
        result.inserted_count, result.updated_count, result.total_processed;
        
    IF result.total_processed >= 5 THEN  -- Should process at least our 5 recent test permits
        RAISE NOTICE 'TEST 3 PASSED: Function processed permits without parameters';
    ELSE
        RAISE EXCEPTION 'TEST 3 FAILED: Expected at least 5 permits processed, got %', result.total_processed;
    END IF;
END;
$$;

-- Test 4: Test function with limit only (p_limit=2)
DO $$
DECLARE
    result RECORD;
BEGIN
    RAISE NOTICE 'TEST 4: Testing function with limit=2';
    SELECT * FROM public.upsert_leads_from_permits_limit(2, NULL) INTO result;
    
    RAISE NOTICE 'Result: inserted=%, updated=%, total=%', 
        result.inserted_count, result.updated_count, result.total_processed;
        
    IF result.total_processed = 2 THEN
        RAISE NOTICE 'TEST 4 PASSED: Function respected limit parameter';
    ELSE
        RAISE EXCEPTION 'TEST 4 FAILED: Expected 2 permits processed, got %', result.total_processed;
    END IF;
END;
$$;

-- Test 5: Test function with days filter (p_days=15, should exclude permits older than 15 days)
DO $$
DECLARE
    result RECORD;
    expected_count INTEGER;
BEGIN
    RAISE NOTICE 'TEST 5: Testing function with days=15';
    
    -- Count permits within 15 days
    SELECT COUNT(*) INTO expected_count
    FROM public.permits 
    WHERE source = 'test_limit_function' 
    AND COALESCE(issued_date, created_at, NOW()) >= NOW() - INTERVAL '15 days';
    
    RAISE NOTICE 'Expected permits within 15 days: %', expected_count;
    
    SELECT * FROM public.upsert_leads_from_permits_limit(NULL, 15) INTO result;
    
    RAISE NOTICE 'Result: inserted=%, updated=%, total=%', 
        result.inserted_count, result.updated_count, result.total_processed;
        
    IF result.total_processed = expected_count THEN
        RAISE NOTICE 'TEST 5 PASSED: Function respected days parameter';
    ELSE
        RAISE EXCEPTION 'TEST 5 FAILED: Expected % permits processed, got %', expected_count, result.total_processed;
    END IF;
END;
$$;

-- Test 6: Test function with both parameters (p_limit=50, p_days=365) - matches problem statement
DO $$
DECLARE
    result RECORD;
    expected_count INTEGER;
    actual_limit INTEGER;
BEGIN
    RAISE NOTICE 'TEST 6: Testing function with limit=50, days=365 (problem statement parameters)';
    
    -- Count permits within 365 days (should exclude the old one)
    SELECT COUNT(*) INTO expected_count
    FROM public.permits 
    WHERE source = 'test_limit_function' 
    AND COALESCE(issued_date, created_at, NOW()) >= NOW() - INTERVAL '365 days';
    
    RAISE NOTICE 'Expected permits within 365 days: %', expected_count;
    
    -- Since we have fewer than 50 test permits, we should get all within 365 days
    actual_limit := LEAST(50, expected_count);
    
    SELECT * FROM public.upsert_leads_from_permits_limit(50, 365) INTO result;
    
    RAISE NOTICE 'Result: inserted=%, updated=%, total=%', 
        result.inserted_count, result.updated_count, result.total_processed;
        
    IF result.total_processed = actual_limit THEN
        RAISE NOTICE 'TEST 6 PASSED: Function worked with problem statement parameters (limit=50, days=365)';
    ELSE
        RAISE EXCEPTION 'TEST 6 FAILED: Expected % permits processed, got %', actual_limit, result.total_processed;
    END IF;
END;
$$;

-- Test 7: Verify leads were created correctly
DO $$
DECLARE
    lead_count INTEGER;
BEGIN
    RAISE NOTICE 'TEST 7: Verifying leads were created correctly';
    
    SELECT COUNT(*) INTO lead_count
    FROM public.leads 
    WHERE source = 'permit_ingest'
    AND permit_id IN (
        SELECT id FROM public.permits WHERE source = 'test_limit_function'
    );
    
    RAISE NOTICE 'Total leads created from test permits: %', lead_count;
    
    IF lead_count > 0 THEN
        RAISE NOTICE 'TEST 7 PASSED: Leads were created from permits';
    ELSE
        RAISE EXCEPTION 'TEST 7 FAILED: No leads were created from test permits';
    END IF;
END;
$$;

-- Test 8: Verify function uses correct date column (issued_date)
DO $$
DECLARE
    function_source TEXT;
BEGIN
    RAISE NOTICE 'TEST 8: Verifying function uses issued_date column';
    
    SELECT prosrc INTO function_source
    FROM pg_proc p
    JOIN pg_namespace n ON p.pronamespace = n.oid
    WHERE n.nspname = 'public' 
    AND p.proname = 'upsert_leads_from_permits_limit';
    
    IF function_source LIKE '%issued_date%' AND function_source NOT LIKE '%issue_date%' THEN
        RAISE NOTICE 'TEST 8 PASSED: Function uses issued_date column (not issue_date)';
    ELSE
        RAISE EXCEPTION 'TEST 8 FAILED: Function may not be using correct date column';
    END IF;
END;
$$;

-- Cleanup test data
DELETE FROM public.leads WHERE source = 'permit_ingest' AND permit_id IN (
    SELECT id FROM public.permits WHERE source = 'test_limit_function'
);
DELETE FROM public.permits WHERE source = 'test_limit_function';

RAISE NOTICE 'All tests completed successfully! Function upsert_leads_from_permits_limit is working correctly.';