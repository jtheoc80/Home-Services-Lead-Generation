-- Harris County Permits Normalization Migration
-- Creates permits_raw_harris table and normalize_permits_harris() function
-- Adds missing fields to support unified permit schema

-- Create permits_raw_harris table for raw Harris County permit data
CREATE TABLE IF NOT EXISTS permits_raw_harris (
  id BIGSERIAL PRIMARY KEY,
  event_id TEXT UNIQUE NOT NULL,  -- Harris County's unique event/permit identifier
  permit_number TEXT,
  address TEXT,
  permit_type TEXT,
  work_description TEXT,
  permit_status TEXT,
  issue_date TIMESTAMPTZ,
  application_date TIMESTAMPTZ,
  expiration_date TIMESTAMPTZ,
  applicant_name TEXT,
  property_owner TEXT,
  contractor_name TEXT,
  valuation NUMERIC,
  square_footage NUMERIC,
  latitude DOUBLE PRECISION,
  longitude DOUBLE PRECISION,
  parcel_id TEXT,
  district TEXT,
  sub_type TEXT,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  raw_data JSONB  -- Store full original record
);

-- Add missing fields to public.permits/leads table if they don't exist
ALTER TABLE leads ADD COLUMN IF NOT EXISTS source_ref TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS county TEXT;
ALTER TABLE leads ADD COLUMN IF NOT EXISTS permit_type TEXT;

-- Add index on source_ref for upsert operations
CREATE INDEX IF NOT EXISTS idx_leads_source_ref ON leads(source_ref);

-- Add indexes for permits_raw_harris
CREATE INDEX IF NOT EXISTS idx_permits_raw_harris_event_id ON permits_raw_harris(event_id);
CREATE INDEX IF NOT EXISTS idx_permits_raw_harris_issue_date ON permits_raw_harris(issue_date);
CREATE INDEX IF NOT EXISTS idx_permits_raw_harris_created_at ON permits_raw_harris(created_at);

-- Create normalize_permits_harris() function
CREATE OR REPLACE FUNCTION normalize_permits_harris() 
RETURNS TABLE(processed_count INTEGER, new_count INTEGER, updated_count INTEGER) 
LANGUAGE plpgsql AS $$
DECLARE
    rec RECORD;
    processed_count INTEGER := 0;
    new_count INTEGER := 0;
    updated_count INTEGER := 0;
    normalized_address TEXT;
    normalized_permit_type TEXT;
    normalized_category TEXT;
    trade_tags_array TEXT[];
    existing_source_ref TEXT;
