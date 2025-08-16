-- Auto-create leads from permits implementation
-- Creates function and trigger to automatically generate leads from new permits
-- Adds unique index on permit_id and backfills existing permits

-- Step 1: Add unique index on permit_id in leads table to prevent duplicates
CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_permit_id_unique 
ON public.leads(permit_id) 
WHERE permit_id IS NOT NULL;

-- Step 2: Create function to generate lead from permit data
CREATE OR REPLACE FUNCTION create_lead_from_permit()
RETURNS TRIGGER AS $$
DECLARE
    lead_name TEXT;
    lead_email TEXT;
    lead_phone TEXT;
    lead_address TEXT;
    lead_city TEXT;
    lead_state TEXT;
    lead_zip TEXT;
    lead_county TEXT;
    lead_service TEXT;
    lead_value NUMERIC;
    permit_id_str TEXT;
BEGIN
    -- Generate permit_id string from the permit UUID
    permit_id_str := NEW.id::TEXT;
    
    -- Extract lead information from permit data
    -- Use applicant_name as primary, fallback to owner_name, then contractor_name
    lead_name := COALESCE(
        NULLIF(trim(NEW.applicant_name), ''),
        NULLIF(trim(NEW.owner_name), ''), 
        NULLIF(trim(NEW.contractor_name), ''),
        'Unknown'
    );
    
    -- Extract email from raw_data if available
    lead_email := COALESCE(
        NEW.raw_data->>'email',
        NEW.raw_data->>'applicant_email',
        NEW.raw_data->>'owner_email'
    );
    
    -- Extract phone from raw_data if available
    lead_phone := COALESCE(
        NEW.raw_data->>'phone',
        NEW.raw_data->>'applicant_phone', 
        NEW.raw_data->>'owner_phone'
    );
    
    -- Use permit address information
    lead_address := NEW.address;
    lead_city := NEW.city;
    lead_state := 'TX'; -- Default to Texas for this system
    lead_zip := NEW.zipcode;
    lead_county := NEW.county;
    
    -- Determine service type from work description and permit type
    lead_service := CASE 
        WHEN NEW.work_description ILIKE '%hvac%' OR NEW.work_description ILIKE '%air%' OR NEW.work_description ILIKE '%heating%' OR NEW.work_description ILIKE '%cooling%' THEN 'HVAC'
        WHEN NEW.work_description ILIKE '%electrical%' OR NEW.work_description ILIKE '%electric%' THEN 'Electrical'
        WHEN NEW.work_description ILIKE '%plumbing%' OR NEW.work_description ILIKE '%plumb%' THEN 'Plumbing'
        WHEN NEW.work_description ILIKE '%roof%' THEN 'Roofing'
        WHEN NEW.work_description ILIKE '%solar%' THEN 'Solar'
        WHEN NEW.permit_type ILIKE '%building%' OR NEW.permit_type ILIKE '%residential%' THEN 'General Construction'
        ELSE 'Home Services'
    END;
    
    -- Use permit valuation as lead value
    lead_value := NEW.valuation;
    
    -- Insert lead (will be ignored if permit_id already exists due to unique constraint)
    INSERT INTO public.leads (
        name,
        email, 
        phone,
        address,
        city,
        state,
        zip,
        county,
        service,
        source,
        status,
        permit_id,
        value,
        created_at,
        metadata
    ) VALUES (
        lead_name,
        lead_email,
        lead_phone, 
        lead_address,
        lead_city,
        lead_state,
        lead_zip,
        lead_county,
        lead_service,
        'permit_ingest',
        'new',
        permit_id_str,
        lead_value,
        COALESCE(NEW.issued_date, NEW.created_at, NOW()),
        jsonb_build_object(
            'permit_source', NEW.source,
            'permit_number', NEW.permit_number,
            'permit_type', NEW.permit_type,
            'permit_class', NEW.permit_class,
            'work_description', NEW.work_description,
            'contractor_name', NEW.contractor_name,
            'auto_generated', true,
            'generated_at', NOW()
        )
    )
    ON CONFLICT (permit_id) DO NOTHING; -- Ignore if permit already has a lead
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 3: Create trigger to automatically create leads from new permits
DROP TRIGGER IF EXISTS trg_lead_from_permit ON public.permits;
CREATE TRIGGER trg_lead_from_permit
    AFTER INSERT ON public.permits
    FOR EACH ROW
    EXECUTE FUNCTION create_lead_from_permit();

