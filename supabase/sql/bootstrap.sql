-- ================================================================================
-- Supabase Bootstrap SQL for Home Services Lead Generation
-- ================================================================================
-- 
-- This script creates the complete permits → leads pipeline infrastructure:
-- - Creates permits and leads tables if they don't exist
-- - Adds unique indexes on external source IDs to prevent duplicates
-- - Creates trigger function to canonicalize incoming permit IDs
-- - Inserts normalized lead records automatically
-- - Adds RLS policies for read-only anon access and service role full access
--
-- Usage:
--   psql -h <host> -U postgres -d <database> -f bootstrap.sql
--   or copy/paste into Supabase SQL Editor
--
-- Prerequisites: 
--   - SUPABASE_URL environment variable
--   - SUPABASE_SERVICE_ROLE_KEY environment variable
--
-- ================================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "postgis";

-- ================================================================================
-- PERMITS TABLE
-- ================================================================================

-- Create public.permits table for TX permit ingestion
CREATE TABLE IF NOT EXISTS public.permits (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Source identification with unique constraint
  source TEXT NOT NULL, -- 'austin', 'houston', 'dallas'
  source_record_id TEXT NOT NULL, -- Original record ID from source
  
  -- Canonical permit identifier (derived from permit_number, permit_no, source_record_id, or id)
  permit_id TEXT,
  
  -- Core permit information
  permit_number TEXT,
  issued_date TIMESTAMPTZ,
  application_date TIMESTAMPTZ,
  expiration_date TIMESTAMPTZ,
  finaled_at TIMESTAMPTZ,
  
  -- Work and permit classification
  permit_type TEXT,
  permit_class TEXT,
  work_description TEXT,
  work_class TEXT,
  
  -- Location information
  address TEXT,
  city TEXT,
  county TEXT,
  zipcode TEXT,
  latitude NUMERIC,
  longitude NUMERIC,
  geom GEOMETRY(POINT, 4326), -- PostGIS geometry column
  
  -- Financial details
  valuation NUMERIC,
  square_feet INTEGER,
  
  -- People and entities (canonical names)
  applicant TEXT,
  applicant_name TEXT,
  contractor_name TEXT,
  owner TEXT,
  owner_name TEXT,
  
  -- Status and metadata
  status TEXT,
  raw_data JSONB,
  provenance JSONB, -- Track data lineage and transformations
  record_hash TEXT, -- MD5 hash of key attributes for change detection
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ================================================================================
-- LEADS TABLE
-- ================================================================================

-- Create public.leads table
CREATE TABLE IF NOT EXISTS public.leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    created_at TIMESTAMPTZ DEFAULT now(),
    updated_at TIMESTAMPTZ DEFAULT now(),
    
    -- Lead identification and contact
    name TEXT,
    email TEXT,
    phone TEXT,
    
    -- Address information
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    county TEXT,
    
    -- Service and business details
    service TEXT,
    trade TEXT,
    source TEXT,
    status TEXT DEFAULT 'new',
    value NUMERIC,
    
    -- Scoring and quality
    lead_score INTEGER,
    score_label TEXT,
    
    -- Permit relationship
    permit_id UUID, -- FK to permits.id
    external_permit_id TEXT, -- Canonical permit identifier for external tracking
    
    -- Demographics and metadata
    county_population INTEGER,
    metadata JSONB,
    
    -- User association for RLS
    user_id UUID REFERENCES auth.users(id)
);

-- ================================================================================
-- UNIQUE INDEXES FOR DUPLICATE PREVENTION
-- ================================================================================

-- Prevent duplicate permits from same source
CREATE UNIQUE INDEX IF NOT EXISTS uq_permits_source_record_id
  ON public.permits (source, source_record_id)
  WHERE source_record_id IS NOT NULL;

-- Prevent duplicate permits with same canonical permit_id from same source
CREATE UNIQUE INDEX IF NOT EXISTS uq_permits_source_permit_id
  ON public.permits (source, permit_id)
  WHERE permit_id IS NOT NULL;

-- Prevent duplicate leads per permit (using UUID FK)
CREATE UNIQUE INDEX IF NOT EXISTS leads_permit_unique
  ON public.leads (permit_id)
  WHERE permit_id IS NOT NULL;

-- Prevent duplicate leads per external permit ID
CREATE UNIQUE INDEX IF NOT EXISTS uq_leads_external_permit_id
  ON public.leads (external_permit_id)
  WHERE external_permit_id IS NOT NULL;

