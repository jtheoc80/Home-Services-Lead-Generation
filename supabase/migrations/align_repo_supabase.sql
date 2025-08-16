-- =====================================================================
-- Supabase Schema Alignment Migration
-- =====================================================================
-- Goals:
-- - Standardize identifiers: canonical permit_id (text) + (source, permit_id) uniqueness
-- - Keep existing UUID permits.id and leads.permit_id (UUID FK) working  
-- - Add missing fields used by docs/pipeline
-- - Normalize date/name/value names; provide compatibility views
-- - Upgrade upsert_permit(jsonb) RPC to fill permit_id from incoming payload
-- - Refresh AFTER INSERT trigger to auto-create leads from permits
-- - Supply safe indexes & optional PostGIS for geospatial

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =====================================================================
-- PHASE 1: Enhance permits table schema
-- =====================================================================

-- Add new columns to public.permits table
DO $$ 
BEGIN
    -- Add permit_id as canonical text identifier
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' AND table_name = 'permits' AND column_name = 'permit_id') THEN
        ALTER TABLE public.permits ADD COLUMN permit_id TEXT;
    END IF;
    
    -- Add missing fields used by docs/pipeline
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' AND table_name = 'permits' AND column_name = 'applicant') THEN
        ALTER TABLE public.permits ADD COLUMN applicant TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' AND table_name = 'permits' AND column_name = 'owner') THEN
        ALTER TABLE public.permits ADD COLUMN owner TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' AND table_name = 'permits' AND column_name = 'work_class') THEN
        ALTER TABLE public.permits ADD COLUMN work_class TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' AND table_name = 'permits' AND column_name = 'provenance') THEN
        ALTER TABLE public.permits ADD COLUMN provenance JSONB DEFAULT '{}'::jsonb;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' AND table_name = 'permits' AND column_name = 'finaled_at') THEN
        ALTER TABLE public.permits ADD COLUMN finaled_at TIMESTAMPTZ;
    END IF;
    
    -- Note: geom already exists in current schema from PostGIS setup
END $$;

-- Backfill permit_id from existing data
UPDATE public.permits 
SET permit_id = COALESCE(
    NULLIF(trim(permit_number), ''),
    id::text
)
WHERE permit_id IS NULL;

-- Backfill other fields from existing columns for consistency
UPDATE public.permits 
SET 
    applicant = COALESCE(applicant, applicant_name),
    owner = COALESCE(owner, owner_name)
WHERE applicant IS NULL OR owner IS NULL;

-- Add created_at if missing (should exist from current schema but verify)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' AND table_name = 'permits' AND column_name = 'created_at') THEN
        ALTER TABLE public.permits ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW();
    END IF;
END $$;

-- =====================================================================
-- PHASE 2: Add unique constraints and indexes
-- =====================================================================

-- Drop existing constraint temporarily if we're changing it
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.table_constraints 
               WHERE constraint_name = 'permits_source_source_record_id_key' 
               AND table_name = 'permits' AND table_schema = 'public') THEN
        -- Keep existing unique constraint on (source, source_record_id)
        NULL;
    END IF;
END $$;

-- Add partial unique constraint on (source, permit_id) when permit_id is not null
DROP INDEX IF EXISTS uq_permits_source_permit_id;
CREATE UNIQUE INDEX uq_permits_source_permit_id 
ON public.permits(source, permit_id) 
WHERE permit_id IS NOT NULL;

-- Add helpful indexes for the new fields
CREATE INDEX IF NOT EXISTS idx_permits_permit_id ON public.permits(permit_id);
CREATE INDEX IF NOT EXISTS idx_permits_applicant ON public.permits(applicant);
CREATE INDEX IF NOT EXISTS idx_permits_owner ON public.permits(owner);
CREATE INDEX IF NOT EXISTS idx_permits_work_class ON public.permits(work_class);
CREATE INDEX IF NOT EXISTS idx_permits_finaled_at ON public.permits(finaled_at);

-- =====================================================================
-- PHASE 3: Enhance leads table schema  
-- =====================================================================

-- Add service column to leads table and sync with trade
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'service') THEN
        ALTER TABLE public.leads ADD COLUMN service TEXT;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'trade') THEN
        ALTER TABLE public.leads ADD COLUMN trade TEXT;
    END IF;
    
    -- Ensure created_at exists
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_schema = 'public' AND table_name = 'leads' AND column_name = 'created_at') THEN
        ALTER TABLE public.leads ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW();
    END IF;
END $$;

-- Backfill service from trade if trade exists but service doesn't
UPDATE public.leads 
SET service = trade 
WHERE service IS NULL AND trade IS NOT NULL;