BEGIN
    -- Process records from permits_raw_harris, getting the latest version of each event_id
    FOR rec IN 
        SELECT DISTINCT ON (event_id) *
        FROM permits_raw_harris
        ORDER BY event_id, created_at DESC  -- Get latest version of each event_id
    LOOP
        -- Normalize address
        normalized_address := COALESCE(
            TRIM(REGEXP_REPLACE(rec.address, '\s+', ' ', 'g')),
            'Address Not Available'
        );
        
        -- Normalize permit type
        normalized_permit_type := COALESCE(rec.permit_type, rec.sub_type, 'General');
        
        -- Determine category based on permit type and description
        normalized_category := CASE
            WHEN LOWER(COALESCE(rec.permit_type, '')) LIKE '%residential%' 
                OR LOWER(COALESCE(rec.work_description, '')) LIKE ANY(ARRAY['%single family%', '%duplex%', '%residential%', '%house%', '%home%'])
            THEN 'residential'
            WHEN LOWER(COALESCE(rec.permit_type, '')) LIKE '%commercial%'
                OR LOWER(COALESCE(rec.work_description, '')) LIKE ANY(ARRAY['%commercial%', '%office%', '%retail%', '%industrial%'])
            THEN 'commercial'
            ELSE 'other'
        END;
        
        -- Extract trade tags based on work description
        trade_tags_array := ARRAY[]::TEXT[];
        IF LOWER(COALESCE(rec.work_description, '')) LIKE ANY(ARRAY['%plumb%', '%water%', '%sewer%']) THEN
            trade_tags_array := array_append(trade_tags_array, 'plumbing');
        END IF;
        IF LOWER(COALESCE(rec.work_description, '')) LIKE ANY(ARRAY['%electric%', '%electrical%', '%wiring%']) THEN
            trade_tags_array := array_append(trade_tags_array, 'electrical');
        END IF;
        IF LOWER(COALESCE(rec.work_description, '')) LIKE ANY(ARRAY['%hvac%', '%heating%', '%cooling%', '%air%']) THEN
            trade_tags_array := array_append(trade_tags_array, 'hvac');
        END IF;
        IF LOWER(COALESCE(rec.work_description, '')) LIKE ANY(ARRAY['%roof%', '%roofing%']) THEN
            trade_tags_array := array_append(trade_tags_array, 'roofing');
        END IF;
        IF LOWER(COALESCE(rec.work_description, '')) LIKE ANY(ARRAY['%kitchen%', '%bathroom%', '%remodel%', '%renovation%']) THEN
            trade_tags_array := array_append(trade_tags_array, 'general_contractor');
        END IF;
        
        -- Upsert into leads table
        INSERT INTO leads (
            jurisdiction,
            permit_id,
            address,
            description,
            work_class,
            category,
            status,
            issue_date,
            applicant,
            owner,
            value,
            is_residential,
            latitude,
            longitude,
            trade_tags,
            source_ref,
            county,
            permit_type,
            state,
            created_at,
            updated_at
        ) VALUES (
            'Harris County',
            rec.permit_number,
            normalized_address,
            rec.work_description,
            normalized_permit_type,
            normalized_category,
            rec.permit_status,
            rec.issue_date,
            COALESCE(rec.applicant_name, rec.contractor_name),
            rec.property_owner,
            rec.valuation,
            (normalized_category = 'residential'),
            rec.latitude,
            rec.longitude,
            trade_tags_array,
            rec.event_id,  -- Use event_id as source_ref
            'Harris',
            normalized_permit_type,
            'TX',
            now(),
            now()
        )
        ON CONFLICT (source_ref) 
        DO UPDATE SET
            permit_id = EXCLUDED.permit_id,
            address = EXCLUDED.address,
            description = EXCLUDED.description,
            work_class = EXCLUDED.work_class,
            category = EXCLUDED.category,
            status = EXCLUDED.status,
            issue_date = EXCLUDED.issue_date,
            applicant = EXCLUDED.applicant,
            owner = EXCLUDED.owner,
            value = EXCLUDED.value,
            is_residential = EXCLUDED.is_residential,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            trade_tags = EXCLUDED.trade_tags,
            county = EXCLUDED.county,
            permit_type = EXCLUDED.permit_type,
            updated_at = now();
        
        -- Check if this source_ref already exists
        SELECT source_ref INTO existing_source_ref FROM leads WHERE source_ref = rec.event_id;
        
        -- Upsert into leads table
        INSERT INTO leads (
            jurisdiction,
            permit_id,
            address,
            description,
            work_class,
            category,
            status,
            issue_date,
            applicant,
            owner,
            value,
            is_residential,
            latitude,
            longitude,
            trade_tags,
            source_ref,
            county,
            permit_type,
            state,
            created_at,
            updated_at
        ) VALUES (
            'Harris County',
            rec.permit_number,
            normalized_address,
            rec.work_description,
            normalized_permit_type,
            normalized_category,
            rec.permit_status,
            rec.issue_date,
            COALESCE(rec.applicant_name, rec.contractor_name),
            rec.property_owner,
            rec.valuation,
            (normalized_category = 'residential'),
            rec.latitude,
            rec.longitude,
            trade_tags_array,
            rec.event_id,  -- Use event_id as source_ref
            'Harris',
            normalized_permit_type,
            'TX',
            now(),
            now()
        )
        ON CONFLICT (source_ref) 
        DO UPDATE SET
            permit_id = EXCLUDED.permit_id,
            address = EXCLUDED.address,
            description = EXCLUDED.description,
            work_class = EXCLUDED.work_class,
            category = EXCLUDED.category,
            status = EXCLUDED.status,
            issue_date = EXCLUDED.issue_date,
            applicant = EXCLUDED.applicant,
            owner = EXCLUDED.owner,
            value = EXCLUDED.value,
            is_residential = EXCLUDED.is_residential,
            latitude = EXCLUDED.latitude,
            longitude = EXCLUDED.longitude,
            trade_tags = EXCLUDED.trade_tags,
            county = EXCLUDED.county,
            permit_type = EXCLUDED.permit_type,
            updated_at = now();
        
        -- Track insert vs update
        IF existing_source_ref IS NOT NULL THEN
            updated_count := updated_count + 1;
        ELSE
            new_count := new_count + 1;
        END IF;
        
        processed_count := processed_count + 1;
        
        -- Log progress every 100 records
        IF processed_count % 100 = 0 THEN
            RAISE NOTICE 'Processed % records (% new, % updated)', processed_count, new_count, updated_count;
        END IF;
    END LOOP;
    
    -- Return summary
    RETURN QUERY SELECT processed_count, new_count, updated_count;
END;
$$;

-- Add comments for documentation
COMMENT ON TABLE permits_raw_harris IS 'Raw Harris County permit data before normalization';
COMMENT ON COLUMN permits_raw_harris.event_id IS 'Unique Harris County event/permit identifier for deduplication';
COMMENT ON COLUMN permits_raw_harris.raw_data IS 'Complete original record in JSONB format';

COMMENT ON FUNCTION normalize_permits_harris() IS 'Normalizes new Harris County permits from raw table to unified leads schema';

COMMENT ON COLUMN leads.source_ref IS 'Reference to original source record (event_id for Harris County)';
COMMENT ON COLUMN leads.county IS 'County name (e.g., Harris, Fort Bend)';
COMMENT ON COLUMN leads.permit_type IS 'Specific permit type from source system';