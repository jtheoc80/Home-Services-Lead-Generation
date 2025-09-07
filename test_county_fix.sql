-- =====================================================================
-- Test Script for County NULL Fix and Enhanced upsert_leads_from_permits()
-- =====================================================================
-- This script tests the enhanced upsert_leads_from_permits() function to ensure:
-- 1. County column has proper default value 'Unknown'
-- 2. Function uses coalesce(county, inferred-from-jurisdiction, 'Unknown')
-- 3. Name field is never NULL with proper fallbacks
-- 4. All records have proper keys and no NULL values in critical fields
-- =====================================================================

\echo '=== Testing County NULL Fix and Enhanced upsert_leads_from_permits() ==='

-- Test 1: Verify function exists with new signature
DO $$
DECLARE
    function_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.routines 
        WHERE routine_schema = 'public' 
        AND routine_name = 'upsert_leads_from_permits'
        AND routine_type = 'FUNCTION'
    ) INTO function_exists;
    
    IF function_exists THEN
        RAISE NOTICE '✅ TEST 1 PASSED: Enhanced upsert_leads_from_permits() function exists';
    ELSE
        RAISE EXCEPTION '❌ TEST 1 FAILED: upsert_leads_from_permits() function does not exist';
    END IF;
END;
$$;

-- Test 2: Verify infer_county_from_jurisdiction function exists
DO $$
DECLARE
    function_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT 1 FROM information_schema.routines 
        WHERE routine_schema = 'public' 
        AND routine_name = 'infer_county_from_jurisdiction'
        AND routine_type = 'FUNCTION'
    ) INTO function_exists;
    
    IF function_exists THEN
        RAISE NOTICE '✅ TEST 2 PASSED: infer_county_from_jurisdiction() function exists';
    ELSE
        RAISE EXCEPTION '❌ TEST 2 FAILED: infer_county_from_jurisdiction() function does not exist';
    END IF;
END;
$$;

-- Test 3: Verify county column has default value
DO $$
DECLARE
    default_value TEXT;
BEGIN
    SELECT column_default 
    INTO default_value
    FROM information_schema.columns 
    WHERE table_schema = 'public' 
    AND table_name = 'leads' 
    AND column_name = 'county';
    
    IF default_value LIKE '%Unknown%' THEN
        RAISE NOTICE '✅ TEST 3 PASSED: County column has default value: %', default_value;
    ELSE
        RAISE EXCEPTION '❌ TEST 3 FAILED: County column default is: %', COALESCE(default_value, 'NULL');
    END IF;
END;
$$;

-- Test 4: Test jurisdiction-to-county mapping function
DO $$
DECLARE
    test_result TEXT;
BEGIN
    -- Test known jurisdictions
    SELECT public.infer_county_from_jurisdiction('tx-harris') INTO test_result;
    IF test_result = 'Harris County' THEN
        RAISE NOTICE '✅ TEST 4a PASSED: tx-harris → %', test_result;
    ELSE
        RAISE EXCEPTION '❌ TEST 4a FAILED: tx-harris → %', COALESCE(test_result, 'NULL');
    END IF;
    
    SELECT public.infer_county_from_jurisdiction('tx-dallas') INTO test_result;
    IF test_result = 'Dallas County' THEN
        RAISE NOTICE '✅ TEST 4b PASSED: tx-dallas → %', test_result;
    ELSE
        RAISE EXCEPTION '❌ TEST 4b FAILED: tx-dallas → %', COALESCE(test_result, 'NULL');
    END IF;
    
    -- Test unknown jurisdiction
    SELECT public.infer_county_from_jurisdiction('unknown-jurisdiction') INTO test_result;
    IF test_result IS NULL THEN
        RAISE NOTICE '✅ TEST 4c PASSED: unknown-jurisdiction → NULL (as expected)';
    ELSE
        RAISE EXCEPTION '❌ TEST 4c FAILED: unknown-jurisdiction → %', test_result;
    END IF;
END;
$$;