-- Backfill trade from service if service exists but trade doesn't  
UPDATE public.leads 
SET trade = service 
WHERE trade IS NULL AND service IS NOT NULL;

-- =====================================================================
-- PHASE 4: Create compatibility views
-- =====================================================================

-- Compatibility view for permits with column aliases
CREATE OR REPLACE VIEW public.permits_compat AS
SELECT 
    id,
    source,
    source_record_id,
    permit_id,
    permit_number,
    issued_date AS issue_date,  -- Alias: issue_date → issued_date
    application_date,
    expiration_date,
    permit_type,
    permit_class,
    work_description,
    address,
    city,
    county,
    zipcode AS postal_code,     -- Alias: postal_code → zipcode  
    latitude,
    longitude,
    geom,
    valuation AS value,         -- Alias: valuation → value
    square_feet,
    applicant_name,
    contractor_name,
    owner_name,
    applicant,
    owner,
    work_class,
    status,
    raw_data,
    provenance,
    finaled_at,
    created_at,
    updated_at
FROM public.permits;

-- Compatibility view for leads to expose trade as service
CREATE OR REPLACE VIEW public.leads_compat AS
SELECT 
    id,
    created_at,
    updated_at,
    name,
    email,
    phone,
    address,
    city,
    state,
    zip,
    county,
    COALESCE(service, trade) AS service,  -- Prefer service, fallback to trade
    COALESCE(trade, service) AS trade,    -- Prefer trade, fallback to service
    source,
    status,
    metadata,
    lead_score,
    score_label,
    value,
    permit_id,
    county_population,
    user_id
FROM public.leads;

-- =====================================================================
-- PHASE 5: Update upsert_permit RPC function
-- =====================================================================

CREATE OR REPLACE FUNCTION public.upsert_permit(p JSONB)
RETURNS TABLE(id UUID, action TEXT) AS $$
DECLARE
  permit_id_val UUID;
  permit_action TEXT;
  source_val TEXT;
  source_record_id_val TEXT;
  canonical_permit_id TEXT;