-- Step 4: Backfill existing permits into leads (insert missing only)
-- This will create leads for all existing permits that don't already have leads
INSERT INTO public.leads (
    name,
    email,
    phone,
    address,
    city,
    state,
    zip,
    county,
    service,
    source,
    status,
    permit_id,
    value,
    created_at,
    metadata
)
SELECT DISTINCT
    -- Extract lead name (prefer applicant, fallback to owner, then contractor)
    COALESCE(
        NULLIF(trim(p.applicant_name), ''),
        NULLIF(trim(p.owner_name), ''), 
        NULLIF(trim(p.contractor_name), ''),
        'Unknown'
    ) as name,
    
    -- Extract email from raw_data if available
    COALESCE(
        p.raw_data->>'email',
        p.raw_data->>'applicant_email',
        p.raw_data->>'owner_email'
    ) as email,
    
    -- Extract phone from raw_data if available  
    COALESCE(
        p.raw_data->>'phone',
        p.raw_data->>'applicant_phone',
        p.raw_data->>'owner_phone'
    ) as phone,
    
    -- Address information
    p.address,
    p.city,
    'TX' as state,
    p.zipcode as zip,
    p.county,
    
    -- Determine service type from work description
    CASE 
        WHEN p.work_description ILIKE '%hvac%' OR p.work_description ILIKE '%air%' OR p.work_description ILIKE '%heating%' OR p.work_description ILIKE '%cooling%' THEN 'HVAC'
        WHEN p.work_description ILIKE '%electrical%' OR p.work_description ILIKE '%electric%' THEN 'Electrical'
        WHEN p.work_description ILIKE '%plumbing%' OR p.work_description ILIKE '%plumb%' THEN 'Plumbing'
        WHEN p.work_description ILIKE '%roof%' THEN 'Roofing'
        WHEN p.work_description ILIKE '%solar%' THEN 'Solar'
        WHEN p.permit_type ILIKE '%building%' OR p.permit_type ILIKE '%residential%' THEN 'General Construction'
        ELSE 'Home Services'
    END as service,
    
    'permit_backfill' as source,
    'new' as status,
    p.id::TEXT as permit_id,
    p.valuation as value,
    COALESCE(p.issued_date, p.created_at, NOW()) as created_at,
    
    -- Store permit metadata
    jsonb_build_object(
        'permit_source', p.source,
        'permit_number', p.permit_number,
        'permit_type', p.permit_type,
        'permit_class', p.permit_class,
        'work_description', p.work_description,
        'contractor_name', p.contractor_name,
        'backfilled', true,
        'backfilled_at', NOW()
    ) as metadata

FROM public.permits p
LEFT JOIN public.leads l ON l.permit_id = p.id::TEXT
WHERE l.permit_id IS NULL  -- Only insert permits that don't already have leads
  AND p.id IS NOT NULL;   -- Ensure permit has valid ID

-- Create index to improve performance of permit_id lookups
CREATE INDEX IF NOT EXISTS idx_leads_permit_id ON public.leads(permit_id);

-- Add comments for documentation
COMMENT ON FUNCTION create_lead_from_permit() IS 'Automatically creates a lead record when a new permit is inserted';
COMMENT ON TRIGGER trg_lead_from_permit ON public.permits IS 'Trigger to auto-create leads from new permits';

-- Verify the setup
SELECT 
    'Permits to leads setup completed successfully!' as message,
    'Function: create_lead_from_permit()' as function_created,
    'Trigger: trg_lead_from_permit on public.permits' as trigger_created,
    'Unique index: idx_leads_permit_id_unique' as index_created,
    COUNT(*) as permits_backfilled
FROM public.leads 
WHERE source IN ('permit_ingest', 'permit_backfill');