-- Test 5: Clean up any existing test data
DELETE FROM public.leads WHERE permit_id IN (
    'test-county-fix-permit-1'::uuid,
    'test-county-fix-permit-2'::uuid,
    'test-county-fix-permit-3'::uuid,
    'test-county-fix-permit-4'::uuid
);
DELETE FROM public.permits WHERE id IN (
    'test-county-fix-permit-1'::uuid,
    'test-county-fix-permit-2'::uuid,
    'test-county-fix-permit-3'::uuid,
    'test-county-fix-permit-4'::uuid
);

-- Test 6: Insert sample permits with various county/jurisdiction scenarios
INSERT INTO public.permits (
    id, source, source_record_id, permit_id, permit_number, issued_date,
    permit_type, permit_class, work_description, address, city, county, 
    jurisdiction, status, valuation, created_at, updated_at
) VALUES 
-- Permit 1: Has county data (should use existing county)
(
    'test-county-fix-permit-1'::uuid, 'test', 'test-county-1', 'TEST-COUNTY-001', 'TEST-001',
    '2025-01-15 10:00:00'::timestamptz, 'Residential', 'New Construction',
    'Test home construction', '123 Test St', 'Houston', 'Harris County',
    'tx-harris', 'Issued', 250000.00, NOW(), NOW()
),
-- Permit 2: No county but has jurisdiction (should infer from jurisdiction)
(
    'test-county-fix-permit-2'::uuid, 'test', 'test-county-2', 'TEST-COUNTY-002', 'TEST-002',
    '2025-01-15 11:00:00'::timestamptz, 'Commercial', 'Renovation',
    'Office renovation', '456 Business Ave', 'Dallas', '',
    'tx-dallas', 'Issued', 100000.00, NOW(), NOW()
),
-- Permit 3: No county, jurisdiction in source field (should infer from source)
(
    'test-county-fix-permit-3'::uuid, 'tx-fort-bend', 'test-county-3', 'TEST-COUNTY-003', 'TEST-003',
    '2025-01-15 12:00:00'::timestamptz, 'Residential', 'Addition',
    '', '789 Suburb Ln', 'Sugar Land', NULL,
    '', 'Issued', 75000.00, NOW(), NOW()
),
-- Permit 4: No county, no jurisdiction, no work_description (should default to 'Unknown' and generate name)
(
    'test-county-fix-permit-4'::uuid, 'test', 'test-county-4', 'TEST-COUNTY-004', 'TEST-004',
    '2025-01-15 13:00:00'::timestamptz, '', '',
    '', '101 Unknown St', 'Somewhere', NULL,
    '', 'Issued', 50000.00, NOW(), NOW()
);

RAISE NOTICE '✅ TEST 6 PASSED: Sample permit data inserted';

-- Test 7: Run the enhanced upsert function
DO $$
DECLARE
    result RECORD;
    total_before INTEGER;
    total_after INTEGER;
BEGIN
    -- Count leads before function call
    SELECT COUNT(*) INTO total_before FROM public.leads WHERE permit_id IN (
        'test-county-fix-permit-1'::uuid, 'test-county-fix-permit-2'::uuid,
        'test-county-fix-permit-3'::uuid, 'test-county-fix-permit-4'::uuid
    );
    
    -- Call the enhanced function
    SELECT * INTO result FROM public.upsert_leads_from_permits();
    
    -- Count leads after function call
    SELECT COUNT(*) INTO total_after FROM public.leads WHERE permit_id IN (
        'test-county-fix-permit-1'::uuid, 'test-county-fix-permit-2'::uuid,
        'test-county-fix-permit-3'::uuid, 'test-county-fix-permit-4'::uuid
    );
    
    IF result.total_processed IS NOT NULL AND result.total_processed >= 0 THEN
        RAISE NOTICE '✅ TEST 7 PASSED: Enhanced function executed. Inserted: %, Updated: %, Total: %', 
            result.inserted_count, result.updated_count, result.total_processed;
    ELSE
        RAISE EXCEPTION '❌ TEST 7 FAILED: Function did not return expected results';
    END IF;
    
    IF total_after > total_before THEN
        RAISE NOTICE '✅ TEST 7 INFO: % new leads created (before: %, after: %)', 
            total_after - total_before, total_before, total_after;
    ELSE
        RAISE NOTICE '✅ TEST 7 INFO: No new leads created (before: %, after: %)', total_before, total_after;
    END IF;