-- ================================================================================
-- PERFORMANCE INDEXES
-- ================================================================================

-- Permits indexes
CREATE INDEX IF NOT EXISTS permits_issued_idx ON public.permits (issued_date DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS permits_created_idx ON public.permits (created_at DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_permits_source ON public.permits(source);
CREATE INDEX IF NOT EXISTS idx_permits_city ON public.permits(city);
CREATE INDEX IF NOT EXISTS idx_permits_county ON public.permits(county);
CREATE INDEX IF NOT EXISTS idx_permits_valuation ON public.permits(valuation);
CREATE INDEX IF NOT EXISTS idx_permits_status ON public.permits(status);
CREATE INDEX IF NOT EXISTS idx_permits_geom ON public.permits USING GIST(geom);

-- Leads indexes
CREATE INDEX IF NOT EXISTS idx_leads_lead_score ON public.leads(lead_score);
CREATE INDEX IF NOT EXISTS idx_leads_value ON public.leads(value);
CREATE INDEX IF NOT EXISTS idx_leads_permit_id ON public.leads(permit_id);
CREATE INDEX IF NOT EXISTS idx_leads_external_permit_id ON public.leads(external_permit_id);
CREATE INDEX IF NOT EXISTS idx_leads_user_id ON public.leads(user_id);
CREATE INDEX IF NOT EXISTS idx_leads_county ON public.leads(county);
CREATE INDEX IF NOT EXISTS idx_leads_service ON public.leads(service);
CREATE INDEX IF NOT EXISTS idx_leads_updated_at ON public.leads(updated_at);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON public.leads(created_at DESC);

-- ================================================================================
-- UTILITY FUNCTIONS
-- ================================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Function to update geometry from lat/lng coordinates
CREATE OR REPLACE FUNCTION update_permits_geom_from_coordinates()
RETURNS TRIGGER AS $$
BEGIN
  IF NEW.latitude IS NOT NULL AND NEW.longitude IS NOT NULL THEN
    NEW.geom := ST_SetSRID(ST_MakePoint(NEW.longitude, NEW.latitude), 4326);
  END IF;
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ================================================================================
-- CANONICAL PERMIT ID RESOLUTION AND LEAD CREATION TRIGGER
-- ================================================================================

-- Function to canonicalize permit IDs and create leads
CREATE OR REPLACE FUNCTION public.create_lead_from_permit()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
  v_name TEXT;
  v_trade TEXT;
  v_service TEXT;
  v_canonical_permit_id TEXT;
  v_metadata JSONB;
BEGIN
  -- Canonical identifier resolution (order of precedence)
  v_canonical_permit_id := COALESCE(
    NULLIF(NEW.permit_id, ''),
    NULLIF(NEW.permit_number, ''),
    NULLIF(NEW.source_record_id, ''),
    NEW.id::TEXT
  );
  
  -- Update permit_id if it was null
  IF NEW.permit_id IS NULL OR NEW.permit_id = '' THEN
    NEW.permit_id := v_canonical_permit_id;
  END IF;
  
  -- Name extraction priority: applicant > owner > contractor_name > 'Unknown'
  v_name := COALESCE(
    NULLIF(NEW.applicant, ''),
    NULLIF(NEW.applicant_name, ''),
    NULLIF(NEW.owner, ''),
    NULLIF(NEW.owner_name, ''),
    NULLIF(NEW.contractor_name, ''),
    'Unknown'
  );
  
  -- Service/Trade classification from work description and permit type
  v_service := CASE 
    WHEN NEW.work_description ILIKE '%hvac%' OR NEW.work_description ILIKE '%air%' OR 
         NEW.work_description ILIKE '%heating%' OR NEW.work_description ILIKE '%cooling%' THEN 'HVAC'
    WHEN NEW.work_description ILIKE '%electrical%' OR NEW.work_description ILIKE '%electric%' THEN 'Electrical'
    WHEN NEW.work_description ILIKE '%plumbing%' OR NEW.work_description ILIKE '%plumb%' THEN 'Plumbing'
    WHEN NEW.work_description ILIKE '%roof%' THEN 'Roofing'
    WHEN NEW.work_description ILIKE '%solar%' THEN 'Solar'
    WHEN NEW.work_description ILIKE '%paint%' THEN 'Painting'
    WHEN NEW.work_description ILIKE '%flooring%' OR NEW.work_description ILIKE '%floor%' THEN 'Flooring'
    WHEN NEW.work_description ILIKE '%window%' OR NEW.work_description ILIKE '%door%' THEN 'Windows & Doors'
    WHEN NEW.permit_type ILIKE '%building%' OR NEW.permit_type ILIKE '%residential%' THEN 'General Construction'
    ELSE 'Home Services'
  END;
  
  v_trade := COALESCE(
    NULLIF(NEW.permit_type, ''), 
    NULLIF(NEW.permit_class, ''),
    NULLIF(NEW.work_class, ''),
    v_service
  );
  
  -- Build enriched metadata
  v_metadata := jsonb_build_object(
    'canonical_permit_id', v_canonical_permit_id,
    'permit_uuid', NEW.id,
    'source', NEW.source,
    'jurisdiction', NEW.source,
    'work_class', NEW.work_class,
    'permit_type', NEW.permit_type,
    'permit_number', NEW.permit_number,
    'work_description', NEW.work_description,
    'contractor_name', NEW.contractor_name,
    'auto_generated', true,
    'generated_at', NOW()
  );
  
  -- Merge with existing raw_data if it exists
  IF NEW.raw_data IS NOT NULL THEN
    v_metadata := v_metadata || NEW.raw_data;
  END IF;

  -- Insert lead with canonical permit ID and enriched metadata
  INSERT INTO public.leads (
    permit_id, 
    external_permit_id,
    name, 
    service,
    trade, 
    address,
    city,
    state,
    zip,
    county, 
    status, 
    value, 
    lead_score, 
    created_at,
    source,
    metadata
  )
  VALUES (
    NEW.id, -- UUID FK to permits.id
    v_canonical_permit_id, -- Canonical external permit ID
    v_name,
    v_service,
    v_trade,
    NEW.address,
    NEW.city,
    COALESCE(NEW.raw_data->>'state', 'TX'), -- Default to TX
    NEW.zipcode,
    NEW.county,
    COALESCE(NULLIF(NEW.status, ''), 'New'),
    NEW.valuation,
    75, -- Default lead score
    COALESCE(NEW.issued_date, NEW.application_date, NOW()),
    'permit_ingest',
    v_metadata
  )
  ON CONFLICT (permit_id) DO NOTHING; -- Prevent duplicates
  
  RETURN NEW;
END;
$$;

-- ================================================================================
-- TRIGGERS
-- ================================================================================

-- Trigger to auto-update updated_at on permits
DROP TRIGGER IF EXISTS set_updated_at ON public.permits;
CREATE TRIGGER set_updated_at
  BEFORE UPDATE ON public.permits
  FOR EACH ROW
  EXECUTE FUNCTION update_updated_at_column();

-- Trigger to auto-update updated_at on leads
DROP TRIGGER IF EXISTS update_leads_updated_at ON public.leads;
CREATE TRIGGER update_leads_updated_at
    BEFORE UPDATE ON public.leads
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to automatically update geometry from coordinates
DROP TRIGGER IF EXISTS trigger_permits_update_geom ON public.permits;
CREATE TRIGGER trigger_permits_update_geom
  BEFORE INSERT OR UPDATE ON public.permits
  FOR EACH ROW
  EXECUTE FUNCTION update_permits_geom_from_coordinates();

-- Main trigger: create leads from permits
DROP TRIGGER IF EXISTS trg_lead_from_permit ON public.permits;
CREATE TRIGGER trg_lead_from_permit
  AFTER INSERT ON public.permits
  FOR EACH ROW
  EXECUTE FUNCTION public.create_lead_from_permit();

-- ================================================================================
-- UPSERT PERMIT FUNCTION
-- ================================================================================

-- Helper function to extract permit_id from JSONB
CREATE OR REPLACE FUNCTION public.extract_permit_id(p JSONB)
RETURNS TEXT
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT COALESCE(
    p->>'permit_id',
    p->>'permit_no',
    p->>'permit_number',
    p->>'source_record_id'
  );
$$;

CREATE OR REPLACE FUNCTION public.upsert_permit(p JSONB)
RETURNS UUID
LANGUAGE plpgsql
AS $$
DECLARE
  rid UUID;
  v_permit_id TEXT := public.extract_permit_id(p);
  v_record_hash TEXT;
BEGIN
  -- Generate record hash for change detection
  v_record_hash := md5(
    COALESCE(p->>'permit_number', '') || '|' ||
    COALESCE(p->>'work_description', '') || '|' ||
    COALESCE(p->>'applicant_name', '') || '|' ||
    COALESCE(p->>'valuation', '') || '|' ||
    COALESCE(p->>'status', '')
  );

  -- Upsert permit with comprehensive field mapping
  INSERT INTO public.permits (
    source, source_record_id, permit_id, permit_number, issued_date, application_date,
    expiration_date, finaled_at, permit_type, permit_class, work_description, work_class,
    address, city, county, zipcode, latitude, longitude, valuation, square_feet,
    applicant, applicant_name, contractor_name, owner, owner_name, status, 
    raw_data, record_hash, created_at, updated_at
  )
  VALUES (
    p->>'source', 
    p->>'source_record_id', 
    COALESCE(p->>'permit_no', p->>'permit_number'), 
    NULLIF(p->>'issued_date','')::TIMESTAMPTZ,
    NULLIF(p->>'application_date','')::TIMESTAMPTZ,
    NULLIF(p->>'expiration_date','')::TIMESTAMPTZ,
    NULLIF(p->>'finaled_at','')::TIMESTAMPTZ,
    p->>'permit_type', 
    p->>'permit_class',
    COALESCE(p->>'work_description', p->>'description'),
    p->>'work_class',
    p->>'address', 
    p->>'city', 
    p->>'county', 
    p->>'zipcode',
    NULLIF(p->>'latitude','')::DOUBLE PRECISION, 
    NULLIF(p->>'longitude','')::DOUBLE PRECISION,
    NULLIF(p->>'valuation','')::NUMERIC,
    NULLIF(p->>'square_feet','')::INTEGER,
    COALESCE(p->>'applicant', p->>'applicant_name'),
    p->>'applicant_name',
    p->>'contractor_name',
    COALESCE(p->>'owner', p->>'owner_name'), 
    p->>'owner_name',
    p->>'status', 
    p,
    v_record_hash,
    NOW(), 
    NOW()
  )
  ON CONFLICT (source, source_record_id) DO UPDATE SET
    permit_id = COALESCE(excluded.permit_id, public.permits.permit_id),
    permit_number = excluded.permit_number,
    issued_date = excluded.issued_date,
    application_date = excluded.application_date,
    expiration_date = excluded.expiration_date,
    finaled_at = excluded.finaled_at,
    permit_type = excluded.permit_type,
    permit_class = excluded.permit_class,
    work_description = excluded.work_description,
    work_class = excluded.work_class,
    address = excluded.address,
    city = excluded.city,
    county = excluded.county,
    zipcode = excluded.zipcode,
    latitude = excluded.latitude,
    longitude = excluded.longitude,
    valuation = excluded.valuation,
    square_feet = excluded.square_feet,
    applicant = excluded.applicant,
    applicant_name = excluded.applicant_name,
    contractor_name = excluded.contractor_name,
    owner = excluded.owner,
    owner_name = excluded.owner_name,
    status = excluded.status,
    raw_data = excluded.raw_data,
    record_hash = excluded.record_hash,
    updated_at = NOW()
  RETURNING id INTO rid;

  RETURN rid;
END;
$$;

-- ================================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ================================================================================

-- Enable RLS on tables
ALTER TABLE public.leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.permits ENABLE ROW LEVEL SECURITY;

-- Read-only policies for anonymous users on views/selects
DROP POLICY IF EXISTS "anon_read_leads" ON public.leads;
CREATE POLICY "anon_read_leads"
  ON public.leads FOR SELECT
  TO anon
  USING (true);

DROP POLICY IF EXISTS "anon_read_permits" ON public.permits;
CREATE POLICY "anon_read_permits"
  ON public.permits FOR SELECT
  TO anon
  USING (true);

-- Full access policies for authenticated users (own data only)
DROP POLICY IF EXISTS "authenticated_full_access_leads" ON public.leads;
CREATE POLICY "authenticated_full_access_leads"
  ON public.leads FOR ALL
  TO authenticated
  USING (auth.uid() = user_id)
  WITH CHECK (auth.uid() = user_id);

-- Service role gets full access to everything (bypass RLS)
DROP POLICY IF EXISTS "service_role_full_access_leads" ON public.leads;
CREATE POLICY "service_role_full_access_leads"
  ON public.leads FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

DROP POLICY IF EXISTS "service_role_full_access_permits" ON public.permits;
CREATE POLICY "service_role_full_access_permits"
  ON public.permits FOR ALL
  TO service_role
  USING (true)
  WITH CHECK (true);

-- ================================================================================
-- BACKFILL EXISTING PERMITS INTO LEADS
-- ================================================================================

-- Create leads for existing permits that don't have leads yet
INSERT INTO public.leads (
  permit_id, 
  external_permit_id,
  name, 
  service,
  trade, 
  address,
  city,
  state,
  zip,
  county, 
  status, 
  value, 
  lead_score, 
  created_at,
  source,
  metadata
)
SELECT DISTINCT
  p.id, -- UUID FK
  COALESCE(p.permit_id, p.permit_number, p.source_record_id, p.id::TEXT), -- Canonical external permit ID
  COALESCE(
    NULLIF(p.applicant, ''),
    NULLIF(p.applicant_name, ''),
    NULLIF(p.owner, ''),
    NULLIF(p.owner_name, ''),
    NULLIF(p.contractor_name, ''),
    'Unknown'
  ),
  CASE 
    WHEN p.work_description ILIKE '%hvac%' OR p.work_description ILIKE '%air%' OR 
         p.work_description ILIKE '%heating%' OR p.work_description ILIKE '%cooling%' THEN 'HVAC'
    WHEN p.work_description ILIKE '%electrical%' OR p.work_description ILIKE '%electric%' THEN 'Electrical'
    WHEN p.work_description ILIKE '%plumbing%' OR p.work_description ILIKE '%plumb%' THEN 'Plumbing'
    WHEN p.work_description ILIKE '%roof%' THEN 'Roofing'
    WHEN p.work_description ILIKE '%solar%' THEN 'Solar'
    WHEN p.permit_type ILIKE '%building%' OR p.permit_type ILIKE '%residential%' THEN 'General Construction'
    ELSE 'Home Services'
  END,
  COALESCE(NULLIF(p.permit_type, ''), NULLIF(p.permit_class, ''), NULLIF(p.work_class, '')),
  p.address,
  p.city,
  COALESCE(p.raw_data->>'state', 'TX'),
  p.zipcode,
  p.county,
  COALESCE(NULLIF(p.status, ''), 'New'),
  p.valuation,
  75,
  COALESCE(p.issued_date, p.application_date, p.created_at, NOW()),
  'permit_backfill',
  jsonb_build_object(
    'canonical_permit_id', COALESCE(p.permit_id, p.permit_number, p.source_record_id, p.id::TEXT),
    'permit_uuid', p.id,
    'source', p.source,
    'jurisdiction', p.source,
    'work_class', p.work_class,
    'permit_type', p.permit_type,
    'backfilled', true,
    'backfilled_at', NOW()
  )
FROM public.permits p
LEFT JOIN public.leads l ON l.permit_id = p.id
WHERE l.permit_id IS NULL
  AND p.id IS NOT NULL;

-- ================================================================================
-- TABLE COMMENTS FOR DOCUMENTATION
-- ================================================================================

COMMENT ON TABLE public.permits IS 'Permits ingestion table with canonical permit ID resolution and change tracking';
COMMENT ON TABLE public.leads IS 'Leads table with automatic creation from permits via triggers';

COMMENT ON COLUMN public.permits.permit_id IS 'Canonical permit identifier (derived from permit_number, permit_no, source_record_id, or id)';
COMMENT ON COLUMN public.permits.record_hash IS 'MD5 hash of key attributes for change detection';
COMMENT ON COLUMN public.permits.provenance IS 'Data lineage and transformation tracking';

COMMENT ON COLUMN public.leads.external_permit_id IS 'Canonical external permit identifier for tracking';
COMMENT ON COLUMN public.leads.permit_id IS 'Foreign key to permits.id (UUID)';
COMMENT ON COLUMN public.leads.lead_score IS 'Lead quality score (0-100)';
COMMENT ON COLUMN public.leads.metadata IS 'Enriched metadata including permit details and generation info';

COMMENT ON FUNCTION public.upsert_permit(JSONB) IS 'Idempotent upsert function with canonical permit ID resolution';
COMMENT ON FUNCTION public.create_lead_from_permit() IS 'Trigger function for automatic lead creation with ID canonicalization';

-- ================================================================================
-- BOOTSTRAP COMPLETE
-- ================================================================================

SELECT 
  'Supabase bootstrap completed successfully!' AS message,
  'Tables: permits, leads' AS tables_created,
  'Functions: upsert_permit(), create_lead_from_permit()' AS functions_created,
  'Triggers: permit → lead pipeline active' AS triggers_created,
  'RLS: anon read-only, service_role full access' AS security_policies,
  COUNT(*) AS existing_leads_found
FROM public.leads;