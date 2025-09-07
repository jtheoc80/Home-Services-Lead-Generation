-- Fix public_leads view "cannot change name of view column" error
-- Drop and recreate the view with correct schema from public.leads table
--
-- NOTE: This changes the view schema from the previous version that selected
-- from public.permits to now selecting from public.leads with different columns.
-- Previous columns: id, source_record_id, created_at (from permits)
-- New columns: source, external_permit_id, trade, address, zipcode, status, created_at, updated_at (from leads)

-- Drop the existing view to avoid column name conflicts
DROP VIEW IF EXISTS public.public_leads;

-- Create the view with the required columns from public.leads table
CREATE VIEW public.public_leads AS
SELECT 
    source,
    external_permit_id,
    trade,
    address,
    zip AS zipcode,  -- Map zip column to zipcode for compatibility
    status,
    created_at,
    updated_at
FROM public.leads;

-- Grant permissions
GRANT SELECT ON public.public_leads TO anon, authenticated;

-- Add comment for documentation
COMMENT ON VIEW public.public_leads IS 'Public read-only view of leads data with selected columns for external access. Note: Schema changed from permits-based to leads-based data.';