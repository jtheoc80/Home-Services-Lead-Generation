-- Verification query to select newest rows from public.leads
-- This query shows the most recently created/updated leads with their zipcode data

-- Show the 20 newest leads by created_at with zipcode information
SELECT 
  l.id,
  l.created_at,
  l.updated_at,
  l.name,
  l.email,
  l.phone,
  l.address,
  l.city,
  l.zip,
  l.county,
  l.service,
  l.source,
  l.status,
  l.value,
  l.permit_id,
  p.zipcode as permit_zipcode,
  CASE 
    WHEN l.zip = p.zipcode THEN 'MATCH'
    WHEN l.zip IS NULL AND p.zipcode IS NOT NULL THEN 'LEAD_MISSING'
    WHEN l.zip IS NOT NULL AND p.zipcode IS NULL THEN 'PERMIT_MISSING'
    WHEN l.zip != p.zipcode THEN 'MISMATCH'
    ELSE 'BOTH_NULL'
  END as zipcode_status
FROM public.leads l
LEFT JOIN public.permits p ON l.permit_id = p.id
ORDER BY l.created_at DESC
LIMIT 20;

-- Summary statistics of zipcode coverage
SELECT 
  COUNT(*) as total_leads,
  COUNT(l.zip) as leads_with_zip,
  COUNT(p.zipcode) as permits_with_zipcode,
  COUNT(CASE WHEN l.zip = p.zipcode THEN 1 END) as matching_zipcodes,
  COUNT(CASE WHEN l.zip IS NULL AND p.zipcode IS NOT NULL THEN 1 END) as leads_missing_zip,
  ROUND(
    COUNT(l.zip) * 100.0 / COUNT(*), 2
  ) as zip_coverage_percentage
FROM public.leads l
LEFT JOIN public.permits p ON l.permit_id = p.id;

-- Show leads created in the last 7 days with zipcode data
SELECT 
  DATE(l.created_at) as date_created,
  COUNT(*) as leads_created,
  COUNT(l.zip) as leads_with_zip,
  ROUND(COUNT(l.zip) * 100.0 / COUNT(*), 2) as zip_coverage_pct
FROM public.leads l
WHERE l.created_at >= NOW() - INTERVAL '7 days'
GROUP BY DATE(l.created_at)
ORDER BY date_created DESC;