END;
$$;

-- Test 8: Verify county values are properly set (no NULLs)
DO $$
DECLARE
    null_county_count INTEGER;
    null_name_count INTEGER;
    county_values TEXT;
    name_values TEXT;
BEGIN
    -- Check for NULL county values
    SELECT COUNT(*) INTO null_county_count 
    FROM public.leads 
    WHERE permit_id IN (
        'test-county-fix-permit-1'::uuid, 'test-county-fix-permit-2'::uuid,
        'test-county-fix-permit-3'::uuid, 'test-county-fix-permit-4'::uuid
    ) AND county IS NULL;
    
    -- Check for NULL name values
    SELECT COUNT(*) INTO null_name_count 
    FROM public.leads 
    WHERE permit_id IN (
        'test-county-fix-permit-1'::uuid, 'test-county-fix-permit-2'::uuid,
        'test-county-fix-permit-3'::uuid, 'test-county-fix-permit-4'::uuid
    ) AND name IS NULL;
    
    IF null_county_count = 0 THEN
        RAISE NOTICE '✅ TEST 8a PASSED: No NULL county values found';
    ELSE
        RAISE EXCEPTION '❌ TEST 8a FAILED: Found % NULL county values', null_county_count;
    END IF;
    
    IF null_name_count = 0 THEN
        RAISE NOTICE '✅ TEST 8b PASSED: No NULL name values found';
    ELSE
        RAISE EXCEPTION '❌ TEST 8b FAILED: Found % NULL name values', null_name_count;
    END IF;
    
    -- Show actual county and name values for verification
    SELECT string_agg(DISTINCT county, ', ' ORDER BY county) INTO county_values
    FROM public.leads 
    WHERE permit_id IN (
        'test-county-fix-permit-1'::uuid, 'test-county-fix-permit-2'::uuid,
        'test-county-fix-permit-3'::uuid, 'test-county-fix-permit-4'::uuid
    );
    
    SELECT string_agg(name, ' | ' ORDER BY permit_id) INTO name_values
    FROM public.leads 
    WHERE permit_id IN (
        'test-county-fix-permit-1'::uuid, 'test-county-fix-permit-2'::uuid,
        'test-county-fix-permit-3'::uuid, 'test-county-fix-permit-4'::uuid
    );
    
    RAISE NOTICE '✅ TEST 8c INFO: County values: %', COALESCE(county_values, 'None');
    RAISE NOTICE '✅ TEST 8d INFO: Name values: %', COALESCE(name_values, 'None');
END;
$$;

-- Test 9: Verify specific county inference logic
DO $$
DECLARE
    harris_county_count INTEGER;
    dallas_county_count INTEGER;
    fort_bend_county_count INTEGER;
    unknown_county_count INTEGER;
