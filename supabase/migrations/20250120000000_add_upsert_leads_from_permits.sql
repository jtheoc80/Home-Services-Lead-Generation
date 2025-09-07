-- Create upsert_leads_from_permits RPC function
-- This function upserts leads from permits data, ensuring correct date column usage

CREATE OR REPLACE FUNCTION public.upsert_leads_from_permits()
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
      COALESCE(
        NULLIF(p.work_description,''),
        'Permit ' || COALESCE(p.permit_number, p.permit_id, p.id::text, '(no #)')
      ) as name,
      p.address,
      p.city,
      NULLIF(p.county,'') as county,
      COALESCE(NULLIF(p.permit_type,''), NULLIF(p.permit_class,''), 'Home Services') as service,
      COALESCE(NULLIF(p.permit_type,''), NULLIF(p.permit_class,'')) as trade,
      'permit_ingest' as source,
      COALESCE(NULLIF(p.status,''),'new') as status,
      p.valuation,
      75,
      COALESCE(p.issued_date, p.created_at, NOW())  -- Use correct issued_date column
    FROM public.permits p
    LEFT JOIN public.leads l ON l.permit_id = p.id
    WHERE l.permit_id IS NULL  -- Only insert if lead doesn't exist
    
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
COMMENT ON FUNCTION public.upsert_leads_from_permits() IS 
'RPC function that upserts leads from permits data. Uses public.permits.issued_date (not issue_date) for correct date handling. Returns counts of inserted, updated, and total processed records.';