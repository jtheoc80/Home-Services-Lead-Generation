-- =====================================================================
-- Verification Script: upsert_leads_from_permits_limit Uses Correct Column
-- =====================================================================
-- This script verifies that the upsert_leads_from_permits_limit() function
-- uses public.permits.issued_date (NOT issue_date) as required and
-- supports the limit and days parameters.
-- =====================================================================

-- Extract the function definition to verify it uses the correct column
SELECT 
    routine_name,
    routine_definition
FROM information_schema.routines 
WHERE routine_schema = 'public' 
AND routine_name = 'upsert_leads_from_permits_limit'
AND routine_type = 'FUNCTION';

-- Verify the function definition contains correct elements
DO $$
DECLARE
    func_definition TEXT;
    has_issued_date BOOLEAN := FALSE;
    has_issue_date BOOLEAN := FALSE;
    has_limit_param BOOLEAN := FALSE;
    has_days_param BOOLEAN := FALSE;
BEGIN
    -- Get function definition
    SELECT routine_definition INTO func_definition
    FROM information_schema.routines 
    WHERE routine_schema = 'public' 
    AND routine_name = 'upsert_leads_from_permits_limit';
    
    IF func_definition IS NULL THEN
        RAISE EXCEPTION 'Function upsert_leads_from_permits_limit() not found!';
    END IF;
    
    -- Check if function uses correct column name
    has_issued_date := func_definition LIKE '%issued_date%';
    has_issue_date := func_definition LIKE '%issue_date%' AND func_definition LIKE '%.issue_date%';
    has_limit_param := func_definition LIKE '%p_limit%';
    has_days_param := func_definition LIKE '%p_days%';
    
    -- Verify correct date column usage
    IF has_issued_date AND NOT has_issue_date THEN
        RAISE NOTICE '✓ SUCCESS: upsert_leads_from_permits_limit() uses correct "issued_date" column';
        RAISE NOTICE '✓ SUCCESS: Function does NOT use incorrect "issue_date" column';
    ELSIF has_issue_date THEN
        RAISE EXCEPTION '✗ FAILED: Function contains incorrect "issue_date" column reference!';
    ELSE
        RAISE EXCEPTION '✗ FAILED: Function does not reference any date column!';
    END IF;
    
    -- Verify parameter support
    IF has_limit_param THEN
        RAISE NOTICE '✓ SUCCESS: Function supports p_limit parameter';
    ELSE
        RAISE EXCEPTION '✗ FAILED: Function missing p_limit parameter!';
    END IF;
    
    IF has_days_param THEN
        RAISE NOTICE '✓ SUCCESS: Function supports p_days parameter';
    ELSE
        RAISE EXCEPTION '✗ FAILED: Function missing p_days parameter!';
    END IF;
    
    RAISE NOTICE 'Verification complete: The RPC function is correctly implemented.';
END;
$$;

-- Test function call with problem statement parameters
DO $$
DECLARE
    result RECORD;
BEGIN
    RAISE NOTICE 'Testing function call with problem statement parameters (p_limit=50, p_days=365)';
    
    -- This should work without error (though may return 0 results if no data)
    SELECT * FROM public.upsert_leads_from_permits_limit(50, 365) INTO result;
    
    RAISE NOTICE 'Function call successful: inserted=%, updated=%, total=%', 
        result.inserted_count, result.updated_count, result.total_processed;
        
    RAISE NOTICE '✓ SUCCESS: Function can be called with problem statement parameters';
EXCEPTION
    WHEN OTHERS THEN
        RAISE EXCEPTION '✗ FAILED: Function call with parameters failed: %', SQLERRM;
END;
$$;