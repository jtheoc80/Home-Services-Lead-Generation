-- Create public.permits view for frontend Supabase queries
-- Maps gold.permits table to expected column names for compatibility
-- 
-- Expected columns: id, jurisdiction, county, permit_type, value, status, issued_date, address

-- First, ensure we have the gold schema and tables available
-- This view assumes 2025-setup.sql has been applied

-- Create the permits view that maps columns to expected names
CREATE OR REPLACE VIEW public.permits AS
SELECT 
    p.id,
    COALESCE(s.name, s.id, 'Unknown') as jurisdiction,
    p.county,
    p.permit_type,
    p.valuation as value,
    p.status,
    p.issued_at as issued_date,
    p.address
FROM gold.permits p
LEFT JOIN meta.sources s ON p.source_id = s.id
WHERE p.issued_at IS NOT NULL
ORDER BY p.issued_at DESC;

-- Add comment for documentation
COMMENT ON VIEW public.permits IS 'Unified permits view for frontend queries with standardized column names';

-- Grant read access to authenticated users
-- Note: This inherits RLS from the underlying gold.permits table
GRANT SELECT ON public.permits TO authenticated;
GRANT SELECT ON public.permits TO anon;

-- Success message
SELECT 'Public permits view created successfully!' as message;