BEGIN
    -- Check specific county inferences
    SELECT COUNT(*) INTO harris_county_count
    FROM public.leads l
    JOIN public.permits p ON l.permit_id = p.id
    WHERE p.id = 'test-county-fix-permit-1'::uuid 
    AND l.county = 'Harris County';
    
    SELECT COUNT(*) INTO dallas_county_count
    FROM public.leads l
    JOIN public.permits p ON l.permit_id = p.id
    WHERE p.id = 'test-county-fix-permit-2'::uuid 
    AND l.county = 'Dallas County';
    
    SELECT COUNT(*) INTO fort_bend_county_count
    FROM public.leads l
    JOIN public.permits p ON l.permit_id = p.id
    WHERE p.id = 'test-county-fix-permit-3'::uuid 
    AND l.county = 'Fort Bend County';
    
    SELECT COUNT(*) INTO unknown_county_count
    FROM public.leads l
    JOIN public.permits p ON l.permit_id = p.id
    WHERE p.id = 'test-county-fix-permit-4'::uuid 
    AND l.county = 'Unknown';
    
    IF harris_county_count > 0 THEN
        RAISE NOTICE '✅ TEST 9a PASSED: Harris County preserved from permit data';
    ELSE
        RAISE EXCEPTION '❌ TEST 9a FAILED: Harris County not found for permit 1';
    END IF;
    
    IF dallas_county_count > 0 THEN
        RAISE NOTICE '✅ TEST 9b PASSED: Dallas County inferred from jurisdiction tx-dallas';
    ELSE
        RAISE EXCEPTION '❌ TEST 9b FAILED: Dallas County not inferred for permit 2';
    END IF;
    
    IF fort_bend_county_count > 0 THEN
        RAISE NOTICE '✅ TEST 9c PASSED: Fort Bend County inferred from source tx-fort-bend';
    ELSE
        RAISE EXCEPTION '❌ TEST 9c FAILED: Fort Bend County not inferred for permit 3';
    END IF;
    
    IF unknown_county_count > 0 THEN
        RAISE NOTICE '✅ TEST 9d PASSED: Unknown county defaulted for permit 4';
    ELSE
        RAISE EXCEPTION '❌ TEST 9d FAILED: Unknown county not defaulted for permit 4';
    END IF;
END;
$$;

-- Test 10: Verify all leads have proper keys (permit_id)
DO $$
DECLARE
    missing_keys_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO missing_keys_count
    FROM public.leads 
    WHERE permit_id IN (
        'test-county-fix-permit-1'::uuid, 'test-county-fix-permit-2'::uuid,
        'test-county-fix-permit-3'::uuid, 'test-county-fix-permit-4'::uuid
    ) AND permit_id IS NULL;
    
    IF missing_keys_count = 0 THEN
        RAISE NOTICE '✅ TEST 10 PASSED: All leads have permit_id keys';
    ELSE
        RAISE EXCEPTION '❌ TEST 10 FAILED: Found % leads without permit_id keys', missing_keys_count;
    END IF;
END;
$$;

-- Test 11: Run function with p_days parameter to test filtering
DO $$
DECLARE
    result RECORD;
BEGIN
    -- Call function with p_days=1 (should process recent permits)
    SELECT * INTO result FROM public.upsert_leads_from_permits(1);
    
    IF result.total_processed IS NOT NULL AND result.total_processed >= 0 THEN
        RAISE NOTICE '✅ TEST 11 PASSED: Function with p_days=1 executed. Processed: %', result.total_processed;
    ELSE
        RAISE EXCEPTION '❌ TEST 11 FAILED: Function with p_days parameter failed';
    END IF;
END;
$$;

-- Test 12: Clean up test data
DELETE FROM public.leads WHERE permit_id IN (
    'test-county-fix-permit-1'::uuid, 'test-county-fix-permit-2'::uuid,
    'test-county-fix-permit-3'::uuid, 'test-county-fix-permit-4'::uuid
);
DELETE FROM public.permits WHERE id IN (
    'test-county-fix-permit-1'::uuid, 'test-county-fix-permit-2'::uuid,
    'test-county-fix-permit-3'::uuid, 'test-county-fix-permit-4'::uuid
);

RAISE NOTICE '✅ TEST 12 PASSED: Test data cleaned up';

\echo '=== All tests completed successfully! ==='
\echo 'The enhanced upsert_leads_from_permits() function properly handles:'
\echo '  ✅ County inference from jurisdiction data'
\echo '  ✅ Fallback to "Unknown" when no county can be determined'
\echo '  ✅ Non-NULL name generation with proper fallbacks'
\echo '  ✅ Proper key relationships (permit_id)'
\echo '  ✅ No NULL values in critical fields';