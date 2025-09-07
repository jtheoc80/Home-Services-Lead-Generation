-- SQL backfill to update leads.zip from permits.zipcode
-- This script updates the zip field in the leads table using zipcode data from permits
-- It handles the relationship between leads and permits via the permit_id foreign key

-- Update leads.zip from permits.zipcode where the zip field is currently NULL or empty
UPDATE public.leads 
SET zip = p.zipcode,
    updated_at = NOW()
FROM public.permits p
WHERE leads.permit_id = p.id
  AND p.zipcode IS NOT NULL 
  AND p.zipcode != ''
  AND (leads.zip IS NULL OR leads.zip = '');

-- Report on the backfill results
SELECT 
  COUNT(*) as total_leads_updated,
  COUNT(DISTINCT leads.permit_id) as unique_permits_updated
FROM public.leads
INNER JOIN public.permits p ON leads.permit_id = p.id
WHERE leads.zip = p.zipcode
  AND p.zipcode IS NOT NULL 
  AND p.zipcode != '';

-- Verification: Show sample of updated leads with their zipcode data
SELECT 
  l.id as lead_id,
  l.name,
  l.zip as lead_zip,
  p.zipcode as permit_zipcode,
  l.created_at,
  l.updated_at
FROM public.leads l
INNER JOIN public.permits p ON l.permit_id = p.id
WHERE l.zip IS NOT NULL 
  AND l.zip != ''
ORDER BY l.updated_at DESC
LIMIT 10;