-- Migration: Fix county NULL values and enhance upsert_leads_from_permits()
-- This migration addresses the problem statement:
-- 1. Add a default value 'Unknown' to public.leads.county
-- 2. Recreate upsert_leads_from_permits() to always supply county using 
--    coalesce(county, inferred-from-jurisdiction, 'Unknown')
-- 3. Ensure non-null name values

-- ================================================================================
-- STEP 1: Add default value to county column
-- ================================================================================

-- Add DEFAULT 'Unknown' to leads.county column
ALTER TABLE public.leads ALTER COLUMN county SET DEFAULT 'Unknown';

-- Update existing NULL county values to 'Unknown'
UPDATE public.leads SET county = 'Unknown' WHERE county IS NULL;

-- ================================================================================
-- STEP 2: Create jurisdiction-to-county mapping function
-- ================================================================================

-- Function to map jurisdiction slug to county name
CREATE OR REPLACE FUNCTION public.infer_county_from_jurisdiction(jurisdiction_slug TEXT)
RETURNS TEXT
LANGUAGE plpgsql
IMMUTABLE
AS $$
BEGIN
  -- Map known Texas jurisdictions to their counties
  RETURN CASE jurisdiction_slug
    WHEN 'tx-harris' THEN 'Harris County'
    WHEN 'tx-fort-bend' THEN 'Fort Bend County'
    WHEN 'tx-brazoria' THEN 'Brazoria County'
    WHEN 'tx-galveston' THEN 'Galveston County'
    WHEN 'tx-dallas' THEN 'Dallas County'
    WHEN 'tx-travis' THEN 'Travis County'
    WHEN 'tx-bexar' THEN 'Bexar County'
    ELSE NULL
  END;
END;
$$;

-- Add comment for documentation
COMMENT ON FUNCTION public.infer_county_from_jurisdiction(TEXT) IS 
'Maps jurisdiction slugs to county names. Returns NULL for unknown jurisdictions.';

-- ================================================================================
-- STEP 3: Recreate upsert_leads_from_permits() with proper county handling
-- ================================================================================

-- Drop and recreate the function with enhanced county logic
DROP FUNCTION IF EXISTS public.upsert_leads_from_permits(INTEGER);

CREATE OR REPLACE FUNCTION public.upsert_leads_from_permits(p_days INTEGER DEFAULT NULL)
RETURNS TABLE(
  inserted_count INTEGER,
  updated_count INTEGER,
  total_processed INTEGER
)
LANGUAGE plpgsql
AS $$
DECLARE
  inserted_count INTEGER := 0;
  updated_count INTEGER := 0;
  total_processed INTEGER := 0;
BEGIN
  -- Upsert leads from permits using the correct issued_date column
  -- Filter by p_days if provided to only process recent permits
  WITH upsert_results AS (
    INSERT INTO public.leads (
      permit_id, 
      external_permit_id,
      name, 
      address,
      city,
      county,
      service,
      trade, 
      source,
      status, 
      value, 
      lead_score, 
      created_at
    )
    SELECT 
      p.id,
      p.permit_id,  -- Use canonical permit_id as external_permit_id
      -- Enhanced name logic to ensure never NULL
      COALESCE(
        NULLIF(TRIM(p.work_description),''),
        NULLIF(TRIM(p.permit_type),''),
        'Permit ' || COALESCE(NULLIF(TRIM(p.permit_number),''), NULLIF(TRIM(p.permit_id),''), p.id::text, '(no #)')
      ) as name,
      p.address,
      p.city,
      -- Enhanced county logic: county -> jurisdiction-inferred -> 'Unknown'
      COALESCE(
        NULLIF(TRIM(p.county),''),
        public.infer_county_from_jurisdiction(p.jurisdiction),
        public.infer_county_from_jurisdiction(p.source),  -- fallback: try source as jurisdiction
        'Unknown'
      ) as county,
      COALESCE(NULLIF(TRIM(p.permit_type),''), NULLIF(TRIM(p.permit_class),''), 'Home Services') as service,
      COALESCE(NULLIF(TRIM(p.permit_type),''), NULLIF(TRIM(p.permit_class),'')) as trade,
      'permit_ingest' as source,
      COALESCE(NULLIF(TRIM(p.status),''),'new') as status,
      p.valuation,
      75,
      COALESCE(p.issued_date, p.created_at, NOW())  -- Use correct issued_date column
    FROM public.permits p
    WHERE 
      CASE 
        WHEN p_days IS NOT NULL THEN 
          COALESCE(p.issued_date, p.created_at, NOW()) >= NOW() - INTERVAL '1 day' * p_days
        ELSE 
          TRUE
      END
    
    ON CONFLICT (permit_id) DO UPDATE SET
      name = EXCLUDED.name,
      external_permit_id = EXCLUDED.external_permit_id,
      address = EXCLUDED.address,
      city = EXCLUDED.city,
      county = EXCLUDED.county,
      service = EXCLUDED.service,
      trade = EXCLUDED.trade,
      source = EXCLUDED.source,
      status = EXCLUDED.status,
      value = EXCLUDED.value,
      lead_score = EXCLUDED.lead_score,
      updated_at = NOW()
    RETURNING 
      CASE WHEN xmax = 0 THEN 1 ELSE 0 END as is_insert,
      CASE WHEN xmax > 0 THEN 1 ELSE 0 END as is_update
  )
  SELECT 
    SUM(is_insert)::INTEGER,
    SUM(is_update)::INTEGER,
    COUNT(*)::INTEGER
  INTO inserted_count, updated_count, total_processed
  FROM upsert_results;

  -- Return results
  RETURN QUERY SELECT inserted_count, updated_count, total_processed;
END;
$$;

-- Add comment for documentation
COMMENT ON FUNCTION public.upsert_leads_from_permits(INTEGER) IS 
'Enhanced RPC function that upserts leads from permits data with guaranteed non-NULL county and name values. 
Uses coalesce(county, inferred-from-jurisdiction, ''Unknown'') for county and enhanced fallback logic for name.
Accepts optional p_days parameter to filter permits from the last N days. 
Uses public.permits.issued_date (not issue_date) for correct date handling. 
Returns counts of inserted, updated, and total processed records.';