BEGIN
  -- Extract required fields from parameter 'p'
  source_val := p->>'source';
  source_record_id_val := p->>'source_record_id';
  
  -- Derive canonical permit_id from payload
  canonical_permit_id := COALESCE(
      NULLIF(trim(p->>'permit_id'), ''),
      NULLIF(trim(p->>'permit_no'), ''),
      NULLIF(trim(p->>'source_record_id'), '')
  );
  
  -- Validate required fields
  IF source_val IS NULL OR source_record_id_val IS NULL THEN
    RAISE EXCEPTION 'source and source_record_id are required fields';
  END IF;

  -- Attempt to update existing record by (source, source_record_id)
  UPDATE public.permits SET
    permit_id = canonical_permit_id,
    permit_number = p->>'permit_number',
    issued_date = CASE 
      WHEN p->>'issued_date' IS NOT NULL 
      THEN (p->>'issued_date')::TIMESTAMPTZ 
      ELSE NULL 
    END,
    application_date = CASE 
      WHEN p->>'application_date' IS NOT NULL 
      THEN (p->>'application_date')::TIMESTAMPTZ 
      ELSE NULL 
    END,
    expiration_date = CASE 
      WHEN p->>'expiration_date' IS NOT NULL 
      THEN (p->>'expiration_date')::TIMESTAMPTZ 
      ELSE NULL 
    END,
    permit_type = p->>'permit_type',
    permit_class = p->>'permit_class',
    work_description = p->>'work_description',
    address = p->>'address',
    city = p->>'city',
    county = p->>'county',
    zipcode = p->>'zipcode',
    latitude = CASE 
      WHEN p->>'latitude' IS NOT NULL 
      THEN (p->>'latitude')::NUMERIC 
      ELSE NULL 
    END,
    longitude = CASE 
      WHEN p->>'longitude' IS NOT NULL 
      THEN (p->>'longitude')::NUMERIC 
      ELSE NULL 
    END,
    valuation = CASE 
      WHEN p->>'valuation' IS NOT NULL 
      THEN (p->>'valuation')::NUMERIC 
      WHEN p->>'value' IS NOT NULL 
      THEN (p->>'value')::NUMERIC 
      ELSE NULL 
    END,
    square_feet = CASE 
      WHEN p->>'square_feet' IS NOT NULL 
      THEN (p->>'square_feet')::INTEGER 
      ELSE NULL 
    END,
    applicant_name = p->>'applicant_name',
    applicant = COALESCE(p->>'applicant', p->>'applicant_name'),
    contractor_name = p->>'contractor_name',
    owner_name = p->>'owner_name',
    owner = COALESCE(p->>'owner', p->>'owner_name'),
    work_class = p->>'work_class',
    status = p->>'status',
    raw_data = p,
    updated_at = NOW()
  WHERE source = source_val AND source_record_id = source_record_id_val
  RETURNING public.permits.id INTO permit_id_val;
  
  -- If update affected a row, return it
  IF permit_id_val IS NOT NULL THEN
    permit_action := 'updated';
    RETURN QUERY SELECT permit_id_val, permit_action;
    RETURN;
  END IF;
  
  -- Otherwise, insert new record
  INSERT INTO public.permits (
    source,
    source_record_id,
    permit_id,
    permit_number,
    issued_date,
    application_date,
    expiration_date,
    permit_type,
    permit_class,
    work_description,
    address,
    city,
    county,
    zipcode,
    latitude,
    longitude,
    valuation,
    square_feet,
    applicant_name,
    applicant,
    contractor_name,
    owner_name,
    owner,
    work_class,
    status,
    raw_data,
    created_at,
    updated_at
  ) VALUES (
    source_val,
    source_record_id_val,
    canonical_permit_id,
    p->>'permit_number',
    CASE 
      WHEN p->>'issued_date' IS NOT NULL 
      THEN (p->>'issued_date')::TIMESTAMPTZ 
      ELSE NULL 
    END,
    CASE 
      WHEN p->>'application_date' IS NOT NULL 
      THEN (p->>'application_date')::TIMESTAMPTZ 
      ELSE NULL 
    END,
    CASE 
      WHEN p->>'expiration_date' IS NOT NULL 
      THEN (p->>'expiration_date')::TIMESTAMPTZ 
      ELSE NULL 
    END,
    p->>'permit_type',
    p->>'permit_class',
    p->>'work_description',
    p->>'address',
    p->>'city',
    p->>'county',
    p->>'zipcode',
    CASE 
      WHEN p->>'latitude' IS NOT NULL 
      THEN (p->>'latitude')::NUMERIC 
      ELSE NULL 
    END,
    CASE 
      WHEN p->>'longitude' IS NOT NULL 
      THEN (p->>'longitude')::NUMERIC 
      ELSE NULL 
    END,
    CASE 
      WHEN p->>'valuation' IS NOT NULL 
      THEN (p->>'valuation')::NUMERIC 
      WHEN p->>'value' IS NOT NULL 
      THEN (p->>'value')::NUMERIC 
      ELSE NULL 
    END,
    CASE 
      WHEN p->>'square_feet' IS NOT NULL 
      THEN (p->>'square_feet')::INTEGER 
      ELSE NULL 
    END,
    p->>'applicant_name',
    COALESCE(p->>'applicant', p->>'applicant_name'),
    p->>'contractor_name',
    p->>'owner_name',
    COALESCE(p->>'owner', p->>'owner_name'),
    p->>'work_class',
    p->>'status',
    p,
    COALESCE((p->>'created_at')::TIMESTAMPTZ, NOW()),
    NOW()
  ) RETURNING public.permits.id INTO permit_id_val;
  
  permit_action := 'inserted';
  RETURN QUERY SELECT permit_id_val, permit_action;
END;
$$ LANGUAGE plpgsql;

-- Update function comment
COMMENT ON FUNCTION public.upsert_permit(JSONB) IS 'Enhanced upsert function that derives permit_id from payload (permit_id, permit_no, or source_record_id)';

-- =====================================================================
-- PHASE 6: Refresh permit→lead pipeline  
-- =====================================================================

-- Create enhanced lead generation function using consistent fields
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
    lead_trade TEXT;
    lead_value NUMERIC;
    permit_id_str TEXT;
