-- =====================================================================
-- Verification Script: upsert_leads_from_permits Uses Correct Column
-- =====================================================================
-- This script verifies that the upsert_leads_from_permits() function
-- uses public.permits.issued_date (NOT issue_date) as required.
-- =====================================================================

-- Extract the function definition to verify it uses the correct column
SELECT 
    routine_name,
    routine_definition
FROM information_schema.routines 
WHERE routine_schema = 'public' 
AND routine_name = 'upsert_leads_from_permits'
AND routine_type = 'FUNCTION';

-- Verify the function definition contains "issued_date" and NOT "issue_date"
DO $$
DECLARE
    func_definition TEXT;
    has_issued_date BOOLEAN := FALSE;
    has_issue_date BOOLEAN := FALSE;
BEGIN
    -- Get function definition
    SELECT routine_definition INTO func_definition
    FROM information_schema.routines 
    WHERE routine_schema = 'public' 
    AND routine_name = 'upsert_leads_from_permits';
    
    IF func_definition IS NULL THEN
        RAISE EXCEPTION 'Function upsert_leads_from_permits() not found!';
    END IF;
    
    -- Check if function uses correct column name
    has_issued_date := func_definition LIKE '%issued_date%';
    has_issue_date := func_definition LIKE '%issue_date%';
    
    IF has_issued_date AND NOT has_issue_date THEN
        RAISE NOTICE '✓ SUCCESS: upsert_leads_from_permits() uses correct "issued_date" column';
        RAISE NOTICE '✓ SUCCESS: Function does NOT use incorrect "issue_date" column';
    ELSIF has_issue_date THEN
        RAISE EXCEPTION '✗ FAILED: Function contains incorrect "issue_date" reference!';
    ELSE
        RAISE EXCEPTION '✗ FAILED: Function does not reference any date column!';
    END IF;
    
    RAISE NOTICE 'Verification complete: The RPC function uses the correct date column as required.';
END;
$$;