-- =====================================================================
-- Verify County Fix: Run RPC and Check for NULLs
-- =====================================================================
-- This script runs the enhanced upsert_leads_from_permits() RPC function
-- and verifies there are no NULLs in county/name and keys are present
-- =====================================================================

\echo '=== Running RPC and Verifying No NULLs in County/Name ==='

-- Step 1: Run the RPC function
DO $$
DECLARE
    result RECORD;
BEGIN
    \echo 'Running upsert_leads_from_permits() RPC function...'
    SELECT * INTO result FROM public.upsert_leads_from_permits();
    
    RAISE NOTICE 'RPC Results - Inserted: %, Updated: %, Total Processed: %', 
        result.inserted_count, result.updated_count, result.total_processed;
END;
$$;

-- Step 2: Check for NULL county values
DO $$
DECLARE
    null_county_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO null_county_count FROM public.leads WHERE county IS NULL;
    
    IF null_county_count = 0 THEN
        RAISE NOTICE '✅ VERIFICATION PASSED: No NULL county values found';
    ELSE
        RAISE WARNING '❌ VERIFICATION FAILED: Found % NULL county values', null_county_count;
        
        -- Show some examples of NULL county records
        RAISE NOTICE 'Examples of NULL county records:';
        FOR rec IN 
            SELECT id, name, address, city, county, permit_id 
            FROM public.leads 
            WHERE county IS NULL 
            LIMIT 5
        LOOP
            RAISE NOTICE '  ID: %, Name: %, Address: %, City: %, County: %, PermitID: %',
                rec.id, rec.name, rec.address, rec.city, rec.county, rec.permit_id;
        END LOOP;
    END IF;
END;
$$;

-- Step 3: Check for NULL name values  
DO $$
DECLARE
    null_name_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO null_name_count FROM public.leads WHERE name IS NULL;
    
    IF null_name_count = 0 THEN
        RAISE NOTICE '✅ VERIFICATION PASSED: No NULL name values found';
    ELSE
        RAISE WARNING '❌ VERIFICATION FAILED: Found % NULL name values', null_name_count;
        
        -- Show some examples of NULL name records
        RAISE NOTICE 'Examples of NULL name records:';
        FOR rec IN 
            SELECT id, name, address, city, county, permit_id 
            FROM public.leads 
            WHERE name IS NULL 
            LIMIT 5
        LOOP
            RAISE NOTICE '  ID: %, Name: %, Address: %, City: %, County: %, PermitID: %',
                rec.id, rec.name, rec.address, rec.city, rec.county, rec.permit_id;
        END LOOP;
    END IF;
END;
$$;

-- Step 4: Check for missing keys (permit_id)
DO $$
DECLARE
    missing_permit_id_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO missing_permit_id_count FROM public.leads WHERE permit_id IS NULL;
    
    IF missing_permit_id_count = 0 THEN
        RAISE NOTICE '✅ VERIFICATION PASSED: All leads have permit_id keys';
    ELSE
        RAISE WARNING '❌ VERIFICATION FAILED: Found % leads without permit_id keys', missing_permit_id_count;
    END IF;
END;
$$;

-- Step 5: Show distribution of county values
DO $$
DECLARE
    county_stats TEXT;
BEGIN
    SELECT string_agg(
        county || ' (' || count || ')', 
        ', ' ORDER BY count DESC
    ) INTO county_stats
    FROM (
        SELECT 
            COALESCE(county, 'NULL') as county, 
            COUNT(*)::text as count
        FROM public.leads 
        GROUP BY county 
        ORDER BY COUNT(*) DESC
        LIMIT 10
    ) county_counts;
    
    RAISE NOTICE 'County distribution (top 10): %', COALESCE(county_stats, 'No data');
END;
$$;

-- Step 6: Show sample of recent leads to verify data quality
\echo 'Sample of recent leads (showing county and name values):'
SELECT 
    id,
    CASE 
        WHEN name IS NULL THEN '⚠️ NULL' 
        WHEN TRIM(name) = '' THEN '⚠️ EMPTY'
        ELSE LEFT(name, 40) 
    END as name_sample,
    city,
    CASE 
        WHEN county IS NULL THEN '⚠️ NULL' 
        WHEN TRIM(county) = '' THEN '⚠️ EMPTY'
        ELSE county 
    END as county_value,
    permit_id IS NOT NULL as has_permit_key,
    created_at
FROM public.leads 
ORDER BY created_at DESC 
LIMIT 10;

\echo '=== Verification Complete ===';