BEGIN
    -- Use consistent permit_id (prefer canonical permit_id, fallback to UUID)
    permit_id_str := COALESCE(NEW.permit_id, NEW.id::TEXT);
    
    -- Extract lead information using enhanced field mapping
    -- Priority: applicant → owner → contractor_name → 'Unknown'
    lead_name := COALESCE(
        NULLIF(trim(NEW.applicant), ''),
        NULLIF(trim(NEW.applicant_name), ''),
        NULLIF(trim(NEW.owner), ''), 
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
    
    -- Enhanced service categorization from work description and permit type
    lead_service := CASE 
        WHEN NEW.work_description ILIKE '%hvac%' OR NEW.work_description ILIKE '%air%' OR NEW.work_description ILIKE '%heating%' OR NEW.work_description ILIKE '%cooling%' THEN 'HVAC'
        WHEN NEW.work_description ILIKE '%electrical%' OR NEW.work_description ILIKE '%electric%' THEN 'Electrical'
        WHEN NEW.work_description ILIKE '%plumbing%' OR NEW.work_description ILIKE '%plumb%' THEN 'Plumbing'
        WHEN NEW.work_description ILIKE '%roof%' THEN 'Roofing'
        WHEN NEW.work_description ILIKE '%solar%' THEN 'Solar'
        WHEN NEW.permit_type ILIKE '%building%' OR NEW.permit_type ILIKE '%residential%' THEN 'General Construction'
        WHEN NEW.work_class IS NOT NULL THEN NEW.work_class
        ELSE 'Home Services'
    END;
    
    -- Keep trade and service in sync
    lead_trade := lead_service;
    
    -- Use permit valuation as lead value
    lead_value := NEW.valuation;
    
    -- Insert lead with enhanced metadata
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
        trade,
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
        lead_trade,
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
            'work_class', NEW.work_class,
            'contractor_name', NEW.contractor_name,
            'applicant', NEW.applicant,
            'owner', NEW.owner,
            'canonical_permit_id', NEW.permit_id,
            'auto_generated', true,
            'generated_at', NOW(),
            'migration_version', 'align_repo_supabase'
        )
    )
    ON CONFLICT (permit_id) DO NOTHING; -- Ignore if permit already has a lead
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Update trigger 
DROP TRIGGER IF EXISTS trg_lead_from_permit ON public.permits;
CREATE TRIGGER trg_lead_from_permit
    AFTER INSERT ON public.permits
    FOR EACH ROW
    EXECUTE FUNCTION create_lead_from_permit();

-- Update function comments
COMMENT ON FUNCTION create_lead_from_permit() IS 'Enhanced function to create leads from permits using canonical permit_id and improved field mapping';
COMMENT ON TRIGGER trg_lead_from_permit ON public.permits IS 'Enhanced trigger to auto-create leads from new permits with canonical identifiers';

-- =====================================================================
-- PHASE 7: Backfill and validation
-- =====================================================================

-- Ensure all existing permits have canonical permit_id
UPDATE public.permits 
SET permit_id = id::text 
WHERE permit_id IS NULL;

-- Update existing leads to use canonical permit_id where possible
UPDATE public.leads l
SET permit_id = p.permit_id
FROM public.permits p 
WHERE l.permit_id = p.id::text 
  AND p.permit_id IS NOT NULL 
  AND p.permit_id != p.id::text;

-- Add helpful comments to new columns
COMMENT ON COLUMN public.permits.permit_id IS 'Canonical permit identifier derived from permit_no, source_record_id, or UUID';
COMMENT ON COLUMN public.permits.applicant IS 'Permit applicant (normalized from applicant_name)';
COMMENT ON COLUMN public.permits.owner IS 'Property owner (normalized from owner_name)';
COMMENT ON COLUMN public.permits.work_class IS 'Work classification for permit categorization';
COMMENT ON COLUMN public.permits.provenance IS 'Data lineage and source metadata';
COMMENT ON COLUMN public.permits.finaled_at IS 'Timestamp when permit was finalized/completed';

COMMENT ON COLUMN public.leads.service IS 'Service category (synced with trade column)';
COMMENT ON COLUMN public.leads.trade IS 'Trade classification (synced with service column)';

-- =====================================================================
-- PHASE 8: Final verification and success message
-- =====================================================================

-- Verify the setup with a comprehensive check
DO $$
DECLARE
    permits_count INTEGER;
    leads_count INTEGER;
    permit_id_count INTEGER;
    unique_services_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO permits_count FROM public.permits;
    SELECT COUNT(*) INTO leads_count FROM public.leads;
    SELECT COUNT(*) INTO permit_id_count FROM public.permits WHERE permit_id IS NOT NULL;
    SELECT COUNT(DISTINCT service) INTO unique_services_count FROM public.leads WHERE service IS NOT NULL;
    
    RAISE NOTICE 'Supabase schema alignment completed successfully!';
    RAISE NOTICE 'Permits table: % records, % with permit_id', permits_count, permit_id_count;
    RAISE NOTICE 'Leads table: % records with % unique services', leads_count, unique_services_count;
    RAISE NOTICE 'Enhanced upsert_permit() function ready for canonical permit_id derivation';
    RAISE NOTICE 'Compatibility views created: permits_compat, leads_compat';
    RAISE NOTICE 'Enhanced permit→lead pipeline with improved field mapping';
END $$;

-- Final success message
SELECT 
    'Schema alignment migration completed successfully!' as status,
    'Enhanced permit_id derivation' as enhancement_1,
    'Canonical (source, permit_id) uniqueness' as enhancement_2,
    'Compatibility views for old column names' as enhancement_3,
    'Improved permit→lead pipeline' as enhancement_4,
    'Ready for sentinel test' as next_step;